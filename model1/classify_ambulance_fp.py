import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw
from torch.utils.data import DataLoader

from model_v4 import TrafficDetectorV4
from traffic_dataset_v4 import TrafficDatasetV4


# ==========================================================
# CONFIG
# ==========================================================

NUM_CLASSES = 15
IMAGE_SIZE = 448

CONFIDENCE_THRESHOLD = 0.97
NMS_IOU_THRESHOLD = 0.40
MATCH_IOU_THRESHOLD = 0.50

# Diagnostic-only heuristics. These do NOT change official evaluation.
RELATED_IOU_THRESHOLD = 0.10
DUPLICATE_PRED_IOU_THRESHOLD = 0.25
PRED_OVERLAP_FRACTION_THRESHOLD = 0.25

BATCH_SIZE = 8
NUM_WORKERS = 4
MAX_SAVED_PER_TYPE = 100

MODEL_DIR = Path(__file__).resolve().parent
PROJECT_DIR = MODEL_DIR.parent

MODEL_PATH = MODEL_DIR / "traffic_detector_v4_best.pth"

AMB_IMAGE_DIR = PROJECT_DIR / "ambulance_v4" / "valid" / "images"
AMB_LABEL_DIR = PROJECT_DIR / "ambulance_v4" / "valid" / "labels"

OUTPUT_DIR = PROJECT_DIR / "ambulance_fp_classification_v4"
TYPE_A_DIR = OUTPUT_DIR / "A_background"
TYPE_B_DIR = OUTPUT_DIR / "B_localization"
TYPE_C_DIR = OUTPUT_DIR / "C_duplicate"
TP_DIR = OUTPUT_DIR / "TP_reference"
FN_DIR = OUTPUT_DIR / "FN_reference"


# ==========================================================
# DATA
# ==========================================================

def detection_collate(batch):
    images = torch.stack([sample[0] for sample in batch], dim=0)
    boxes = [sample[1] for sample in batch]
    categories = [sample[2] for sample in batch]
    supervision = [sample[3] for sample in batch]
    return images, boxes, categories, supervision


# ==========================================================
# GEOMETRY
# ==========================================================

def intersection_area(a, b):
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def box_area(box):
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def calculate_iou(a, b):
    inter = intersection_area(a, b)
    union = box_area(a) + box_area(b) - inter
    return inter / union if union > 0.0 else 0.0


def prediction_overlap_fraction(pred_box, gt_box):
    area = box_area(pred_box)
    if area <= 0.0:
        return 0.0
    return intersection_area(pred_box, gt_box) / area


def center_inside(pred_box, gt_box):
    cx = (pred_box[0] + pred_box[2]) / 2.0
    cy = (pred_box[1] + pred_box[3]) / 2.0
    return (
        gt_box[0] <= cx <= gt_box[2]
        and gt_box[1] <= cy <= gt_box[3]
    )


# ==========================================================
# NMS
# ==========================================================

def class_aware_nms(detections):
    detections = sorted(
        detections,
        key=lambda d: d["confidence"],
        reverse=True
    )

    kept = []

    while detections:
        best = detections.pop(0)
        kept.append(best)

        remaining = []

        for detection in detections:
            if detection["class_id"] != best["class_id"]:
                remaining.append(detection)
                continue

            if (
                calculate_iou(best["box"], detection["box"])
                < NMS_IOU_THRESHOLD
            ):
                remaining.append(detection)

        detections = remaining

    return kept


# ==========================================================
# DECODER
# ==========================================================

def decode_head(prediction):
    objectness = torch.sigmoid(prediction[0])

    class_probabilities = torch.softmax(
        prediction[5:],
        dim=0
    )

    best_class_probability, best_class_id = torch.max(
        class_probabilities,
        dim=0
    )

    confidence = objectness * best_class_probability

    rows, columns = torch.where(
        confidence >= CONFIDENCE_THRESHOLD
    )

    if rows.numel() == 0:
        return []

    tx = torch.sigmoid(prediction[1, rows, columns])
    ty = torch.sigmoid(prediction[2, rows, columns])
    width = torch.sigmoid(prediction[3, rows, columns])
    height = torch.sigmoid(prediction[4, rows, columns])

    grid_h, grid_w = prediction.shape[-2:]

    center_x = (columns.float() + tx) / grid_w
    center_y = (rows.float() + ty) / grid_h

    x1 = torch.clamp(center_x - width / 2.0, 0.0, 1.0)
    y1 = torch.clamp(center_y - height / 2.0, 0.0, 1.0)
    x2 = torch.clamp(center_x + width / 2.0, 0.0, 1.0)
    y2 = torch.clamp(center_y + height / 2.0, 0.0, 1.0)

    detections = []

    for index in range(rows.numel()):
        box = (
            float(x1[index]),
            float(y1[index]),
            float(x2[index]),
            float(y2[index])
        )

        if box[2] <= box[0] or box[3] <= box[1]:
            continue

        detections.append({
            "confidence": float(
                confidence[rows[index], columns[index]]
            ),
            "class_id": int(
                best_class_id[rows[index], columns[index]]
            ),
            "box": box
        })

    return detections


def decode_ambulance(outputs, batch_index):
    small = outputs["small"][batch_index].detach().float().cpu()
    large = outputs["large"][batch_index].detach().float().cpu()

    detections = decode_head(small) + decode_head(large)
    detections = class_aware_nms(detections)

    return [
        detection
        for detection in detections
        if detection["class_id"] == 14
    ]


# ==========================================================
# GROUND TRUTH
# ==========================================================

def build_ambulance_gt(boxes, categories):
    ground_truth = []

    for box, category in zip(boxes, categories):
        if int(category.item()) != 14:
            continue

        x, y, width, height = [
            float(value)
            for value in box.tolist()
        ]

        gt_box = (
            max(0.0, min(1.0, x)),
            max(0.0, min(1.0, y)),
            max(0.0, min(1.0, x + width)),
            max(0.0, min(1.0, y + height))
        )

        if gt_box[2] > gt_box[0] and gt_box[3] > gt_box[1]:
            ground_truth.append({
                "class_id": 14,
                "box": gt_box
            })

    return ground_truth


# ==========================================================
# OFFICIAL MATCHING
# ==========================================================

def match_detections(predictions, ground_truth):
    predictions = sorted(
        predictions,
        key=lambda d: d["confidence"],
        reverse=True
    )

    matched_gt = set()

    true_positives = []
    false_positives = []

    for prediction in predictions:
        best_iou = 0.0
        best_gt_index = None

        for gt_index, gt in enumerate(ground_truth):
            if gt_index in matched_gt:
                continue

            overlap = calculate_iou(
                prediction["box"],
                gt["box"]
            )

            if overlap > best_iou:
                best_iou = overlap
                best_gt_index = gt_index

        item = dict(prediction)

        if (
            best_gt_index is not None
            and best_iou >= MATCH_IOU_THRESHOLD
        ):
            matched_gt.add(best_gt_index)

            item["matched_gt_index"] = best_gt_index
            item["matched_iou"] = best_iou

            true_positives.append(item)

        else:
            item["official_best_iou"] = best_iou
            false_positives.append(item)

    false_negatives = [
        {
            "gt_index": gt_index,
            "box": gt["box"]
        }
        for gt_index, gt in enumerate(ground_truth)
        if gt_index not in matched_gt
    ]

    return (
        true_positives,
        false_positives,
        false_negatives
    )


# ==========================================================
# DIAGNOSTIC FP CLASSIFICATION
# ==========================================================

def classify_false_positive(
    false_positive,
    true_positives,
    ground_truth
):
    pred_box = false_positive["box"]

    best_gt_iou = 0.0
    best_pred_overlap = 0.0
    any_center_inside = False
    best_gt_index = None

    for gt_index, gt in enumerate(ground_truth):
        gt_box = gt["box"]

        gt_iou = calculate_iou(
            pred_box,
            gt_box
        )

        pred_overlap = prediction_overlap_fraction(
            pred_box,
            gt_box
        )

        if gt_iou > best_gt_iou:
            best_gt_iou = gt_iou
            best_gt_index = gt_index

        best_pred_overlap = max(
            best_pred_overlap,
            pred_overlap
        )

        if center_inside(pred_box, gt_box):
            any_center_inside = True

    best_tp_iou = 0.0

    for tp in true_positives:
        best_tp_iou = max(
            best_tp_iou,
            calculate_iou(
                pred_box,
                tp["box"]
            )
        )

    matched_gt_indices = {
        tp["matched_gt_index"]
        for tp in true_positives
    }

    # Type C:
    # Extra prediction around an ambulance that has already
    # been correctly matched by another prediction.
    if (
        best_tp_iou >= DUPLICATE_PRED_IOU_THRESHOLD
        or (
            best_gt_index in matched_gt_indices
            and (
                best_gt_iou >= RELATED_IOU_THRESHOLD
                or best_pred_overlap
                >= PRED_OVERLAP_FRACTION_THRESHOLD
                or any_center_inside
            )
        )
    ):
        return "C_duplicate", {
            "best_gt_iou": best_gt_iou,
            "best_tp_iou": best_tp_iou,
            "pred_overlap_fraction": best_pred_overlap,
            "center_inside_gt": any_center_inside
        }

    # Type B:
    # Clearly related to an ambulance GT, but localization
    # is insufficient for the official IoU >= 0.50 match.
    if (
        best_gt_iou >= RELATED_IOU_THRESHOLD
        or best_pred_overlap
        >= PRED_OVERLAP_FRACTION_THRESHOLD
        or any_center_inside
    ):
        return "B_localization", {
            "best_gt_iou": best_gt_iou,
            "best_tp_iou": best_tp_iou,
            "pred_overlap_fraction": best_pred_overlap,
            "center_inside_gt": any_center_inside
        }

    # Type A:
    # No meaningful geometric relation to an ambulance GT.
    return "A_background", {
        "best_gt_iou": best_gt_iou,
        "best_tp_iou": best_tp_iou,
        "pred_overlap_fraction": best_pred_overlap,
        "center_inside_gt": any_center_inside
    }


# ==========================================================
# VISUALIZATION
# ==========================================================

def tensor_to_image(image_tensor):
    array = (
        image_tensor
        .detach()
        .cpu()
        .permute(1, 2, 0)
        .numpy()
    )

    array = np.clip(
        array * 255.0,
        0,
        255
    ).astype(np.uint8)

    return Image.fromarray(array)


def to_pixels(box):
    return tuple(
        int(value * IMAGE_SIZE)
        for value in box
    )


def draw_example(
    image_tensor,
    ground_truth,
    true_positives,
    false_positive,
    fp_type
):
    image = tensor_to_image(image_tensor)
    draw = ImageDraw.Draw(image)

    for gt in ground_truth:
        draw.rectangle(
            to_pixels(gt["box"]),
            outline="orange",
            width=3
        )

    for tp in true_positives:
        draw.rectangle(
            to_pixels(tp["box"]),
            outline="green",
            width=3
        )

    fp_box = to_pixels(false_positive["box"])

    draw.rectangle(
        fp_box,
        outline="red",
        width=4
    )

    text = (
        f"{fp_type} "
        f"{false_positive['confidence']:.3f}"
    )

    draw.text(
        (
            fp_box[0],
            max(0, fp_box[1] - 14)
        ),
        text,
        fill="red"
    )

    return image


# ==========================================================
# MODEL
# ==========================================================

def load_model(device):
    model = TrafficDetectorV4(
        num_classes=NUM_CLASSES
    ).to(device)

    loaded = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=True
    )

    if (
        isinstance(loaded, dict)
        and "model_state_dict" in loaded
    ):
        state_dict = loaded["model_state_dict"]

    elif (
        isinstance(loaded, dict)
        and "model" in loaded
        and isinstance(loaded["model"], dict)
    ):
        state_dict = loaded["model"]

    else:
        state_dict = loaded

    model.load_state_dict(state_dict)
    model.eval()

    return model


# ==========================================================
# MAIN
# ==========================================================

def main():
    for required in [
        MODEL_PATH,
        AMB_IMAGE_DIR,
        AMB_LABEL_DIR
    ]:
        if not required.exists():
            raise FileNotFoundError(
                f"Missing: {required}"
            )

    for folder in [
        TYPE_A_DIR,
        TYPE_B_DIR,
        TYPE_C_DIR,
        TP_DIR,
        FN_DIR
    ]:
        folder.mkdir(
            parents=True,
            exist_ok=True
        )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("=" * 90)
    print("V4 AMBULANCE FALSE-POSITIVE CLASSIFIER")
    print("=" * 90)
    print("Device          :", device)
    print("Confidence      :", CONFIDENCE_THRESHOLD)
    print("Official IoU    :", MATCH_IOU_THRESHOLD)
    print("Output          :", OUTPUT_DIR)
    print()
    print("IMPORTANT: A/B/C are diagnostic heuristics.")
    print("Official evaluation remains IoU >= 0.50.")
    print("=" * 90)

    dataset = TrafficDatasetV4(
        AMB_IMAGE_DIR,
        AMB_LABEL_DIR,
        image_size=IMAGE_SIZE,
        augment=False
    )

    loader_args = {
        "batch_size": BATCH_SIZE,
        "shuffle": False,
        "num_workers": NUM_WORKERS,
        "pin_memory": device.type == "cuda",
        "collate_fn": detection_collate
    }

    if NUM_WORKERS > 0:
        loader_args["persistent_workers"] = True
        loader_args["prefetch_factor"] = 2

    loader = DataLoader(
        dataset,
        **loader_args
    )

    model = load_model(device)

    totals = {
        "tp": 0,
        "fp": 0,
        "fn": 0,
        "A_background": 0,
        "B_localization": 0,
        "C_duplicate": 0
    }

    saved = {
        "A_background": 0,
        "B_localization": 0,
        "C_duplicate": 0
    }

    fp_records = []

    processed = 0

    with torch.inference_mode():

        for (
            images,
            boxes_batch,
            categories_batch,
            _
        ) in loader:

            images_device = images.to(
                device,
                non_blocking=True
            )

            with torch.amp.autocast(
                device_type=device.type,
                dtype=torch.float16,
                enabled=device.type == "cuda"
            ):
                outputs = model(images_device)

            for batch_index in range(
                images.shape[0]
            ):
                predictions = decode_ambulance(
                    outputs,
                    batch_index
                )

                ground_truth = build_ambulance_gt(
                    boxes_batch[batch_index],
                    categories_batch[batch_index]
                )

                (
                    true_positives,
                    false_positives,
                    false_negatives
                ) = match_detections(
                    predictions,
                    ground_truth
                )

                totals["tp"] += len(true_positives)
                totals["fp"] += len(false_positives)
                totals["fn"] += len(false_negatives)

                image_name = (
                    dataset
                    .image_files[processed]
                    .stem
                )

                for fp_index, false_positive in enumerate(
                    false_positives
                ):
                    fp_type, details = (
                        classify_false_positive(
                            false_positive,
                            true_positives,
                            ground_truth
                        )
                    )

                    totals[fp_type] += 1

                    fp_records.append({
                        "image": dataset.image_files[
                            processed
                        ].name,
                        "confidence":
                            false_positive["confidence"],
                        "type": fp_type,
                        **details
                    })

                    if (
                        saved[fp_type]
                        < MAX_SAVED_PER_TYPE
                    ):
                        image = draw_example(
                            images[batch_index],
                            ground_truth,
                            true_positives,
                            false_positive,
                            fp_type
                        )

                        destination = {
                            "A_background": TYPE_A_DIR,
                            "B_localization": TYPE_B_DIR,
                            "C_duplicate": TYPE_C_DIR
                        }[fp_type]

                        image.save(
                            destination
                            / (
                                f"{image_name}"
                                f"_fp{fp_index:02d}.png"
                            )
                        )

                        saved[fp_type] += 1

                processed += 1

                if processed % 100 == 0:
                    print(
                        f"Processed "
                        f"{processed}/"
                        f"{len(dataset)}"
                    )

    total_fp = totals["fp"]

    percentages = {}

    for fp_type in [
        "A_background",
        "B_localization",
        "C_duplicate"
    ]:
        percentages[fp_type] = (
            100.0
            * totals[fp_type]
            / total_fp
            if total_fp > 0
            else 0.0
        )

    summary = {
        "confidence_threshold":
            CONFIDENCE_THRESHOLD,
        "official_match_iou":
            MATCH_IOU_THRESHOLD,
        "diagnostic_thresholds": {
            "related_iou":
                RELATED_IOU_THRESHOLD,
            "duplicate_prediction_iou":
                DUPLICATE_PRED_IOU_THRESHOLD,
            "prediction_overlap_fraction":
                PRED_OVERLAP_FRACTION_THRESHOLD
        },
        "totals": totals,
        "percentages_of_fp": percentages,
        "saved_examples": saved
    }

    with open(
        OUTPUT_DIR / "summary.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            summary,
            file,
            indent=2
        )

    with open(
        OUTPUT_DIR / "fp_details.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            fp_records,
            file,
            indent=2
        )

    print("\n" + "=" * 90)
    print("RESULT")
    print("=" * 90)

    print(
        f"Official TP : {totals['tp']}"
    )
    print(
        f"Official FP : {totals['fp']}"
    )
    print(
        f"Official FN : {totals['fn']}"
    )

    print()

    print(
        "A - Background/unrelated : "
        f"{totals['A_background']} "
        f"({percentages['A_background']:.1f}%)"
    )

    print(
        "B - Localization/partial : "
        f"{totals['B_localization']} "
        f"({percentages['B_localization']:.1f}%)"
    )

    print(
        "C - Duplicate ambulance  : "
        f"{totals['C_duplicate']} "
        f"({percentages['C_duplicate']:.1f}%)"
    )

    print()
    print("Saved to:")
    print(OUTPUT_DIR)
    print("=" * 90)


if __name__ == "__main__":
    main()
