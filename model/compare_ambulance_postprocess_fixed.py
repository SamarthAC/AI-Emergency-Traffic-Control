"""
compare_ambulance_postprocess_fixed.py

Final fair ambulance comparison for:
    - traffic_detector_v4_best.pth
    - traffic_detector_v4_1_best.pth

This version matches the REAL evaluate_v4.py interface:
    decode_head(prediction, minimum_confidence)

It deliberately decodes BOTH heads BEFORE NMS so each experimental NMS
threshold is applied exactly once.

Official GT matching remains IoU >= 0.50.
Directional containment:
    intersection(kept, candidate) / area(candidate)
"""

from pathlib import Path
import torch

import evaluate_v4 as ev


# ==========================================================
# CONFIG
# ==========================================================

MODEL_DIR = Path(__file__).resolve().parent

MODELS = {
    "V4": MODEL_DIR / "traffic_detector_v4_best.pth",
    "V4.1": MODEL_DIR / "traffic_detector_v4_1_best.pth",
}

AMBULANCE_CLASS_ID = 14
MATCH_IOU = 0.50

# Decode permissively once, then sweep cached detections.
CACHE_CONFIDENCE = 0.90

CONF_THRESHOLDS = [0.94, 0.95, 0.96, 0.97, 0.98]
NMS_THRESHOLDS = [0.40, 0.35, 0.30, 0.25, 0.20]
CONTAINMENT_THRESHOLDS = [None, 0.70, 0.80, 0.90]


# ==========================================================
# GEOMETRY
# ==========================================================

def area(box):
    x1, y1, x2, y2 = box
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def intersection(a, b):
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])

    return (
        max(0.0, x2 - x1)
        * max(0.0, y2 - y1)
    )


def box_iou(a, b):
    inter = intersection(a, b)
    union = area(a) + area(b) - inter

    if union <= 0.0:
        return 0.0

    return inter / union


def candidate_containment(kept_box, candidate_box):
    """
    Directional containment.

    candidate_box is the LOWER-CONFIDENCE box currently being considered.
    Only suppress it when most of THAT candidate lies inside the already-kept
    higher-confidence box.
    """
    candidate_area = area(candidate_box)

    if candidate_area <= 0.0:
        return 0.0

    return (
        intersection(kept_box, candidate_box)
        / candidate_area
    )


# ==========================================================
# POST-PROCESSING
# ==========================================================

def postprocess(
    detections,
    confidence_threshold,
    nms_threshold,
    containment_threshold,
):
    detections = [
        d
        for d in detections
        if (
            d["class_id"] == AMBULANCE_CLASS_ID
            and d["confidence"] >= confidence_threshold
        )
    ]

    detections.sort(
        key=lambda d: d["confidence"],
        reverse=True,
    )

    kept = []

    while detections:
        best = detections.pop(0)
        kept.append(best)

        remaining = []

        for candidate in detections:

            # Same-class IoU NMS.
            if (
                box_iou(
                    best["box"],
                    candidate["box"],
                )
                >= nms_threshold
            ):
                continue

            # Directional containment suppression.
            if containment_threshold is not None:
                contained = candidate_containment(
                    best["box"],
                    candidate["box"],
                )

                if contained >= containment_threshold:
                    continue

            remaining.append(candidate)

        detections = remaining

    return kept


# ==========================================================
# OFFICIAL ONE-TO-ONE MATCHING
# ==========================================================

def match_predictions(predictions, ground_truth):
    predictions = sorted(
        predictions,
        key=lambda d: d["confidence"],
        reverse=True,
    )

    matched_gt = set()

    tp = 0
    fp = 0
    iou_sum = 0.0

    for prediction in predictions:

        best_index = -1
        best_iou = 0.0

        for index, gt in enumerate(ground_truth):

            if index in matched_gt:
                continue

            current_iou = box_iou(
                prediction["box"],
                gt,
            )

            if current_iou > best_iou:
                best_iou = current_iou
                best_index = index

        if (
            best_index >= 0
            and best_iou >= MATCH_IOU
        ):
            matched_gt.add(best_index)
            tp += 1
            iou_sum += best_iou
        else:
            fp += 1

    fn = len(ground_truth) - len(matched_gt)

    return tp, fp, fn, iou_sum


# ==========================================================
# MODEL LOADING
# ==========================================================

def extract_state_dict(checkpoint):
    if (
        isinstance(checkpoint, dict)
        and "model_state_dict" in checkpoint
    ):
        return checkpoint["model_state_dict"]

    if (
        isinstance(checkpoint, dict)
        and "model" in checkpoint
        and isinstance(checkpoint["model"], dict)
    ):
        return checkpoint["model"]

    return checkpoint


def load_model(model_path, device):
    model = ev.TrafficDetectorV4(
        num_classes=ev.NUM_CLASSES
    ).to(device)

    checkpoint = torch.load(
        model_path,
        map_location=device,
        weights_only=True,
    )

    model.load_state_dict(
        extract_state_dict(checkpoint)
    )

    model.eval()

    return model


# ==========================================================
# AMBULANCE DATASET
# ==========================================================

def get_ambulance_dataset():
    """
    Uses the exact validation paths and TrafficDatasetV4 class from
    evaluate_v4.py, avoiding assumptions about an evaluator loader helper.
    """
    return ev.TrafficDatasetV4(
        ev.AMBULANCE_IMAGE_DIR,
        ev.AMBULANCE_LABEL_DIR,
        image_size=ev.IMAGE_SIZE,
        augment=False,
    )


def collate_fn(batch):
    images = torch.stack(
        [sample[0] for sample in batch],
        dim=0,
    )

    boxes = [
        sample[1]
        for sample in batch
    ]

    categories = [
        sample[2]
        for sample in batch
    ]

    return images, boxes, categories


def make_loader(dataset, device):
    kwargs = {
        "batch_size": 8,
        "shuffle": False,
        "num_workers": 4,
        "pin_memory": device.type == "cuda",
        "collate_fn": collate_fn,
    }

    if kwargs["num_workers"] > 0:
        kwargs["persistent_workers"] = True
        kwargs["prefetch_factor"] = 2

    return torch.utils.data.DataLoader(
        dataset,
        **kwargs,
    )


# ==========================================================
# GT
# ==========================================================

def build_ambulance_gt(boxes, categories):
    ground_truth = []

    for box, category in zip(
        boxes,
        categories,
    ):
        class_id = int(category.item())

        if class_id != AMBULANCE_CLASS_ID:
            continue

        x, y, width, height = [
            float(value)
            for value in box.tolist()
        ]

        x1 = max(0.0, min(1.0, x))
        y1 = max(0.0, min(1.0, y))
        x2 = max(
            0.0,
            min(
                1.0,
                x + width,
            ),
        )
        y2 = max(
            0.0,
            min(
                1.0,
                y + height,
            ),
        )

        if x2 > x1 and y2 > y1:
            ground_truth.append(
                (x1, y1, x2, y2)
            )

    return ground_truth


# ==========================================================
# RAW DECODING — CRITICAL FIX
# ==========================================================

def decode_raw_before_nms(outputs, batch_index):
    """
    IMPORTANT:
    evaluate_v4.decode_multiscale_outputs() cannot be used for this sweep,
    because it performs fixed class-aware NMS internally.

    Instead:
      1. take the small head
      2. call the real evaluate_v4.decode_head()
      3. take the large head
      4. call the real evaluate_v4.decode_head()
      5. concatenate
      6. NO NMS HERE

    Experimental NMS is applied later exactly once.
    """

    small_prediction = (
        outputs["small"][batch_index]
        .detach()
        .float()
        .cpu()
    )

    large_prediction = (
        outputs["large"][batch_index]
        .detach()
        .float()
        .cpu()
    )

    detections = []

    detections.extend(
        ev.decode_head(
            small_prediction,
            CACHE_CONFIDENCE,
        )
    )

    detections.extend(
        ev.decode_head(
            large_prediction,
            CACHE_CONFIDENCE,
        )
    )

    return detections


# ==========================================================
# CACHE MODEL OUTPUTS
# ==========================================================

@torch.inference_mode()
def cache_model_predictions(
    model,
    dataset,
    loader,
    device,
):
    cached = []

    processed = 0

    for images, boxes_batch, categories_batch in loader:

        images = images.to(
            device,
            non_blocking=True,
        )

        outputs = model(images)

        for batch_index in range(
            images.shape[0]
        ):
            raw = decode_raw_before_nms(
                outputs,
                batch_index,
            )

            # Keep only class 14 in the cache.
            raw = [
                {
                    "confidence":
                        float(d["confidence"]),
                    "class_id":
                        int(d["class_id"]),
                    "box":
                        tuple(
                            float(v)
                            for v in d["box"]
                        ),
                }
                for d in raw
                if int(d["class_id"])
                == AMBULANCE_CLASS_ID
            ]

            gt = build_ambulance_gt(
                boxes_batch[batch_index],
                categories_batch[batch_index],
            )

            cached.append(
                {
                    "predictions": raw,
                    "ground_truth": gt,
                }
            )

            processed += 1

            if processed % 100 == 0:
                print(
                    f"Cached {processed}/"
                    f"{len(dataset)}"
                )

    return cached


# ==========================================================
# ONE CONFIG
# ==========================================================

def evaluate_configuration(
    cached,
    confidence_threshold,
    nms_threshold,
    containment_threshold,
):
    tp = 0
    fp = 0
    fn = 0

    prediction_count = 0
    ground_truth_count = 0

    absolute_count_error = 0
    matched_iou_sum = 0.0

    for image in cached:

        predictions = postprocess(
            image["predictions"],
            confidence_threshold,
            nms_threshold,
            containment_threshold,
        )

        gt = image["ground_truth"]

        image_tp, image_fp, image_fn, image_iou_sum = (
            match_predictions(
                predictions,
                gt,
            )
        )

        tp += image_tp
        fp += image_fp
        fn += image_fn

        prediction_count += len(predictions)
        ground_truth_count += len(gt)

        absolute_count_error += abs(
            len(predictions)
            - len(gt)
        )

        matched_iou_sum += image_iou_sum

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0.0
    )

    f1 = (
        2.0
        * precision
        * recall
        / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    count_mae = (
        absolute_count_error
        / len(cached)
    )

    mean_tp_iou = (
        matched_iou_sum / tp
        if tp > 0
        else 0.0
    )

    return {
        "confidence":
            confidence_threshold,
        "nms":
            nms_threshold,
        "containment":
            containment_threshold,
        "predictions":
            prediction_count,
        "ground_truth":
            ground_truth_count,
        "tp":
            tp,
        "fp":
            fp,
        "fn":
            fn,
        "precision":
            precision,
        "recall":
            recall,
        "f1":
            f1,
        "count_mae":
            count_mae,
        "mean_tp_iou":
            mean_tp_iou,
    }


# ==========================================================
# SWEEP
# ==========================================================

def sweep_model(
    model_name,
    model_path,
    dataset,
    loader,
    device,
):
    print(
        "\n"
        + "=" * 115
    )
    print(
        f"{model_name} — CORRECTED AMBULANCE SWEEP"
    )
    print(
        "=" * 115
    )
    print(
        "Model:",
        model_path
    )

    model = load_model(
        model_path,
        device,
    )

    cached = cache_model_predictions(
        model,
        dataset,
        loader,
        device,
    )

    del model

    if device.type == "cuda":
        torch.cuda.empty_cache()

    print(
        "\nRaw predictions cached. "
        "Starting post-processing sweep..."
    )

    results = []

    for confidence in CONF_THRESHOLDS:
        for nms in NMS_THRESHOLDS:
            for containment in CONTAINMENT_THRESHOLDS:

                result = evaluate_configuration(
                    cached,
                    confidence,
                    nms,
                    containment,
                )

                results.append(
                    result
                )

    results.sort(
        key=lambda r: (
            r["f1"],
            r["recall"],
            r["precision"],
        ),
        reverse=True,
    )

    print(
        "\nTOP 10 CONFIGURATIONS"
    )
    print(
        "-" * 115
    )

    for rank, result in enumerate(
        results[:10],
        start=1,
    ):
        containment = (
            "None"
            if result["containment"] is None
            else f"{result['containment']:.2f}"
        )

        print(
            f"{rank:2d}. "
            f"conf={result['confidence']:.2f} "
            f"NMS={result['nms']:.2f} "
            f"contain={containment:>4} | "
            f"Pred={result['predictions']:3d} "
            f"GT={result['ground_truth']:3d} | "
            f"TP={result['tp']:3d} "
            f"FP={result['fp']:3d} "
            f"FN={result['fn']:3d} | "
            f"P={result['precision']:.4f} "
            f"R={result['recall']:.4f} "
            f"F1={result['f1']:.4f} | "
            f"CountMAE={result['count_mae']:.2f} "
            f"MeanTP-IoU={result['mean_tp_iou']:.4f}"
        )

    best = results[0]

    print(
        "\nBEST",
        model_name
    )
    print(
        "-" * 115
    )
    print(
        f"Confidence          : "
        f"{best['confidence']:.2f}"
    )
    print(
        f"NMS IoU             : "
        f"{best['nms']:.2f}"
    )
    print(
        "Directional contain :",
        best["containment"]
    )
    print(
        f"Pred / GT           : "
        f"{best['predictions']} / "
        f"{best['ground_truth']}"
    )
    print(
        f"TP / FP / FN        : "
        f"{best['tp']} / "
        f"{best['fp']} / "
        f"{best['fn']}"
    )
    print(
        f"Precision           : "
        f"{best['precision']:.4f}"
    )
    print(
        f"Recall              : "
        f"{best['recall']:.4f}"
    )
    print(
        f"F1                  : "
        f"{best['f1']:.4f}"
    )
    print(
        f"Count MAE           : "
        f"{best['count_mae']:.4f}"
    )
    print(
        f"Mean TP IoU         : "
        f"{best['mean_tp_iou']:.4f}"
    )

    return best


# ==========================================================
# MAIN
# ==========================================================

def main():

    print(
        "=" * 115
    )
    print(
        "FINAL FAIR AMBULANCE POST-PROCESSING COMPARISON"
    )
    print(
        "=" * 115
    )

    for name, path in MODELS.items():
        if not path.exists():
            raise FileNotFoundError(
                f"{name} model not found:\n"
                f"{path}"
            )

    required_functions = [
        "decode_head",
        "TrafficDetectorV4",
        "TrafficDatasetV4",
    ]

    missing = [
        name
        for name in required_functions
        if not hasattr(ev, name)
    ]

    if missing:
        raise AttributeError(
            "evaluate_v4.py is missing required "
            "interface(s): "
            + ", ".join(missing)
        )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        "Device             :",
        device
    )
    print(
        "Official match IoU :",
        MATCH_IOU
    )
    print(
        "Raw decode         : "
        "decode_head(small) + decode_head(large)"
    )
    print(
        "NMS                : "
        "applied exactly once by this script"
    )
    print(
        "Containment        : "
        "intersection / area(lower-confidence candidate)"
    )

    dataset = get_ambulance_dataset()

    print(
        "Ambulance images   :",
        len(dataset)
    )

    final_results = {}

    # Build a fresh loader per model so worker state is clean.
    for model_name, model_path in MODELS.items():

        loader = make_loader(
            dataset,
            device,
        )

        final_results[model_name] = (
            sweep_model(
                model_name,
                model_path,
                dataset,
                loader,
                device,
            )
        )

    print(
        "\n"
        + "=" * 115
    )
    print(
        "FINAL CORRECTED COMPARISON"
    )
    print(
        "=" * 115
    )

    for model_name in (
        "V4",
        "V4.1",
    ):
        result = final_results[
            model_name
        ]

        print(
            f"{model_name:<4} | "
            f"F1={result['f1']:.4f} | "
            f"P={result['precision']:.4f} | "
            f"R={result['recall']:.4f} | "
            f"TP={result['tp']} "
            f"FP={result['fp']} "
            f"FN={result['fn']} | "
            f"CountMAE="
            f"{result['count_mae']:.2f} | "
            f"MeanTP-IoU="
            f"{result['mean_tp_iou']:.4f} | "
            f"conf="
            f"{result['confidence']:.2f} "
            f"NMS="
            f"{result['nms']:.2f} "
            f"contain="
            f"{result['containment']}"
        )

    ambulance_winner = max(
        final_results,
        key=lambda name:
            final_results[name]["f1"],
    )

    print(
        "\nBest corrected ambulance F1:",
        ambulance_winner
    )

    print(
        "\nRemember:"
    )
    print(
        "- Final project-model selection must also "
        "consider BMD F1 and BMD Count MAE."
    )
    print(
        "- V4 BMD baseline: F1 0.5831, Count MAE 3.14."
    )
    print(
        "- V4.1 BMD result : F1 0.5979, Count MAE 2.95."
    )

    print(
        "=" * 115
    )


if __name__ == "__main__":
    main()
