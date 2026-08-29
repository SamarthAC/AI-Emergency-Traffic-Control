import torch

from model import TrafficCNN
from loss import TrafficDetectionLoss
from target_generator import create_target_grid


# ==================================================
# SETTINGS
# ==================================================

NUM_CLASSES = 14
GRID_SIZE = 28
IMAGE_SIZE = 448


# ==================================================
# DEVICE
# ==================================================

device = torch.device(
    "cuda" if torch.cuda.is_available()
    else "cpu"
)

print("Using device:", device)


# ==================================================
# MODEL
# ==================================================

model = TrafficCNN(
    num_classes=NUM_CLASSES
).to(device)


# ==================================================
# LOSS
# ==================================================

criterion = TrafficDetectionLoss().to(device)


print("\nClass weights:")

for i, weight in enumerate(
    criterion.class_weights
):

    print(
        f"Class {i:2d}: "
        f"{weight.item():.4f}"
    )


# ==================================================
# FAKE IMAGE
# ==================================================

image = torch.randn(
    2,
    3,
    IMAGE_SIZE,
    IMAGE_SIZE
).to(device)


# ==================================================
# FAKE BOXES + CLASSES
# ==================================================

boxes1 = torch.tensor(
    [
        [0.20, 0.20, 0.10, 0.10],
        [0.60, 0.50, 0.15, 0.20]
    ],
    dtype=torch.float32
)

categories1 = torch.tensor(
    [7, 2],
    dtype=torch.long
)


boxes2 = torch.tensor(
    [
        [0.30, 0.40, 0.20, 0.15]
    ],
    dtype=torch.float32
)

categories2 = torch.tensor(
    [0],
    dtype=torch.long
)


# ==================================================
# CREATE TARGETS
# ==================================================

target1 = create_target_grid(
    boxes1,
    categories1,
    grid_size=GRID_SIZE,
    num_classes=NUM_CLASSES
)

target2 = create_target_grid(
    boxes2,
    categories2,
    grid_size=GRID_SIZE,
    num_classes=NUM_CLASSES
)


targets = torch.stack(
    [
        target1,
        target2
    ]
).to(device)


# ==================================================
# FORWARD
# ==================================================

predictions = model(
    image
)


print(
    "\nPrediction shape:",
    predictions.shape
)

print(
    "Target shape:",
    targets.shape
)


# ==================================================
# LOSS
# ==================================================

total_loss, loss_parts = criterion(
    predictions,
    targets
)


print(
    "\nTotal loss:",
    total_loss.item()
)


print("\nLoss components:")

for name, value in loss_parts.items():

    print(
        f"{name:12s}: "
        f"{value:.4f}"
    )


# ==================================================
# BACKPROP TEST
# ==================================================

total_loss.backward()


print(
    "\nBackward pass successful!"
)


# ==================================================
# CHECK GRADIENTS
# ==================================================

has_gradient = False

for parameter in model.parameters():

    if parameter.grad is not None:

        has_gradient = True
        break


print(
    "Model gradients created:",
    has_gradient
)


if (
    predictions.shape
    == (2, 19, 28, 28)
    and
    targets.shape
    == (2, 19, 28, 28)
    and
    torch.isfinite(total_loss)
    and
    has_gradient
):

    print(
        "\n✅ V2 LOSS TEST PASSED!"
    )

else:

    print(
        "\n❌ V2 LOSS TEST FAILED!"
    )