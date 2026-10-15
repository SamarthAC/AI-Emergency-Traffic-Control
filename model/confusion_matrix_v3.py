import torch
from PIL import Image
import numpy as np
import json
from pathlib import Path

import matplotlib.pyplot as plt

from model import TrafficCNN


# ==================================================
# SETTINGS
# ==================================================

NUM_CLASSES = 14

GRID_SIZE = 28
IMAGE_SIZE = 448

CONFIDENCE_THRESHOLD = 0.55

NMS_IOU_THRESHOLD = 0.40
MATCH_IOU_THRESHOLD = 0.50


CLASS_NAMES = [

    "Hatchback",
    "Sedan",
    "SUV",
    "MUV",
    "Bus",
    "Truck",
    "Three-wheeler",
    "Two-wheeler",
    "LCV",
    "Mini-bus",
    "Tempo-traveller",
    "Bicycle",
    "Van",
    "Other",

    # Extra class used only for
    # false positives / false negatives
    "Background"
]


BACKGROUND_ID = NUM_CLASSES


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


OUTPUT_PATH = (
    BASE_DIR
    / "confusion_matrix_v3.png"
)


NORMALIZED_OUTPUT_PATH = (
    BASE_DIR
    / "confusion_matrix_v3_normalized.png"
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

            # Different classes are kept separately
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
# DECODE CNN OUTPUT
# ==================================================

def decode_predictions(
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
            # FINAL CONFIDENCE
            # ------------------------------------------

            confidence = (
                objectness
                * class_probability
            )


            if confidence < CONFIDENCE_THRESHOLD:

                continue


            # ------------------------------------------
            # BBOX
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


            # Clamp
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
                    "confidence": confidence,

                    "class_id": class_id,

                    "box": (
                        x1,
                        y1,
                        x2,
                        y2
                    )
                }
            )


    return nms(
        detections,
        NMS_IOU_THRESHOLD
    )


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

        x2 = x + width
        y2 = y + height


        # ------------------------------------------
        # Clamp
        # ------------------------------------------

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


        if x2 <= x1:
            continue

        if y2 <= y1:
            continue


        # ------------------------------------------
        # Normalize
        # ------------------------------------------

        x1 /= image_width
        x2 /= image_width

        y1 /= image_height
        y2 /= image_height


        ground_truth.append(
            {
                "class_id":
                    int(class_id),

                "box": (
                    x1,
                    y1,
                    x2,
                    y2
                )
            }
        )


    return ground_truth


# ==================================================
# MATCH FOR CONFUSION MATRIX
# ==================================================

def update_confusion_matrix(
    predictions,
    ground_truth,
    matrix
):

    # Predictions are checked from
    # highest confidence to lowest
    predictions = sorted(
        predictions,
        key=lambda x: x["confidence"],
        reverse=True
    )


    matched_gt = set()


    for prediction in predictions:

        best_iou = 0.0

        best_gt_index = None


        # IMPORTANT:
        # We do NOT require the classes to match here.
        #
        # Otherwise Sedan -> SUV confusion
        # would never appear in the matrix.

        for gt_index, gt in enumerate(
            ground_truth
        ):

            if gt_index in matched_gt:

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


        # ------------------------------------------
        # MATCHED DETECTION
        # ------------------------------------------

        if (
            best_gt_index is not None
            and
            best_iou >= MATCH_IOU_THRESHOLD
        ):

            gt = ground_truth[
                best_gt_index
            ]


            actual_class = (
                gt["class_id"]
            )

            predicted_class = (
                prediction["class_id"]
            )


            matrix[
                actual_class,
                predicted_class
            ] += 1


            matched_gt.add(
                best_gt_index
            )


        # ------------------------------------------
        # FALSE POSITIVE
        # Background -> predicted class
        # ------------------------------------------

        else:

            predicted_class = (
                prediction["class_id"]
            )


            matrix[
                BACKGROUND_ID,
                predicted_class
            ] += 1


    # ==============================================
    # UNMATCHED GT = FALSE NEGATIVE
    # Actual class -> Background
    # ==============================================

    for gt_index, gt in enumerate(
        ground_truth
    ):

        if gt_index not in matched_gt:

            actual_class = (
                gt["class_id"]
            )


            matrix[
                actual_class,
                BACKGROUND_ID
            ] += 1


# ==================================================
# DRAW MATRIX
# ==================================================

def draw_matrix(
    matrix,
    class_names,
    output_path,
    title,
    normalized=False
):

    display_matrix = (
        matrix.astype(np.float64)
    )


    if normalized:

        row_sums = (
            display_matrix.sum(
                axis=1,
                keepdims=True
            )
        )


        display_matrix = np.divide(
            display_matrix,
            row_sums,
            out=np.zeros_like(
                display_matrix
            ),
            where=row_sums != 0
        )


    fig, ax = plt.subplots(
        figsize=(15, 13)
    )


    image = ax.imshow(
        display_matrix
    )


    fig.colorbar(
        image,
        ax=ax
    )


    ax.set_xticks(
        np.arange(
            len(class_names)
        )
    )

    ax.set_yticks(
        np.arange(
            len(class_names)
        )
    )


    ax.set_xticklabels(
        class_names,
        rotation=90
    )


    ax.set_yticklabels(
        class_names
    )


    ax.set_xlabel(
        "Predicted Class"
    )

    ax.set_ylabel(
        "Actual Class"
    )


    ax.set_title(
        title
    )


    # ------------------------------------------
    # Write values inside cells
    # ------------------------------------------

    for row in range(
        len(class_names)
    ):

        for col in range(
            len(class_names)
        ):

            value = display_matrix[
                row,
                col
            ]


            if normalized:

                text = (
                    f"{value:.2f}"
                )

            else:

                text = str(
                    int(value)
                )


            ax.text(
                col,
                row,
                text,
                ha="center",
                va="center",
                fontsize=6
            )


    fig.tight_layout()


    plt.savefig(
        output_path,
        dpi=250,
        bbox_inches="tight"
    )


    plt.close(fig)


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
# LOAD V3 MODEL
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
    "Match IoU threshold:",
    MATCH_IOU_THRESHOLD
)


# ==================================================
# VALIDATION IMAGES
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
# CONFUSION MATRIX
#
# 14 vehicle classes
# +
# 1 background class
# ==================================================

confusion_matrix = np.zeros(
    (
        NUM_CLASSES + 1,
        NUM_CLASSES + 1
    ),
    dtype=np.int64
)


# ==================================================
# RUN EVALUATION
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
        # CNN
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


        predictions = (
            decode_predictions(
                prediction
            )
        )


        # ------------------------------------------
        # GT
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


        # ------------------------------------------
        # UPDATE MATRIX
        # ------------------------------------------

        update_confusion_matrix(
            predictions,
            ground_truth,
            confusion_matrix
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
# PRINT MATRIX
# ==================================================

print(
    "\n============================================"
)

print(
    "V3 CONFUSION MATRIX"
)

print(
    "============================================"
)


print(
    confusion_matrix
)


# ==================================================
# GENERATE RAW MATRIX
# ==================================================

draw_matrix(

    confusion_matrix,

    CLASS_NAMES,

    OUTPUT_PATH,

    (
        "V3 Object Detection Confusion Matrix "
        "(Confidence = 0.55)"
    ),

    normalized=False
)


# ==================================================
# GENERATE NORMALIZED MATRIX
# ==================================================

draw_matrix(

    confusion_matrix,

    CLASS_NAMES,

    NORMALIZED_OUTPUT_PATH,

    (
        "V3 Normalized Object Detection "
        "Confusion Matrix"
    ),

    normalized=True
)


print(
    "\nSaved raw confusion matrix:"
)

print(
    OUTPUT_PATH
)


print(
    "\nSaved normalized confusion matrix:"
)

print(
    NORMALIZED_OUTPUT_PATH
)


print(
    "\nConfusion matrix complete."
)