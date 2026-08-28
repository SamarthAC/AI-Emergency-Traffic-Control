import torch
from PIL import Image, ImageDraw
import numpy as np
from pathlib import Path

from model import TrafficCNN


# ==================================================
# SETTINGS
# ==================================================

NUM_CLASSES = 14
GRID_SIZE = 28
IMAGE_SIZE = 224

CONFIDENCE_THRESHOLD = 0.10
NMS_IOU_THRESHOLD = 0.40


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
    "Other"
]


# ==================================================
# PATHS
# ==================================================

BASE_DIR = Path(__file__).parent.parent

MODEL_PATH = BASE_DIR / "traffic_detector.pth"

VAL_IMAGE_DIR = (
    BASE_DIR
    / "dataset"
    / "val"
    / "images"
)

OUTPUT_PATH = (
    BASE_DIR
    / "predicted_detection.png"
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
# NON-MAXIMUM SUPPRESSION
# ==================================================

def nms(
    detections,
    iou_threshold=0.40
):

    detections = sorted(
        detections,
        key=lambda x: x["confidence"],
        reverse=True
    )

    kept = []

    while len(detections) > 0:

        best = detections.pop(0)

        kept.append(best)

        remaining = []

        for detection in detections:

            # -----------------------------------
            # Class-aware NMS
            # -----------------------------------

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


            # -----------------------------------
            # Calculate overlap
            # -----------------------------------

            iou = calculate_iou(
                best["box"],
                detection["box"]
            )


            # Keep boxes that do NOT
            # overlap too strongly
            if iou < iou_threshold:

                remaining.append(
                    detection
                )

        detections = remaining

    return kept


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
# LOAD MODEL
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
    "Model loaded successfully!"
)


# ==================================================
# SELECT VALIDATION IMAGE
# ==================================================

image_files = sorted(
    VAL_IMAGE_DIR.glob("*.png")
)


if len(image_files) == 0:

    raise FileNotFoundError(
        f"No validation images found in "
        f"{VAL_IMAGE_DIR}"
    )


# First validation image
image_path = image_files[0]

VAL_LABEL_DIR = (
    BASE_DIR
    / "dataset"
    / "val"
    / "labels"
)

print(
    "Testing image:",
    image_path
)

import json

label_path = (
    VAL_LABEL_DIR
    / f"{image_path.stem}.json"
)

with open(
    label_path,
    "r"
) as file:

    label_data = json.load(file)

ground_truth_objects = (
    label_data["objects"]["bbox"]
)

ground_truth_classes = (
    label_data["objects"]["categories"]
)

print(
    "Ground-truth vehicles:",
    len(ground_truth_objects)
)

print(
    "Ground-truth classes:",
    ground_truth_classes
)


# ==================================================
# LOAD ORIGINAL IMAGE
# ==================================================

original_image = Image.open(
    image_path
).convert("RGB")


original_width, original_height = (
    original_image.size
)


# ==================================================
# PREPROCESS IMAGE
# ==================================================

resized_image = original_image.resize(
    (IMAGE_SIZE, IMAGE_SIZE)
)


image_array = np.asarray(
    resized_image,
    dtype=np.float32
)


image_array = (
    image_array
    / 255.0
)


image_tensor = torch.from_numpy(
    image_array
)


# HWC → CHW
image_tensor = image_tensor.permute(
    2,
    0,
    1
)


# CHW → BCHW
image_tensor = image_tensor.unsqueeze(
    0
)


image_tensor = image_tensor.to(
    device
)


# ==================================================
# RUN CNN
# ==================================================

with torch.no_grad():

    prediction = model(
        image_tensor
    )


prediction = (
    prediction[0]
    .detach()
    .cpu()
)


print(
    "Prediction shape:",
    prediction.shape
)

# ==================================================
# DEBUG CONFIDENCE VALUES
# ==================================================

max_objectness = 0.0
max_class_probability = 0.0
max_combined_confidence = 0.0

for row in range(GRID_SIZE):

    for col in range(GRID_SIZE):

        objectness = torch.sigmoid(
            prediction[0, row, col]
        ).item()

        class_logits = prediction[
            5:,
            row,
            col
        ]

        class_probabilities = torch.softmax(
            class_logits,
            dim=0
        )

        class_probability = torch.max(
            class_probabilities
        ).item()

        combined = (
            objectness
            * class_probability
        )

        max_objectness = max(
            max_objectness,
            objectness
        )

        max_class_probability = max(
            max_class_probability,
            class_probability
        )

        max_combined_confidence = max(
            max_combined_confidence,
            combined
        )


print("\n===== MODEL CONFIDENCE DEBUG =====")

print(
    "Max objectness:",
    round(max_objectness, 4)
)

print(
    "Max class probability:",
    round(max_class_probability, 4)
)

print(
    "Max combined confidence:",
    round(max_combined_confidence, 4)
)

# ==================================================
# DECODE PREDICTIONS
# ==================================================

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
        # CLASS PREDICTION
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


        class_probability, class_id = (
            torch.max(
                class_probabilities,
                dim=0
            )
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

        # Instead of using only:
        #
        # objectness
        #
        # we combine:
        #
        # P(object) × P(class | object)

        confidence = (
            objectness
            * class_probability
        )


        if (
            confidence
            < CONFIDENCE_THRESHOLD
        ):
            continue


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


        # ------------------------------------------
        # CELL → IMAGE CENTER COORDINATES
        # ------------------------------------------

        center_x = (
            col + tx
        ) / GRID_SIZE


        center_y = (
            row + ty
        ) / GRID_SIZE


        # ------------------------------------------
        # CENTER → CORNER FORMAT
        # ------------------------------------------

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


        # ------------------------------------------
        # CLAMP TO IMAGE
        # ------------------------------------------

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


        # ------------------------------------------
        # REJECT INVALID BOXES
        # ------------------------------------------

        if x2 <= x1:
            continue

        if y2 <= y1:
            continue


        class_name = CLASS_NAMES[
            class_id
        ]


        detections.append(
            {
                "confidence":
                    confidence,

                "objectness":
                    objectness,

                "class_probability":
                    class_probability,

                "class_id":
                    class_id,

                "class_name":
                    class_name,

                "box":
                    (
                        x1,
                        y1,
                        x2,
                        y2
                    )
            }
        )


# ==================================================
# BEFORE NMS
# ==================================================

detections.sort(
    key=lambda x: x["confidence"],
    reverse=True
)


print(
    "\nBefore NMS:",
    len(detections)
)

# ==================================================
# THRESHOLD ANALYSIS
# ==================================================

print("\n===== THRESHOLD ANALYSIS =====")

thresholds = [
    0.10,
    0.15,
    0.20,
    0.25,
    0.30,
    0.35,
    0.40
]

for threshold in thresholds:

    filtered = [
        d for d in detections
        if d["confidence"] >= threshold
    ]

    filtered_nms = nms(
        filtered.copy(),
        iou_threshold=NMS_IOU_THRESHOLD
    )

    print(
        f"Threshold {threshold:.2f} | "
        f"Before NMS: {len(filtered):3d} | "
        f"After NMS: {len(filtered_nms):3d}"
    )
# ==================================================
# APPLY NMS
# ==================================================

detections = nms(
    detections,
    iou_threshold=NMS_IOU_THRESHOLD
)


print(
    "After NMS:",
    len(detections)
)


print(
    "Final detections:",
    len(detections)
)


# ==================================================
# DRAW DETECTIONS
# ==================================================

draw = ImageDraw.Draw(
    original_image
)


for detection in detections:

    x1, y1, x2, y2 = (
        detection["box"]
    )


    # Normalized coordinates
    # → original image pixels

    pixel_x1 = int(
        x1 * original_width
    )

    pixel_y1 = int(
        y1 * original_height
    )

    pixel_x2 = int(
        x2 * original_width
    )

    pixel_y2 = int(
        y2 * original_height
    )


    # ------------------------------------------
    # DRAW BOX
    # ------------------------------------------

    draw.rectangle(
        [
            pixel_x1,
            pixel_y1,
            pixel_x2,
            pixel_y2
        ],
        outline="red",
        width=4
    )


    # ------------------------------------------
    # DRAW LABEL
    # ------------------------------------------

    label = (
        f"{detection['class_name']} "
        f"{detection['confidence']:.2f}"
    )


    text_y = max(
        0,
        pixel_y1 - 15
    )


    draw.text(
        (
            pixel_x1,
            text_y
        ),
        label,
        fill="red"
    )


    # Terminal output
    print(
        f"{detection['class_name']:18s}",
        f"Confidence: "
        f"{detection['confidence']:.3f}",
        f"Objectness: "
        f"{detection['objectness']:.3f}",
        f"Class Prob: "
        f"{detection['class_probability']:.3f}"
    )


# ==================================================
# SAVE RESULT
# ==================================================

original_image.save(
    OUTPUT_PATH
)


print(
    "\nPrediction saved to:",
    OUTPUT_PATH
)