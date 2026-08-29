from pathlib import Path
from PIL import ImageDraw
import numpy as np

from traffic_dataset import TrafficDataset


# ==================================================
# PATHS
# ==================================================

base_dir = (
    Path(__file__)
    .parent
    .parent
)

image_dir = (
    base_dir
    / "dataset"
    / "train"
    / "images"
)

label_dir = (
    base_dir
    / "dataset"
    / "train"
    / "labels"
)


# ==================================================
# DATASET WITH AUGMENTATION
# ==================================================

dataset = TrafficDataset(
    image_dir,
    label_dir,
    image_size=448,
    augment=True
)


# ==================================================
# GET SAMPLE
# ==================================================

image_tensor, boxes, categories = dataset[0]


# CHW -> HWC
image_array = (
    image_tensor
    .permute(1, 2, 0)
    .numpy()
)

image_array = (
    image_array * 255
).clip(
    0,
    255
).astype(
    np.uint8
)


# ==================================================
# NUMPY -> PIL
# ==================================================

from PIL import Image

image = Image.fromarray(
    image_array
)

draw = ImageDraw.Draw(
    image
)


# ==================================================
# DRAW BOUNDING BOXES
# ==================================================

image_width, image_height = (
    image.size
)


for box, category in zip(
    boxes,
    categories
):

    x, y, width, height = (
        box.tolist()
    )

    # normalized -> pixel coordinates

    x1 = (
        x
        * image_width
    )

    y1 = (
        y
        * image_height
    )

    x2 = (
        (x + width)
        * image_width
    )

    y2 = (
        (y + height)
        * image_height
    )


    draw.rectangle(
        [
            x1,
            y1,
            x2,
            y2
        ],
        outline="red",
        width=2
    )


    draw.text(
        (
            x1,
            max(
                0,
                y1 - 12
            )
        ),
        str(
            int(category)
        ),
        fill="red"
    )


# ==================================================
# SAVE RESULT
# ==================================================

output_path = (
    base_dir
    / "augmentation_test.png"
)

image.save(
    output_path
)


print(
    "Saved augmented image:"
)

print(
    output_path
)

print(
    "Objects:",
    len(boxes)
)

print(
    "\nOpen augmentation_test.png and verify:"
)

print(
    "1. Boxes are positioned over vehicles."
)

print(
    "2. No boxes appear on empty areas."
)

print(
    "3. Boxes are not mirrored incorrectly."
)

print(
    "4. Boxes stay inside the image."
)