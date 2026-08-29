from pathlib import Path
from collections import Counter

from traffic_dataset import TrafficDataset


GRID_SIZE = 28

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


# IMPORTANT:
# No augmentation here.
# We want to measure the original dataset.
dataset = TrafficDataset(
    TRAIN_IMAGE_DIR,
    TRAIN_LABEL_DIR,
    image_size=448,
    augment=False
)


total_objects = 0
total_occupied_cells = 0
total_collisions = 0

images_with_collisions = 0

max_collisions_in_image = 0
max_collision_image = None

collision_counts = Counter()


for index in range(len(dataset)):

    _, boxes, _ = dataset[index]

    occupied_cells = set()

    image_collisions = 0


    for box in boxes:

        x, y, width, height = box.tolist()

        center_x = x + width / 2
        center_y = y + height / 2


        center_x = max(
            0.0,
            min(
                center_x,
                1.0 - 1e-6
            )
        )

        center_y = max(
            0.0,
            min(
                center_y,
                1.0 - 1e-6
            )
        )


        grid_x = int(
            center_x * GRID_SIZE
        )

        grid_y = int(
            center_y * GRID_SIZE
        )


        cell = (
            grid_x,
            grid_y
        )


        total_objects += 1


        if cell in occupied_cells:

            total_collisions += 1
            image_collisions += 1

        else:

            occupied_cells.add(
                cell
            )


    total_occupied_cells += len(
        occupied_cells
    )


    if image_collisions > 0:

        images_with_collisions += 1


    collision_counts[
        image_collisions
    ] += 1


    if (
        image_collisions
        >
        max_collisions_in_image
    ):

        max_collisions_in_image = (
            image_collisions
        )

        max_collision_image = (
            dataset.images[index].name
        )


# ==================================================
# RESULTS
# ==================================================

collision_percentage = (
    (
        total_collisions
        /
        total_objects
        *
        100
    )
    if total_objects > 0
    else 0
)


images_collision_percentage = (
    (
        images_with_collisions
        /
        len(dataset)
        *
        100
    )
    if len(dataset) > 0
    else 0
)


print(
    "\n========================================"
)

print(
    "      GRID COLLISION ANALYSIS"
)

print(
    "========================================"
)


print(
    "\nGrid size:",
    f"{GRID_SIZE}x{GRID_SIZE}"
)

print(
    "Images:",
    len(dataset)
)

print(
    "Total objects:",
    total_objects
)

print(
    "Occupied target cells:",
    total_occupied_cells
)

print(
    "Colliding objects:",
    total_collisions
)


print(
    "\nObject collision rate:",
    f"{collision_percentage:.2f}%"
)


print(
    "Images containing collisions:",
    images_with_collisions
)

print(
    "Images with collision rate:",
    f"{images_collision_percentage:.2f}%"
)


print(
    "\nMaximum collisions in one image:",
    max_collisions_in_image
)

print(
    "Image with maximum collisions:",
    max_collision_image
)


print(
    "\nCollision distribution:"
)


for collisions in sorted(
    collision_counts
):

    print(
        f"{collisions:2d} collisions : "
        f"{collision_counts[collisions]} images"
    )


print(
    "\n========================================"
)

print(
    "Analysis complete."
)

print(
    "========================================"
)