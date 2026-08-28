import json
import torch
import numpy as np
from PIL import Image
from pathlib import Path

from model import TrafficCNN


NUM_CLASSES = 14
GRID_SIZE = 28
IMAGE_SIZE = 224

CONFIDENCE_THRESHOLD = 0.30
IOU_MATCH_THRESHOLD = 0.50
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


BASE_DIR = Path(__file__).parent.parent

MODEL_PATH = BASE_DIR / "traffic_detector.pth"

IMAGE_PATH = (
    BASE_DIR
    / "dataset"
    / "val"
    / "images"
    / "val_0000.png"
)

LABEL_PATH = (
    BASE_DIR
    / "dataset"
    / "val"
    / "labels"
    / "val_0000.json"
)


# ==================================================
# IOU
# ==================================================

def calculate_iou(box1, box2):

    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])

    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = (
        max(0, x2 - x1)
        *
        max(0, y2 - y1)
    )

    area1 = (
        max(0, box1[2] - box1[0])
        *
        max(0, box1[3] - box1[1])
    )

    area2 = (
        max(0, box2[2] - box2[0])
        *
        max(0, box2[3] - box2[1])
    )

    union = area1 + area2 - intersection

    if union <= 0:
        return 0.0

    return intersection / union


# ==================================================
# NMS
# ==================================================

def nms(detections, threshold=0.4):

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

            if detection["class_id"] != best["class_id"]:

                remaining.append(detection)
                continue

            iou = calculate_iou(
                best["box"],
                detection["box"]
            )

            if iou < threshold:
                remaining.append(detection)

        detections = remaining

    return kept


# ==================================================
# LOAD GROUND TRUTH
# ==================================================

with open(LABEL_PATH, "r") as file:

    data = json.load(file)


image_width = data["image_width"]
image_height = data["image_height"]

gt_boxes = []
gt_classes = []


for box, class_id in zip(
    data["objects"]["bbox"],
    data["objects"]["categories"]
):

    x, y, w, h = box

    x1 = x / image_width
    y1 = y / image_height

    x2 = (x + w) / image_width
    y2 = (y + h) / image_height

    gt_boxes.append(
        (x1, y1, x2, y2)
    )

    gt_classes.append(
        class_id
    )


print(
    "Ground truth:",
    len(gt_boxes)
)


# ==================================================
# LOAD IMAGE
# ==================================================

image = Image.open(
    IMAGE_PATH
).convert("RGB")

image = image.resize(
    (IMAGE_SIZE, IMAGE_SIZE)
)

array = np.asarray(
    image,
    dtype=np.float32
) / 255.0

tensor = torch.from_numpy(
    array
).permute(
    2, 0, 1
).unsqueeze(0)


# ==================================================
# MODEL
# ==================================================

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

model = TrafficCNN(
    num_classes=NUM_CLASSES
).to(device)

model.load_state_dict(
    torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=True
    )
)

model.eval()

tensor = tensor.to(device)


# ==================================================
# PREDICT
# ==================================================

with torch.no_grad():

    prediction = model(tensor)[0].cpu()


detections = []


for row in range(GRID_SIZE):

    for col in range(GRID_SIZE):

        objectness = torch.sigmoid(
            prediction[0, row, col]
        ).item()

        class_probs = torch.softmax(
            prediction[5:, row, col],
            dim=0
        )

        class_prob, class_id = torch.max(
            class_probs,
            dim=0
        )

        class_prob = class_prob.item()
        class_id = class_id.item()

        confidence = (
            objectness
            *
            class_prob
        )


        if confidence < CONFIDENCE_THRESHOLD:
            continue


        tx = torch.sigmoid(
            prediction[1, row, col]
        ).item()

        ty = torch.sigmoid(
            prediction[2, row, col]
        ).item()

        w = torch.sigmoid(
            prediction[3, row, col]
        ).item()

        h = torch.sigmoid(
            prediction[4, row, col]
        ).item()


        cx = (
            col + tx
        ) / GRID_SIZE

        cy = (
            row + ty
        ) / GRID_SIZE


        x1 = max(
            0,
            cx - w / 2
        )

        y1 = max(
            0,
            cy - h / 2
        )

        x2 = min(
            1,
            cx + w / 2
        )

        y2 = min(
            1,
            cy + h / 2
        )


        detections.append(
            {
                "box": (
                    x1,
                    y1,
                    x2,
                    y2
                ),

                "class_id":
                    class_id,

                "confidence":
                    confidence
            }
        )


detections = nms(
    detections,
    NMS_IOU_THRESHOLD
)


print(
    "Predictions after NMS:",
    len(detections)
)


# ==================================================
# MATCH PREDICTIONS WITH GROUND TRUTH
# ==================================================

matched_gt = set()

true_positives = 0
false_positives = 0


for detection in detections:

    best_iou = 0
    best_gt_index = -1


    for i, gt_box in enumerate(gt_boxes):

        if i in matched_gt:
            continue

        iou = calculate_iou(
            detection["box"],
            gt_box
        )

        if iou > best_iou:

            best_iou = iou
            best_gt_index = i


    print(
        "\nPrediction:",
        CLASS_NAMES[
            detection["class_id"]
        ],
        f"{detection['confidence']:.3f}"
    )

    print(
        "Best IoU:",
        f"{best_iou:.3f}"
    )


    if (
        best_iou >= IOU_MATCH_THRESHOLD
        and
        best_gt_index != -1
    ):

        predicted_class = (
            detection["class_id"]
        )

        true_class = (
            gt_classes[
                best_gt_index
            ]
        )


        print(
            "GT class:",
            CLASS_NAMES[
                true_class
            ]
        )


        if predicted_class == true_class:

            print(
                "MATCH: correct box + class"
            )

            true_positives += 1

        else:

            print(
                "Box matched but class WRONG"
            )

            false_positives += 1


        matched_gt.add(
            best_gt_index
        )

    else:

        print(
            "False detection"
        )

        false_positives += 1


false_negatives = (
    len(gt_boxes)
    -
    len(matched_gt)
)


precision = (
    true_positives
    /
    max(
        true_positives
        +
        false_positives,
        1
    )
)

recall = (
    true_positives
    /
    max(
        len(gt_boxes),
        1
    )
)


print(
    "\n=============================="
)

print(
    "FINAL RESULT"
)

print(
    "=============================="
)

print(
    "True positives:",
    true_positives
)

print(
    "False positives:",
    false_positives
)

print(
    "False negatives:",
    false_negatives
)

print(
    f"Precision: {precision:.3f}"
)

print(
    f"Recall: {recall:.3f}"
)