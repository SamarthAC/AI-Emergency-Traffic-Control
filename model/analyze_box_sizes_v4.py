from pathlib import Path
import torch

from traffic_dataset_v4 import TrafficDatasetV4


# ==========================================================
# SETTINGS
# ==========================================================

IMAGE_SIZE = 448

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


# ==========================================================
# DATASET
# ==========================================================

dataset = TrafficDatasetV4(
    TRAIN_IMAGE_DIR,
    TRAIN_LABEL_DIR,
    image_size=IMAGE_SIZE,
    augment=False
)


print("=" * 65)
print("V4 BOUNDING BOX SIZE ANALYSIS")
print("=" * 65)

print(
    "Training images:",
    len(dataset)
)


# ==========================================================
# STORAGE
# ==========================================================

areas = []

widths = []

heights = []

total_objects = 0


# ==========================================================
# ANALYZE DATASET
# ==========================================================

for index in range(len(dataset)):

    _, boxes, _ = dataset[index]

    if len(boxes) == 0:
        continue


    for box in boxes:

        _, _, w, h = box.tolist()


        # Normalized area
        area = w * h


        # Pixel dimensions in 448x448 image
        width_px = (
            w * IMAGE_SIZE
        )

        height_px = (
            h * IMAGE_SIZE
        )


        areas.append(
            area
        )

        widths.append(
            width_px
        )

        heights.append(
            height_px
        )


        total_objects += 1


    if (
        (index + 1) % 500 == 0
    ):

        print(
            f"Processed "
            f"{index + 1}/"
            f"{len(dataset)} images..."
        )


# ==========================================================
# TENSORS
# ==========================================================

areas = torch.tensor(
    areas,
    dtype=torch.float32
)

widths = torch.tensor(
    widths,
    dtype=torch.float32
)

heights = torch.tensor(
    heights,
    dtype=torch.float32
)


# Convert normalized area to pixel area
pixel_areas = (
    areas * IMAGE_SIZE * IMAGE_SIZE
)


# ==========================================================
# PERCENTILES
# ==========================================================

percentiles = [
    0.10,
    0.25,
    0.50,
    0.75,
    0.90,
    0.95
]


print("\n" + "=" * 65)
print("OBJECT STATISTICS")
print("=" * 65)

print(
    "Total valid objects:",
    total_objects
)


print("\nWIDTH (pixels)")
print("-" * 40)

for p in percentiles:

    value = torch.quantile(
        widths,
        p
    ).item()

    print(
        f"{int(p * 100):>3}% : "
        f"{value:8.2f}px"
    )


print("\nHEIGHT (pixels)")
print("-" * 40)

for p in percentiles:

    value = torch.quantile(
        heights,
        p
    ).item()

    print(
        f"{int(p * 100):>3}% : "
        f"{value:8.2f}px"
    )


print("\nAREA (pixels²)")
print("-" * 40)

for p in percentiles:

    value = torch.quantile(
        pixel_areas,
        p
    ).item()

    print(
        f"{int(p * 100):>3}% : "
        f"{value:10.2f}px²"
    )


# ==========================================================
# SIZE GROUPS
# ==========================================================
#
# These are only diagnostic buckets.
# We are NOT yet using these as the final head assignment.
#
# Small  : area < 32²
# Medium : 32² <= area < 96²
# Large  : area >= 96²
#
# ==========================================================

small_limit = 32 ** 2
large_limit = 96 ** 2


small_count = (
    pixel_areas < small_limit
).sum().item()


medium_count = (
    (
        pixel_areas >= small_limit
    )
    &
    (
        pixel_areas < large_limit
    )
).sum().item()


large_count = (
    pixel_areas >= large_limit
).sum().item()


print("\n" + "=" * 65)
print("DIAGNOSTIC SIZE GROUPS")
print("=" * 65)


print(
    f"Small  (<32²):       "
    f"{small_count:6d} "
    f"({small_count / total_objects * 100:.2f}%)"
)

print(
    f"Medium (32²–96²):    "
    f"{medium_count:6d} "
    f"({medium_count / total_objects * 100:.2f}%)"
)

print(
    f"Large  (>=96²):      "
    f"{large_count:6d} "
    f"({large_count / total_objects * 100:.2f}%)"
)


# ==========================================================
# POSSIBLE TWO-HEAD SPLITS
# ==========================================================

candidate_thresholds = [
    24,
    32,
    40,
    48,
    56,
    64,
    72,
    80,
    96
]


print("\n" + "=" * 65)
print("CANDIDATE TWO-HEAD AREA SPLITS")
print("=" * 65)

print(
    "Threshold means:"
)

print(
    "object area < threshold² -> 56x56 head"
)

print(
    "object area >= threshold² -> 28x28 head"
)

print()


for threshold in candidate_thresholds:

    threshold_area = (
        threshold ** 2
    )


    small_head = (
        pixel_areas
        < threshold_area
    ).sum().item()


    large_head = (
        pixel_areas
        >= threshold_area
    ).sum().item()


    small_percentage = (
        small_head
        / total_objects
        * 100
    )


    large_percentage = (
        large_head
        / total_objects
        * 100
    )


    print(
        f"{threshold:>3}px threshold : "
        f"56x56 = "
        f"{small_head:6d} "
        f"({small_percentage:6.2f}%)"
        f" | "
        f"28x28 = "
        f"{large_head:6d} "
        f"({large_percentage:6.2f}%)"
    )


print("\n" + "=" * 65)

print(
    "✅ V4 BOX SIZE ANALYSIS COMPLETE!"
)

print("=" * 65)