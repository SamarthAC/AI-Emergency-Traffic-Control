import torch
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from pathlib import Path
import sys

from model import TrafficCNN


# ==================================================
# SETTINGS
# ==================================================

NUM_CLASSES = 14
GRID_SIZE = 28
IMAGE_SIZE = 448

CONFIDENCE_THRESHOLD = 0.55
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

MODEL_PATH = (
    BASE_DIR
    / "traffic_detector_v3_best.pth"
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
    iou_threshold
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

            # Different classes are not suppressed
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

            # -------------------------------
            # OBJECTNESS
            # -------------------------------

            objectness = torch.sigmoid(
                prediction[
                    0,
                    row,
                    col
                ]
            ).item()


            # -------------------------------
            # CLASS
            # -------------------------------

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


            # -------------------------------
            # CONFIDENCE
            # -------------------------------

            confidence = (
                objectness
                * class_probability
            )


            if (
                confidence
                < CONFIDENCE_THRESHOLD
            ):
                continue


            # -------------------------------
            # BOUNDING BOX
            # -------------------------------

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
                    "class_id":
                        class_id,

                    "confidence":
                        confidence,

                    "box":
                        (
                            x1,
                            y1,
                            x2,
                            y2
                        )
                }
            )


    detections = nms(
        detections,
        NMS_IOU_THRESHOLD
    )

    return detections


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
    "Loaded model:",
    MODEL_PATH
)


# ==================================================
# GET IMAGE PATH
# ==================================================

if len(sys.argv) < 2:

    print(
        "\nUsage:"
    )

    print(
        'python predict_v3_image.py "C:\\path\\to\\image.jpg"'
    )

    sys.exit()


IMAGE_PATH = Path(
    sys.argv[1]
)


if not IMAGE_PATH.exists():

    print(
        "Image not found:",
        IMAGE_PATH
    )

    sys.exit()


# ==================================================
# LOAD ORIGINAL IMAGE
# ==================================================

original_image = Image.open(
    IMAGE_PATH
).convert(
    "RGB"
)


original_width = (
    original_image.width
)

original_height = (
    original_image.height
)


# ==================================================
# PREPROCESS
# ==================================================

resized_image = original_image.resize(
    (
        IMAGE_SIZE,
        IMAGE_SIZE
    )
)


image_array = np.asarray(
    resized_image,
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


# ==================================================
# RUN CNN
# ==================================================

with torch.no_grad():

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


# ==================================================
# DECODE
# ==================================================

detections = decode_predictions(
    prediction
)


print(
    "\n========================================"
)

print(
    "V3 DETECTIONS"
)

print(
    "========================================"
)


if len(detections) == 0:

    print(
        "No vehicles detected."
    )


# ==================================================
# COUNTS
# ==================================================

class_counts = {}


for detection in detections:

    class_id = (
        detection["class_id"]
    )

    class_name = (
        CLASS_NAMES[class_id]
    )

    confidence = (
        detection["confidence"]
    )


    class_counts[
        class_name
    ] = (
        class_counts.get(
            class_name,
            0
        )
        + 1
    )


    print(
        f"{class_name:<20}"
        f" confidence = "
        f"{confidence:.3f}"
    )


print(
    "\n========================================"
)

print(
    "VEHICLE COUNTS"
)

print(
    "========================================"
)


for class_name, count in (
    class_counts.items()
):

    print(
        f"{class_name:<20}: "
        f"{count}"
    )


print(
    "\nTotal detected vehicles:",
    len(detections)
)


# ==================================================
# DRAW DETECTIONS
# ==================================================

draw_image = (
    original_image.copy()
)

draw = ImageDraw.Draw(
    draw_image
)


for detection in detections:

    x1, y1, x2, y2 = (
        detection["box"]
    )


    # Convert normalized box
    # back to original image pixels

    x1 *= original_width
    x2 *= original_width

    y1 *= original_height
    y2 *= original_height


    class_id = (
        detection["class_id"]
    )

    confidence = (
        detection["confidence"]
    )

    class_name = (
        CLASS_NAMES[
            class_id
        ]
    )


    # Draw rectangle

    draw.rectangle(
        (
            x1,
            y1,
            x2,
            y2
        ),
        outline="red",
        width=3
    )


    label = (
        f"{class_name} "
        f"{confidence:.2f}"
    )


    # Label background

    text_box = draw.textbbox(
        (
            x1,
            y1
        ),
        label
    )


    text_width = (
        text_box[2]
        - text_box[0]
    )

    text_height = (
        text_box[3]
        - text_box[1]
    )


    draw.rectangle(
        (
            x1,
            max(
                0,
                y1 - text_height - 6
            ),
            x1 + text_width + 6,
            y1
        ),
        fill="red"
    )


    draw.text(
        (
            x1 + 3,
            max(
                0,
                y1 - text_height - 3
            )
        ),
        label,
        fill="white"
    )


# ==================================================
# SAVE OUTPUT
# ==================================================

OUTPUT_PATH = (
    IMAGE_PATH.parent
    / (
        IMAGE_PATH.stem
        + "_v3_detection.png"
    )
)


draw_image.save(
    OUTPUT_PATH
)


print(
    "\nDetection image saved to:"
)

print(
    OUTPUT_PATH
)

print(
    "\nDone."
)