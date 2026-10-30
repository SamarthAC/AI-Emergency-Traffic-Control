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

# NMS stays exactly the same as V3 evaluation
NMS_IOU_THRESHOLD = 0.40

# Confidence is FIXED at V3's selected threshold
CONFIDENCE_THRESHOLD = 0.55

# We only change the IoU used for GT matching
MATCH_IOU_THRESHOLDS = [
    0.30,
    0.40,
    0.50,
    0.60
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

    x1 = max(
        box1[0],
        box2[0]
    )

    y1 = max(
        box1[1],
        box2[1]
    )

    x2 = min(
        box1[2],
        box2[2]
    )

    y2 = min(
        box1[3],
        box2[3]
    )

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

            # Different classes should NOT
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
# DECODE ALL CNN CANDIDATES
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

            class_probabilities = torch.softmax(
                class_logits,
                dim=0
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


            # Grid-relative center -> normalized center

            center_x = (
                col + tx
            ) / GRID_SIZE

            center_y = (
                row + ty
            ) / GRID_SIZE


            # Center xywh -> corner xyxy

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


            # Skip invalid boxes

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

        data = json.load(
            file
        )


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


        # Clamp to original image dimensions

        x1 = max(
            0.0,
            min(
                float(image_width),
                x1
            )
        )

        y1 = max(
            0.0,
            min(
                float(image_height),
                y1
            )
        )

        x2 = max(
            0.0,
            min(
                float(image_width),
                x2
            )
        )

        y2 = max(
            0.0,
            min(
                float(image_height),
                y2
            )
        )


        # Skip invalid boxes

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
# MATCH PREDICTIONS TO GROUND TRUTH
# ==================================================

def match_detections(
    predictions,
    ground_truth,
    match_iou_threshold
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

            # GT already matched
            if gt_index in matched_gt:
                continue


            # IMPORTANT:
            # Standard detection evaluation requires
            # prediction and GT to have same class.

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


        # Match using CURRENT IoU threshold

        if (
            best_gt_index is not None
            and
            best_iou >= match_iou_threshold
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
# LOAD V3 BEST MODEL
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
    "Confidence threshold:",
    CONFIDENCE_THRESHOLD
)

print(
    "NMS IoU threshold:",
    NMS_IOU_THRESHOLD
)

print(
    "Match IoU thresholds:",
    MATCH_IOU_THRESHOLDS
)


# ==================================================
# VALIDATION FILES
# ==================================================

image_files = sorted(
    VAL_IMAGE_DIR.glob(
        "*.png"
    )
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


for match_iou in MATCH_IOU_THRESHOLDS:

    results[match_iou] = {
        "tp": 0,
        "fp": 0,
        "fn": 0
    }


total_ground_truth = 0
total_predictions = 0


# ==================================================
# EVALUATE ALL 500 IMAGES
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
        ).convert(
            "RGB"
        )


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
        # CNN RUNS ONCE FOR THIS IMAGE
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
        # DECODE ALL CANDIDATES
        # ------------------------------------------

        candidates = (
            decode_all_candidates(
                prediction
            )
        )


        # ------------------------------------------
        # LOAD GT
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
        # FIX CONFIDENCE AT 0.55
        # ------------------------------------------

        filtered = [

            detection

            for detection in candidates

            if (
                detection["confidence"]
                >= CONFIDENCE_THRESHOLD
            )
        ]


        # ------------------------------------------
        # APPLY SAME CLASS-AWARE NMS
        # ------------------------------------------

        filtered = nms(
            filtered,
            NMS_IOU_THRESHOLD
        )


        total_predictions += (
            len(filtered)
        )


        # ------------------------------------------
        # TEST ALL MATCH IoU THRESHOLDS
        # ------------------------------------------

        for match_iou in (
            MATCH_IOU_THRESHOLDS
        ):

            (
                tp,
                fp,
                fn
            ) = match_detections(
                filtered,
                ground_truth,
                match_iou
            )


            results[
                match_iou
            ]["tp"] += tp


            results[
                match_iou
            ]["fp"] += fp


            results[
                match_iou
            ]["fn"] += fn


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
# PRINT RESULTS
# ==================================================

print(
    "\n==============================================================="
)

print(
    "                     IoU SENSITIVITY SWEEP"
)

print(
    "==============================================================="
)


print(
    f"{'IoU':<8}"
    f"{'TP':<8}"
    f"{'FP':<9}"
    f"{'FN':<9}"
    f"{'Prec':<10}"
    f"{'Recall':<10}"
    f"{'F1':<10}"
)


print(
    "-" * 64
)


for match_iou in MATCH_IOU_THRESHOLDS:

    result = results[
        match_iou
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


    print(
        f"{match_iou:<8.2f}"
        f"{tp:<8}"
        f"{fp:<9}"
        f"{fn:<9}"
        f"{precision:<10.4f}"
        f"{recall:<10.4f}"
        f"{f1:<10.4f}"
    )


# ==================================================
# SUMMARY
# ==================================================

print(
    "\n==============================================================="
)

print(
    "Validation images:",
    len(image_files)
)

print(
    "Ground-truth objects:",
    total_ground_truth
)

print(
    "Predictions at confidence 0.55:",
    total_predictions
)

print(
    "Confidence threshold:",
    CONFIDENCE_THRESHOLD
)

print(
    "NMS IoU threshold:",
    NMS_IOU_THRESHOLD
)

print(
    "IoU sensitivity sweep complete."
)

print(
    "==============================================================="
)