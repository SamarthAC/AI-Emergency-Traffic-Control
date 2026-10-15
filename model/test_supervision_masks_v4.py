import torch

from target_generator_v4 import (
    create_multiscale_targets_v4
)


NUM_CLASSES = 15


# ==========================================================
# TEST DATA
# ==========================================================

boxes = torch.tensor(
    [
        # Small object
        [
            0.10,
            0.10,
            0.04,
            0.04
        ],

        # Large ambulance
        [
            0.40,
            0.40,
            0.25,
            0.15
        ]
    ],
    dtype=torch.float32
)


categories = torch.tensor(
    [
        7,
        14
    ],
    dtype=torch.long
)


# ==========================================================
# FULL SUPERVISION TEST
# ==========================================================

print(
    "=" * 65
)

print(
    "FULL SUPERVISION TEST"
)

print(
    "=" * 65
)


full = create_multiscale_targets_v4(
    boxes,
    categories,
    supervision="full",
    num_classes=NUM_CLASSES
)


print(
    "Small target:",
    full["small_target"].shape
)

print(
    "Large target:",
    full["large_target"].shape
)


print(
    "Small mask supervised cells:",
    int(
        full[
            "small_objectness_mask"
        ].sum().item()
    )
)

print(
    "Large mask supervised cells:",
    int(
        full[
            "large_objectness_mask"
        ].sum().item()
    )
)


assert (
    full["small_target"].shape
    == (20, 56, 56)
)

assert (
    full["large_target"].shape
    == (20, 28, 28)
)


assert (
    full[
        "small_objectness_mask"
    ].sum().item()
    == 56 * 56
)


assert (
    full[
        "large_objectness_mask"
    ].sum().item()
    == 28 * 28
)


print(
    "✅ FULL SUPERVISION MASK PASSED"
)


# ==========================================================
# POSITIVE-ONLY TEST
# ==========================================================

print(
    "\n"
    + "=" * 65
)

print(
    "POSITIVE-ONLY SUPERVISION TEST"
)

print(
    "=" * 65
)


positive_only = (
    create_multiscale_targets_v4(
        boxes,
        categories,
        supervision="positive_only",
        num_classes=NUM_CLASSES
    )
)


small_positive_cells = int(
    positive_only[
        "small_target"
    ][0].sum().item()
)


large_positive_cells = int(
    positive_only[
        "large_target"
    ][0].sum().item()
)


small_mask_cells = int(
    positive_only[
        "small_objectness_mask"
    ].sum().item()
)


large_mask_cells = int(
    positive_only[
        "large_objectness_mask"
    ].sum().item()
)


print(
    "Small positive cells:",
    small_positive_cells
)

print(
    "Small supervised cells:",
    small_mask_cells
)


print(
    "Large positive cells:",
    large_positive_cells
)

print(
    "Large supervised cells:",
    large_mask_cells
)


assert (
    small_mask_cells
    == small_positive_cells
)


assert (
    large_mask_cells
    == large_positive_cells
)


# ==========================================================
# VERIFY AMBULANCE CLASS EXISTS
# ==========================================================

large_target = (
    positive_only[
        "large_target"
    ]
)


ambulance_channel = (
    5 + 14
)


ambulance_cells = (
    large_target[
        ambulance_channel
    ].sum().item()
)


print(
    "Ambulance class cells:",
    int(
        ambulance_cells
    )
)


assert (
    ambulance_cells >= 1
)


print(
    "✅ POSITIVE-ONLY MASK PASSED"
)


print(
    "\n"
    + "=" * 65
)

print(
    "✅ V4 SUPERVISION MASK TEST PASSED!"
)

print(
    "=" * 65
)