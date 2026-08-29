import torch
from PIL import Image
import numpy as np
import json
from pathlib import Path


# ==================================================
# IMPORT MODEL
# ==================================================

from model import TrafficCNN


# ==================================================
# SETTINGS
# ==================================================

NUM_CLASSES = 14
GRID_SIZE = 28
IMAGE_SIZE = 448

NMS_IOU_THRESHOLD = 0.40
MATCH_IOU_THRESHOLD = 0.50

CONFIDENCE_THRESHOLDS = [
    0.20,
    0.25,
    0.30,
    0.35,
    0.40,
    0.45,
    0.50,
    0.55,
    0.60,
    0.65,
    0.70
]

# ==================================================
# PATHS
# ==================================================

BASE_DIR = Path(__file__).parent.parent

MODEL_PATH = (
    BASE_DIR
    / "traffic_detector_v3_best.pth"
)

VAL_IMAGE_DIR = (
    BASE_DIR
    / "dataset"
    / "val"
    / "images"
)

VAL_LABEL_DIR = (
    BASE_DIR
    / "dataset"
    / "val"
    / "labels"
)


# ==================================================
# IoU
# ==================================================

def calculate_iou(box1, box2):

    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])

    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection_width = max(
        0.0,
        x2 - x1
    )

    intersection_height = max(
        0.0,
        y2 - y1
    )

    intersection_area = (
        intersection_width
        * intersection_height
    )

    box1_area = max(
        0.0,
        box1[2] - box1[0]
    ) * max(
        0.0,
        box1[3] - box1[1]
    )

    box2_area = max(
        0.0,
        box2[2] - box2[0]
    ) * max(
        0.0,
        box2[3] - box2[1]
    )

    union_area = (
        box1_area
        + box2_area
        - intersection_area
    )

    if union_area <= 0:
        return 0.0

    return (
        intersection_area
        / union_area
    )


# ==================================================
# CLASS-AWARE NMS
# ==================================================

def nms(
    detections,
    iou_threshold=NMS_IOU_THRESHOLD
):

    detections = sorted(
        detections,
        key=lambda x: x["confidence"],
        reverse=True
    )

    kept = []

    while detections:

        best = detections.pop(0)

        kept.append(best)

        remaining = []

        for detection in detections:

            # Different classes should not
            # suppress each other
            if (
                detection["class_id"]
                != best["class_id"]
            ):

                remaining.append(
                    detection
                )

                continue

            iou = calculate_iou(
                best["box"],
                detection["box"]
            )

            if iou < iou_threshold:

                remaining.append(
                    detection
                )

        detections = remaining

    return kept


# ==================================================
# DECODE ALL CANDIDATES
#
# IMPORTANT:
# We do NOT apply confidence threshold here.
#
# CNN runs once per image.
# Then different thresholds reuse these candidates.
# ==================================================

def decode_all_candidates(
    prediction
):

    detections = []

    for row in range(GRID_SIZE):

        for col in range(GRID_SIZE):

            # ------------------------------------------
            # OBJECTNESS
            # ------------------------------------------

            objectness = torch.sigmoid(
                prediction[
                    0,
                    row,
                    col
                ]
            ).item()


            # ------------------------------------------
            # CLASS
            # ------------------------------------------

            class_logits = prediction[
                5:,
                row,
                col
            ]

            class_probabilities = (
                torch.softmax(
                    class_logits,
                    dim=0
                )
            )

            (
                class_probability,
                class_id
            ) = torch.max(
                class_probabilities,
                dim=0
            )

            class_probability = (
                class_probability.item()
            )

            class_id = (
                class_id.item()
            )


            # ------------------------------------------
            # COMBINED CONFIDENCE
            # ------------------------------------------

            confidence = (
                objectness
                * class_probability
            )


            # ------------------------------------------
            # BOUNDING BOX
            # ------------------------------------------

            tx = torch.sigmoid(
                prediction[
                    1,
                    row,
                    col
                ]
            ).item()

            ty = torch.sigmoid(
                prediction[
                    2,
                    row,
                    col
                ]
            ).item()

            width = torch.sigmoid(
                prediction[
                    3,
                    row,
                    col
                ]
            ).item()

            height = torch.sigmoid(
                prediction[
                    4,
                    row,
                    col
                ]
            ).item()


            center_x = (
                col + tx
            ) / GRID_SIZE

            center_y = (
                row + ty
            ) / GRID_SIZE


            x1 = (
                center_x
                - width / 2
            )

            y1 = (
                center_y
                - height / 2
            )

            x2 = (
                center_x
                + width / 2
            )

            y2 = (
                center_y
                + height / 2
            )


            # Clamp to normalized image area
            x1 = max(
                0.0,
                min(1.0, x1)
            )

            y1 = max(
                0.0,
                min(1.0, y1)
            )

            x2 = max(
                0.0,
                min(1.0, x2)
            )

            y2 = max(
                0.0,
                min(1.0, y2)
            )


            if x2 <= x1:
                continue

            if y2 <= y1:
                continue


            detections.append(
                {
                    "confidence":
                        confidence,

                    "class_id":
                        class_id,

                    "box":
                        (
                            x1,
                            y1,
                            x2,
                            y2
                        )
                }
            )

    return detections


# ==================================================
# LOAD GROUND TRUTH
# ==================================================

def load_ground_truth(
    label_path
):

    with open(
        label_path,
        "r"
    ) as file:

        data = json.load(file)


    raw_boxes = (
        data["objects"]["bbox"]
    )

    raw_classes = (
        data["objects"]["categories"]
    )


    image_width = data.get(
        "width",
        1920
    )

    image_height = data.get(
        "height",
        1080
    )


    ground_truth = []


    for bbox, class_id in zip(
        raw_boxes,
        raw_classes
    ):

        x, y, width, height = bbox


        x1 = x
        y1 = y

        x2 = (
            x + width
        )

        y2 = (
            y + height
        )


        # Clamp
        x1 = max(
            0.0,
            min(float(image_width), x1)
        )

        y1 = max(
            0.0,
            min(float(image_height), y1)
        )

        x2 = max(
            0.0,
            min(float(image_width), x2)
        )

        y2 = max(
            0.0,
            min(float(image_height), y2)
        )


        if x2 <= x1:
            continue

        if y2 <= y1:
            continue


        # Normalize
        x1 /= image_width
        x2 /= image_width

        y1 /= image_height
        y2 /= image_height


        ground_truth.append(
            {
                "class_id":
                    int(class_id),

                "box":
                    (
                        x1,
                        y1,
                        x2,
                        y2
                    )
            }
        )

    return ground_truth


# ==================================================
# MATCH PREDICTIONS TO GT
# ==================================================

def match_detections(
    predictions,
    ground_truth
):

    predictions = sorted(
        predictions,
        key=lambda x: x["confidence"],
        reverse=True
    )

    matched_gt = set()

    tp = 0
    fp = 0


    for prediction in predictions:

        best_iou = 0.0
        best_gt_index = None


        for gt_index, gt in enumerate(
            ground_truth
        ):

            if gt_index in matched_gt:
                continue


            # Require correct class
            if (
                prediction["class_id"]
                != gt["class_id"]
            ):
                continue


            iou = calculate_iou(
                prediction["box"],
                gt["box"]
            )


            if iou > best_iou:

                best_iou = iou

                best_gt_index = (
                    gt_index
                )


        if (
            best_gt_index is not None
            and
            best_iou
            >= MATCH_IOU_THRESHOLD
        ):

            tp += 1

            matched_gt.add(
                best_gt_index
            )

        else:

            fp += 1


    fn = (
        len(ground_truth)
        - len(matched_gt)
    )


    return tp, fp, fn


# ==================================================
# DEVICE
# ==================================================

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


print(
    "Using device:",
    device
)


# ==================================================
# LOAD BEST MODEL
# ==================================================

model = TrafficCNN(
    num_classes=NUM_CLASSES
).to(device)


state_dict = torch.load(
    MODEL_PATH,
    map_location=device,
    weights_only=True
)


model.load_state_dict(
    state_dict
)

model.eval()


print(
    "Loaded model:",
    MODEL_PATH
)

print(
    "Match IoU threshold:",
    MATCH_IOU_THRESHOLD
)


# ==================================================
# VALIDATION FILES
# ==================================================

image_files = sorted(
    VAL_IMAGE_DIR.glob("*.png")
)


if len(image_files) == 0:

    raise FileNotFoundError(
        f"No validation images found in "
        f"{VAL_IMAGE_DIR}"
    )


print(
    "Validation images:",
    len(image_files)
)


# ==================================================
# RESULT STORAGE
# ==================================================

results = {}


for threshold in (
    CONFIDENCE_THRESHOLDS
):

    results[threshold] = {

        "tp": 0,
        "fp": 0,
        "fn": 0,

        "predictions": 0,

        "absolute_count_error": 0
    }


total_ground_truth = 0


# ==================================================
# EVALUATE
# ==================================================

with torch.no_grad():

    for image_index, image_path in enumerate(
        image_files
    ):

        # ------------------------------------------
        # LOAD IMAGE
        # ------------------------------------------

        image = Image.open(
            image_path
        ).convert("RGB")


        image = image.resize(
            (
                IMAGE_SIZE,
                IMAGE_SIZE
            )
        )


        image_array = np.asarray(
            image,
            dtype=np.float32
        ) / 255.0


        image_tensor = (
            torch.from_numpy(
                image_array
            )
            .permute(
                2,
                0,
                1
            )
            .unsqueeze(0)
            .to(device)
        )


        # ------------------------------------------
        # CNN RUNS ONLY ONCE
        # ------------------------------------------

        with torch.amp.autocast(
            device_type=device.type,
            dtype=torch.float16,
            enabled=(
                device.type == "cuda"
            )
        ):

            prediction = model(
                image_tensor
            )


        prediction = (
            prediction[0]
            .float()
            .cpu()
        )


        # ------------------------------------------
        # DECODE ALL 28x28 CANDIDATES
        # ------------------------------------------

        candidates = (
            decode_all_candidates(
                prediction
            )
        )


        # ------------------------------------------
        # GROUND TRUTH
        # ------------------------------------------

        label_path = (
            VAL_LABEL_DIR
            / f"{image_path.stem}.json"
        )


        ground_truth = (
            load_ground_truth(
                label_path
            )
        )


        total_ground_truth += (
            len(ground_truth)
        )


        # ------------------------------------------
        # TEST EACH THRESHOLD
        # ------------------------------------------

        for threshold in (
            CONFIDENCE_THRESHOLDS
        ):

            filtered = [

                detection

                for detection
                in candidates

                if (
                    detection[
                        "confidence"
                    ]
                    >= threshold
                )
            ]


            # Apply NMS AFTER threshold
            filtered = nms(
                filtered,
                NMS_IOU_THRESHOLD
            )


            (
                tp,
                fp,
                fn
            ) = match_detections(
                filtered,
                ground_truth
            )


            results[
                threshold
            ]["tp"] += tp


            results[
                threshold
            ]["fp"] += fp


            results[
                threshold
            ]["fn"] += fn


            results[
                threshold
            ]["predictions"] += (
                len(filtered)
            )


            results[
                threshold
            ][
                "absolute_count_error"
            ] += abs(
                len(filtered)
                - len(ground_truth)
            )


        # ------------------------------------------
        # PROGRESS
        # ------------------------------------------

        if (
            image_index + 1
        ) % 50 == 0:

            print(
                f"Processed "
                f"{image_index + 1}/"
                f"{len(image_files)}"
            )


# ==================================================
# PRINT TABLE
# ==================================================

print(
    "\n==============================================================="
)

print(
    "                 CONFIDENCE THRESHOLD SWEEP"
)

print(
    "==============================================================="
)

print(
    f"{'Thresh':<8}"
    f"{'Pred':<9}"
    f"{'TP':<7}"
    f"{'FP':<9}"
    f"{'FN':<8}"
    f"{'Prec':<9}"
    f"{'Recall':<9}"
    f"{'F1':<9}"
    f"{'CountErr':<10}"
)

print(
    "-" * 78
)


best_f1 = -1.0
best_f1_threshold = None

best_count_error = float("inf")
best_count_threshold = None


for threshold in (
    CONFIDENCE_THRESHOLDS
):

    result = results[
        threshold
    ]


    tp = result["tp"]
    fp = result["fp"]
    fn = result["fn"]


    precision = (
        tp / (tp + fp)
        if (
            tp + fp
        ) > 0
        else 0.0
    )


    recall = (
        tp / (tp + fn)
        if (
            tp + fn
        ) > 0
        else 0.0
    )


    f1 = (
        2
        * precision
        * recall
        / (
            precision
            + recall
        )
        if (
            precision
            + recall
        ) > 0
        else 0.0
    )


    count_error = (
        result[
            "absolute_count_error"
        ]
        / len(image_files)
    )


    if f1 > best_f1:

        best_f1 = f1

        best_f1_threshold = (
            threshold
        )


    if (
        count_error
        < best_count_error
    ):

        best_count_error = (
            count_error
        )

        best_count_threshold = (
            threshold
        )


    print(
        f"{threshold:<8.2f}"
        f"{result['predictions']:<9}"
        f"{tp:<7}"
        f"{fp:<9}"
        f"{fn:<8}"
        f"{precision:<9.4f}"
        f"{recall:<9.4f}"
        f"{f1:<9.4f}"
        f"{count_error:<10.2f}"
    )


# ==================================================
# SUMMARY
# ==================================================

print(
    "\n==============================================================="
)

print(
    "Ground-truth objects:",
    total_ground_truth
)

print(
    "\nBest F1 threshold:",
    best_f1_threshold
)

print(
    "Best F1:",
    round(
        best_f1,
        4
    )
)

print(
    "\nBest vehicle-count threshold:",
    best_count_threshold
)

print(
    "Lowest mean count error/image:",
    round(
        best_count_error,
        2
    )
)

print(
    "\n==============================================================="
)

print(
    "Threshold sweep complete."
)

print(
    "==============================================================="
)