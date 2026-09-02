from pathlib import Path

import torch

from traffic_dataset_v4 import TrafficDatasetV4
from target_generator_v4 import create_multiscale_targets_v4
from model_v4 import TrafficDetectorV4
from loss_v4 import MultiScaleTrafficLossV4


# ==========================================================
# SETTINGS
# ==========================================================

NUM_CLASSES = 15

IMAGE_SIZE = 448

BATCH_SIZE = 2


# ==========================================================
# PATHS
# ==========================================================

BASE_DIR = Path(__file__).parent.parent


# ----------------------------------------------------------
# BMD DATASET
# ----------------------------------------------------------

BMD_IMAGE_DIR = (
    BASE_DIR
    / "dataset"
    / "train"
    / "images"
)

BMD_LABEL_DIR = (
    BASE_DIR
    / "dataset"
    / "train"
    / "labels"
)


# ----------------------------------------------------------
# AMBULANCE DATASET
# ----------------------------------------------------------

AMBULANCE_IMAGE_DIR = (
    BASE_DIR
    / "ambulance_v4"
    / "train"
    / "images"
)

AMBULANCE_LABEL_DIR = (
    BASE_DIR
    / "ambulance_v4"
    / "train"
    / "labels"
)


# ==========================================================
# DEVICE
# ==========================================================

device = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


print(
    "=" * 75
)

print(
    "V4 MIXED BMD + AMBULANCE TRAINING-STEP TEST"
)

print(
    "=" * 75
)

print(
    "Device:",
    device
)


# ==========================================================
# CHECK PATHS
# ==========================================================

assert BMD_IMAGE_DIR.exists(), (
    f"BMD image directory not found:\n"
    f"{BMD_IMAGE_DIR}"
)

assert BMD_LABEL_DIR.exists(), (
    f"BMD label directory not found:\n"
    f"{BMD_LABEL_DIR}"
)

assert AMBULANCE_IMAGE_DIR.exists(), (
    f"Ambulance image directory not found:\n"
    f"{AMBULANCE_IMAGE_DIR}"
)

assert AMBULANCE_LABEL_DIR.exists(), (
    f"Ambulance label directory not found:\n"
    f"{AMBULANCE_LABEL_DIR}"
)


# ==========================================================
# DATASETS
# ==========================================================

bmd_dataset = TrafficDatasetV4(
    BMD_IMAGE_DIR,
    BMD_LABEL_DIR,
    image_size=IMAGE_SIZE,
    augment=True
)


ambulance_dataset = TrafficDatasetV4(
    AMBULANCE_IMAGE_DIR,
    AMBULANCE_LABEL_DIR,
    image_size=IMAGE_SIZE,
    augment=True
)


print(
    "\nBMD dataset size:",
    len(
        bmd_dataset
    )
)

print(
    "Ambulance dataset size:",
    len(
        ambulance_dataset
    )
)


assert len(
    bmd_dataset
) > 0

assert len(
    ambulance_dataset
) > 0


# ==========================================================
# LOAD ONE REAL BMD SAMPLE
# ==========================================================

(
    bmd_image,
    bmd_boxes,
    bmd_categories,
    bmd_supervision
) = bmd_dataset[
    0
]


# ==========================================================
# LOAD ONE REAL AMBULANCE SAMPLE
# ==========================================================

(
    ambulance_image,
    ambulance_boxes,
    ambulance_categories,
    ambulance_supervision
) = ambulance_dataset[
    0
]


# ==========================================================
# BASIC SAMPLE VALIDATION
# ==========================================================

print(
    "\n"
    + "-" * 75
)

print(
    "SOURCE SAMPLES"
)

print(
    "-" * 75
)


print(
    "BMD supervision:",
    bmd_supervision
)

print(
    "BMD objects:",
    len(
        bmd_boxes
    )
)

print(
    "BMD categories:",
    bmd_categories.tolist()
)


print(
    "\nAmbulance supervision:",
    ambulance_supervision
)

print(
    "Ambulance objects:",
    len(
        ambulance_boxes
    )
)

print(
    "Ambulance categories:",
    ambulance_categories.tolist()
)


# ==========================================================
# VERIFY SUPERVISION MODES
# ==========================================================

assert (
    bmd_supervision
    == "full"
), (
    "BMD sample must use "
    "'full' supervision."
)


assert (
    ambulance_supervision
    == "positive_only"
), (
    "Ambulance sample must use "
    "'positive_only' supervision."
)


# ==========================================================
# VERIFY AMBULANCE CLASS
# ==========================================================

ambulance_class_present = (
    ambulance_categories
    == 14
).any().item()


assert ambulance_class_present, (
    "Ambulance sample does not contain "
    "class ID 14."
)


print(
    "\n✅ Dataset supervision modes correct"
)

print(
    "✅ Ambulance class 14 present"
)


# ==========================================================
# BUILD MIXED BATCH
# ==========================================================

samples = [
    (
        bmd_image,
        bmd_boxes,
        bmd_categories,
        bmd_supervision,
        "BMD"
    ),
    (
        ambulance_image,
        ambulance_boxes,
        ambulance_categories,
        ambulance_supervision,
        "AMBULANCE"
    )
]


images = []

small_targets = []
large_targets = []

small_masks = []
large_masks = []


total_original_objects = 0

total_small_objects = 0
total_large_objects = 0

total_small_collisions = 0
total_large_collisions = 0


# ==========================================================
# BUILD TARGETS
# ==========================================================

for (
    image,
    boxes,
    categories,
    supervision,
    source_name
) in samples:

    result = (
        create_multiscale_targets_v4(
            boxes,
            categories,
            supervision=supervision,
            num_classes=NUM_CLASSES,
            image_size=IMAGE_SIZE,
            size_threshold_px=32
        )
    )

    images.append(
        image
    )

    small_targets.append(
        result[
            "small_target"
        ]
    )

    large_targets.append(
        result[
            "large_target"
        ]
    )

    small_masks.append(
        result[
            "small_objectness_mask"
        ]
    )

    large_masks.append(
        result[
            "large_objectness_mask"
        ]
    )


    original_objects = (
        len(
            boxes
        )
    )

    encoded_small = int(
        result[
            "small_target"
        ][0].sum().item()
    )

    encoded_large = int(
        result[
            "large_target"
        ][0].sum().item()
    )


    total_original_objects += (
        original_objects
    )

    total_small_objects += (
        encoded_small
    )

    total_large_objects += (
        encoded_large
    )


    total_small_collisions += (
        result[
            "small_collisions"
        ]
    )

    total_large_collisions += (
        result[
            "large_collisions"
        ]
    )


    print(
        "\n"
        + "-" * 75
    )

    print(
        f"{source_name} TARGET SUMMARY"
    )

    print(
        "-" * 75
    )


    print(
        "Supervision:",
        supervision
    )

    print(
        "Original objects:",
        original_objects
    )

    print(
        "Small encoded:",
        encoded_small
    )

    print(
        "Large encoded:",
        encoded_large
    )

    print(
        "Small supervised cells:",
        int(
            result[
                "small_objectness_mask"
            ].sum().item()
        )
    )

    print(
        "Large supervised cells:",
        int(
            result[
                "large_objectness_mask"
            ].sum().item()
        )
    )


# ==========================================================
# STACK MIXED BATCH
# ==========================================================

images = torch.stack(
    images
).to(
    device
)


small_targets = torch.stack(
    small_targets
).to(
    device
)


large_targets = torch.stack(
    large_targets
).to(
    device
)


small_masks = torch.stack(
    small_masks
).to(
    device
)


large_masks = torch.stack(
    large_masks
).to(
    device
)


targets = {

    "small":
        small_targets,

    "large":
        large_targets
}


objectness_masks = {

    "small":
        small_masks,

    "large":
        large_masks
}


# ==========================================================
# DISPLAY BATCH
# ==========================================================

print(
    "\n"
    + "=" * 75
)

print(
    "MIXED BATCH"
)

print(
    "=" * 75
)


print(
    "Image batch:",
    images.shape
)

print(
    "Small targets:",
    small_targets.shape
)

print(
    "Large targets:",
    large_targets.shape
)

print(
    "Small masks:",
    small_masks.shape
)

print(
    "Large masks:",
    large_masks.shape
)


print(
    "\nOriginal objects:",
    total_original_objects
)

print(
    "Encoded small objects:",
    total_small_objects
)

print(
    "Encoded large objects:",
    total_large_objects
)

print(
    "Small collisions:",
    total_small_collisions
)

print(
    "Large collisions:",
    total_large_collisions
)


# ==========================================================
# VERIFY TARGET SHAPES
# ==========================================================

target_shape_ok = (

    small_targets.shape
    ==
    torch.Size(
        [
            BATCH_SIZE,
            20,
            56,
            56
        ]
    )

    and

    large_targets.shape
    ==
    torch.Size(
        [
            BATCH_SIZE,
            20,
            28,
            28
        ]
    )
)


mask_shape_ok = (

    small_masks.shape
    ==
    torch.Size(
        [
            BATCH_SIZE,
            56,
            56
        ]
    )

    and

    large_masks.shape
    ==
    torch.Size(
        [
            BATCH_SIZE,
            28,
            28
        ]
    )
)


# ==========================================================
# VERIFY PER-SOURCE MASKS
# ==========================================================

# BMD is first sample in batch.
bmd_small_mask_count = int(
    small_masks[
        0
    ].sum().item()
)

bmd_large_mask_count = int(
    large_masks[
        0
    ].sum().item()
)


# Ambulance is second sample.
ambulance_small_mask_count = int(
    small_masks[
        1
    ].sum().item()
)

ambulance_large_mask_count = int(
    large_masks[
        1
    ].sum().item()
)


ambulance_small_positive_count = int(
    small_targets[
        1,
        0
    ].sum().item()
)

ambulance_large_positive_count = int(
    large_targets[
        1,
        0
    ].sum().item()
)


print(
    "\n"
    + "-" * 75
)

print(
    "SUPERVISION MASK VALIDATION"
)

print(
    "-" * 75
)


print(
    "BMD small mask cells:",
    bmd_small_mask_count
)

print(
    "BMD large mask cells:",
    bmd_large_mask_count
)


print(
    "Ambulance small positives:",
    ambulance_small_positive_count
)

print(
    "Ambulance small mask cells:",
    ambulance_small_mask_count
)


print(
    "Ambulance large positives:",
    ambulance_large_positive_count
)

print(
    "Ambulance large mask cells:",
    ambulance_large_mask_count
)


bmd_mask_ok = (

    bmd_small_mask_count
    ==
    56 * 56

    and

    bmd_large_mask_count
    ==
    28 * 28
)


ambulance_mask_ok = (

    ambulance_small_mask_count
    ==
    ambulance_small_positive_count

    and

    ambulance_large_mask_count
    ==
    ambulance_large_positive_count
)


# ==========================================================
# VERIFY CLASS 14 ENCODED
# ==========================================================

AMBULANCE_CLASS_ID = 14

AMBULANCE_CHANNEL = (
    5
    + AMBULANCE_CLASS_ID
)


ambulance_small_class_cells = int(
    small_targets[
        1,
        AMBULANCE_CHANNEL
    ].sum().item()
)


ambulance_large_class_cells = int(
    large_targets[
        1,
        AMBULANCE_CHANNEL
    ].sum().item()
)


ambulance_encoded_count = (
    ambulance_small_class_cells
    +
    ambulance_large_class_cells
)


ambulance_class_ok = (
    ambulance_encoded_count
    > 0
)


print(
    "\nAmbulance class-14 encoded cells:",
    ambulance_encoded_count
)


# ==========================================================
# MODEL
# ==========================================================

model = TrafficDetectorV4(
    num_classes=NUM_CLASSES
).to(
    device
)


model.train()


# ==========================================================
# LOSS
# ==========================================================

criterion = (
    MultiScaleTrafficLossV4(
        num_classes=NUM_CLASSES
    ).to(
        device
    )
)


# ==========================================================
# OPTIMIZER
# ==========================================================

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=1e-3,
    weight_decay=1e-4
)


# ==========================================================
# FORWARD
# ==========================================================

optimizer.zero_grad(
    set_to_none=True
)


predictions = model(
    images
)


print(
    "\n"
    + "=" * 75
)

print(
    "MODEL OUTPUT"
)

print(
    "=" * 75
)


print(
    "Prediction small:",
    predictions[
        "small"
    ].shape
)

print(
    "Prediction large:",
    predictions[
        "large"
    ].shape
)


# ==========================================================
# OUTPUT SHAPE VALIDATION
# ==========================================================

prediction_shape_ok = (

    predictions[
        "small"
    ].shape
    ==
    torch.Size(
        [
            BATCH_SIZE,
            20,
            56,
            56
        ]
    )

    and

    predictions[
        "large"
    ].shape
    ==
    torch.Size(
        [
            BATCH_SIZE,
            20,
            28,
            28
        ]
    )
)


# ==========================================================
# LOSS WITH SUPERVISION MASKS
# ==========================================================

losses = criterion(
    predictions,
    targets,
    objectness_masks=objectness_masks
)


# ==========================================================
# PRINT LOSS
# ==========================================================

print(
    "\n"
    + "-" * 75
)

print(
    "LOSS COMPONENTS"
)

print(
    "-" * 75
)


loss_names = [

    "total",

    "small_total",
    "small_box",
    "small_object",
    "small_no_object",
    "small_class",

    "large_total",
    "large_box",
    "large_object",
    "large_no_object",
    "large_class"
]


for name in loss_names:

    value = (
        losses[
            name
        ]
    )

    print(
        f"{name:24s}: "
        f"{value.detach().item():.6f}"
    )


# ==========================================================
# LOSS SUPERVISION DIAGNOSTICS
# ==========================================================

print(
    "\n"
    + "-" * 75
)

print(
    "LOSS SUPERVISION COUNTS"
)

print(
    "-" * 75
)


count_names = [

    "small_positive_cells",
    "small_negative_cells",
    "small_ignored_cells",

    "large_positive_cells",
    "large_negative_cells",
    "large_ignored_cells"
]


for name in count_names:

    print(
        f"{name:24s}: "
        f"{int(losses[name].item())}"
    )


# ==========================================================
# VALIDATE LOSS
# ==========================================================

loss_finite = (
    torch.isfinite(
        losses[
            "total"
        ]
    ).item()
)


# ==========================================================
# VALIDATE IGNORED CELLS
# ==========================================================

ignored_cells_present = (

    losses[
        "small_ignored_cells"
    ].item()
    > 0

    or

    losses[
        "large_ignored_cells"
    ].item()
    > 0
)


# ==========================================================
# BACKWARD
# ==========================================================

losses[
    "total"
].backward()


# ==========================================================
# CHECK GRADIENTS
# ==========================================================

parameters_with_grad = 0

finite_gradients = True

gradient_norm_squared = 0.0


for parameter in model.parameters():

    if parameter.grad is None:
        continue

    parameters_with_grad += 1

    if not torch.isfinite(
        parameter.grad
    ).all():

        finite_gradients = False

    gradient_norm_squared += (
        parameter.grad
        .detach()
        .float()
        .norm()
        .item()
        ** 2
    )


gradient_norm = (
    gradient_norm_squared
    ** 0.5
)


print(
    "\n"
    + "-" * 75
)

print(
    "GRADIENT CHECK"
)

print(
    "-" * 75
)


print(
    "Parameters with gradients:",
    parameters_with_grad
)

print(
    "Finite gradients:",
    finite_gradients
)

print(
    "Global gradient norm:",
    f"{gradient_norm:.6f}"
)


# ==========================================================
# GRADIENT CLIPPING
# ==========================================================

clipped_norm = (
    torch.nn.utils.clip_grad_norm_(
        model.parameters(),
        max_norm=5.0
    )
)


print(
    "Gradient norm before clipping:",
    f"{float(clipped_norm):.6f}"
)

print(
    "Gradient clip limit:",
    5.0
)


# ==========================================================
# OPTIMIZER STEP
# ==========================================================

optimizer.step()


# ==========================================================
# FINAL VALIDATIONS
# ==========================================================

gradient_ok = (

    parameters_with_grad
    > 0

    and

    finite_gradients
)


optimizer_ok = True


# ==========================================================
# PRINT FINAL RESULTS
# ==========================================================

print(
    "\n"
    + "=" * 75
)

print(
    "FINAL TEST RESULTS"
)

print(
    "=" * 75
)


tests = {

    "BMD full supervision":
        bmd_supervision
        == "full",

    "Ambulance positive-only":
        ambulance_supervision
        == "positive_only",

    "Target shapes":
        target_shape_ok,

    "Mask shapes":
        mask_shape_ok,

    "BMD masks":
        bmd_mask_ok,

    "Ambulance masks":
        ambulance_mask_ok,

    "Ambulance class 14":
        ambulance_class_ok,

    "20-channel model output":
        prediction_shape_ok,

    "Finite loss":
        loss_finite,

    "Ignored ambulance cells":
        ignored_cells_present,

    "Backward gradients":
        gradient_ok,

    "Optimizer step":
        optimizer_ok
}


all_passed = True


for name, passed in tests.items():

    print(
        f"{name:30s}: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    if not passed:

        all_passed = False


# ==========================================================
# FINAL RESULT
# ==========================================================

if all_passed:

    print(
        "\n"
        "✅ V4 MIXED BMD + AMBULANCE "
        "TRAINING STEP PASSED!"
    )

else:

    print(
        "\n"
        "❌ V4 MIXED TRAINING STEP FAILED!"
    )


print(
    "=" * 75
)