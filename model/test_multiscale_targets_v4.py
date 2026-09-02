import torch

from target_generator_v4 import (
    create_multiscale_targets_v4,
    decode_target_grid_v4,
    box_iou_xywh
)


# ==========================================================
# TEST BOXES
# ==========================================================

# 448x448 image
#
# Box 1:
# 20x20 = 400 px²
# -> SMALL HEAD
#
# Box 2:
# 30x30 = 900 px²
# -> SMALL HEAD
#
# Box 3:
# 40x40 = 1600 px²
# -> LARGE HEAD
#
# Box 4:
# 100x60 = 6000 px²
# -> LARGE HEAD


IMAGE_SIZE = 448


def px(value):
    return value / IMAGE_SIZE


boxes = torch.tensor(
    [
        [
            0.10,
            0.20,
            px(20),
            px(20)
        ],

        [
            0.30,
            0.40,
            px(30),
            px(30)
        ],

        [
            0.50,
            0.50,
            px(40),
            px(40)
        ],

        [
            0.65,
            0.60,
            px(100),
            px(60)
        ]
    ],
    dtype=torch.float32
)


categories = torch.tensor(
    [
        7,
        6,
        0,
        4
    ],
    dtype=torch.long
)


# ==========================================================
# CREATE TARGETS
# ==========================================================

result = create_multiscale_targets_v4(
    boxes,
    categories,
    num_classes=14,
    image_size=448,
    size_threshold_px=32
)


small_target = result[
    "small_target"
]

large_target = result[
    "large_target"
]


print("=" * 65)

print(
    "V4 MULTI-SCALE TARGET TEST"
)

print("=" * 65)


print(
    "\nSmall target shape:",
    small_target.shape
)

print(
    "Large target shape:",
    large_target.shape
)


small_objects = int(
    small_target[0].sum().item()
)

large_objects = int(
    large_target[0].sum().item()
)


print(
    "\nObjects on 56x56 head:",
    small_objects
)

print(
    "Objects on 28x28 head:",
    large_objects
)


print(
    "\nSmall collisions:",
    result["small_collisions"]
)

print(
    "Large collisions:",
    result["large_collisions"]
)


# ==========================================================
# DECODE BOTH HEADS
# ==========================================================

decoded_small = decode_target_grid_v4(
    small_target,
    grid_size=56
)

decoded_large = decode_target_grid_v4(
    large_target,
    grid_size=28
)


print(
    "\nDecoded small objects:"
)

for item in decoded_small:
    print(item)


print(
    "\nDecoded large objects:"
)

for item in decoded_large:
    print(item)


# ==========================================================
# ROUND-TRIP TEST
# ==========================================================

minimum_iou = 1.0


for original_box, category in zip(
    boxes,
    categories
):

    original = (
        original_box.tolist()
    )

    class_id = int(
        category.item()
    )


    pixel_area = (
        original[2]
        * IMAGE_SIZE
        *
        original[3]
        * IMAGE_SIZE
    )


    if pixel_area < 32 ** 2:

        candidates = (
            decoded_small
        )

        expected_head = (
            "56x56"
        )

    else:

        candidates = (
            decoded_large
        )

        expected_head = (
            "28x28"
        )


    matching = [
        item
        for item in candidates
        if item[4] == class_id
    ]


    if not matching:

        print(
            f"\nClass {class_id}: "
            f"NOT FOUND on "
            f"{expected_head}"
        )

        minimum_iou = 0.0
        continue


    best_iou = max(
        box_iou_xywh(
            original,
            candidate[:4]
        )
        for candidate in matching
    )


    minimum_iou = min(
        minimum_iou,
        best_iou
    )


    print(
        f"\nClass {class_id}"
        f" -> {expected_head}"
        f" -> IoU "
        f"{best_iou:.8f}"
    )


# ==========================================================
# FINAL VALIDATION
# ==========================================================

shape_ok = (
    small_target.shape
    ==
    torch.Size(
        [19, 56, 56]
    )
    and
    large_target.shape
    ==
    torch.Size(
        [19, 28, 28]
    )
)


count_ok = (
    small_objects == 2
    and
    large_objects == 2
)


iou_ok = (
    minimum_iou > 0.999
)


print(
    "\n" + "=" * 65
)

print(
    "Shape test:",
    "PASS"
    if shape_ok
    else "FAIL"
)

print(
    "Scale assignment:",
    "PASS"
    if count_ok
    else "FAIL"
)

print(
    "Round-trip IoU:",
    "PASS"
    if iou_ok
    else "FAIL"
)


print(
    "Minimum IoU:",
    f"{minimum_iou:.8f}"
)


if (
    shape_ok
    and
    count_ok
    and
    iou_ok
):

    print(
        "\n✅ V4 MULTI-SCALE TARGET TEST PASSED!"
    )

else:

    print(
        "\n❌ V4 MULTI-SCALE TARGET TEST FAILED!"
    )


print("=" * 65)