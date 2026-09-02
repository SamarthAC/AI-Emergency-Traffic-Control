from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np
import random

from traffic_dataset_v4 import TrafficDatasetV4


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

TRAIN_IMAGE_DIR = (
    BASE_DIR
    / "dataset"
    / "train"
    / "images"
)

TRAIN_LABEL_DIR = (
    BASE_DIR
    / "dataset"
    / "train"
    / "labels"
)


dataset = TrafficDatasetV4(
    TRAIN_IMAGE_DIR,
    TRAIN_LABEL_DIR,
    image_size=448,
    augment=False
)


# ==========================================================
# PICK 5 UNIQUE RANDOM IMAGES
# ==========================================================

NUM_TEST_IMAGES = 5

random_indices = random.sample(
    range(len(dataset)),
    NUM_TEST_IMAGES
)


print("\nSelected random images:")
print("-" * 60)


# ==========================================================
# PROCESS EACH IMAGE
# ==========================================================

for test_number, index in enumerate(
    random_indices,
    start=1
):

    print(
        f"\nTest {test_number}"
    )

    print(
        "Dataset index:",
        index
    )

    print(
        "Original file:",
        dataset.image_files[index].name
    )


    image_tensor, boxes, categories = dataset[index]


    # ------------------------------------------------------
    # TENSOR -> IMAGE
    # ------------------------------------------------------

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

    image = Image.fromarray(
        image_array
    )

    draw = ImageDraw.Draw(
        image
    )


    width, height = image.size


    # ------------------------------------------------------
    # DRAW BOXES
    # ------------------------------------------------------

    for box, category in zip(
        boxes,
        categories
    ):

        x, y, w, h = box.tolist()

        x1 = x * width
        y1 = y * height

        x2 = (x + w) * width
        y2 = (y + h) * height


        class_id = int(
            category.item()
        )


        if 0 <= class_id < len(CLASS_NAMES):

            class_name = CLASS_NAMES[
                class_id
            ]

        else:

            class_name = (
                f"Class {class_id}"
            )


        # --------------------------------------------------
        # BOX
        # --------------------------------------------------

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


        # --------------------------------------------------
        # LABEL
        # --------------------------------------------------

        draw.text(
            (
                x1,
                max(
                    0,
                    y1 - 15
                )
            ),
            class_name,
            fill="red"
        )


    # ------------------------------------------------------
    # UNIQUE OUTPUT NAME
    # ------------------------------------------------------

    original_name = (
        dataset.image_files[index].stem
    )


    output_path = (
        BASE_DIR
        / (
            f"letterbox_v4_test_"
            f"{test_number}_"
            f"{original_name}.png"
        )
    )


    image.save(
        output_path
    )


    print(
        "Objects:",
        len(boxes)
    )

    print(
        "Saved:",
        output_path
    )


print("\n" + "=" * 60)

print(
    "✅ 5 RANDOM LETTERBOX TEST IMAGES CREATED!"
)

print("=" * 60)