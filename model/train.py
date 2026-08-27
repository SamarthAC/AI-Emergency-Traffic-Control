import torch
from torch.utils.data import DataLoader
from pathlib import Path

from traffic_dataset import TrafficDataset
from target_generator import create_target_grid
from model import TrafficCNN
from loss import DetectionLoss


# ==================================================
# SETTINGS
# ==================================================

EPOCHS = 1
BATCH_SIZE = 4
LEARNING_RATE = 0.001
NUM_CLASSES = 14
GRID_SIZE = 28


# ==================================================
# PATHS
# ==================================================

BASE_DIR = Path(__file__).parent.parent

TRAIN_IMAGE_DIR = BASE_DIR / "dataset" / "train" / "images"
TRAIN_LABEL_DIR = BASE_DIR / "dataset" / "train" / "labels"

VAL_IMAGE_DIR = BASE_DIR / "dataset" / "val" / "images"
VAL_LABEL_DIR = BASE_DIR / "dataset" / "val" / "labels"


# ==================================================
# COLLATE FUNCTION
# ==================================================

def collate_fn(batch):

    images = []
    targets = []

    for image, boxes, categories in batch:

        target = create_target_grid(
            boxes,
            categories,
            grid_size=GRID_SIZE,
            num_classes=NUM_CLASSES
        )

        images.append(image)
        targets.append(target)

    images = torch.stack(images)
    targets = torch.stack(targets)

    return images, targets


# ==================================================
# DATASETS
# ==================================================

train_dataset = TrafficDataset(
    TRAIN_IMAGE_DIR,
    TRAIN_LABEL_DIR
)

val_dataset = TrafficDataset(
    VAL_IMAGE_DIR,
    VAL_LABEL_DIR
)


train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    collate_fn=collate_fn
)

val_loader = DataLoader(
    val_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    collate_fn=collate_fn
)


# ==================================================
# DEVICE
# ==================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Using device:", device)


# ==================================================
# MODEL
# ==================================================

model = TrafficCNN(
    num_classes=NUM_CLASSES
).to(device)


criterion = DetectionLoss()

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE
)


# ==================================================
# TRAINING
# ==================================================

for epoch in range(EPOCHS):

    model.train()

    training_loss = 0.0

    for batch_number, (images, targets) in enumerate(train_loader):

        images = images.to(device)
        targets = targets.to(device)

        # Remove old gradients
        optimizer.zero_grad()

        # Forward pass
        predictions = model(images)

        # Calculate loss
        losses = criterion(
            predictions,
            targets
        )

        loss = losses["total"]

        # Backpropagation
        loss.backward()

        # Update CNN weights
        optimizer.step()

        training_loss += loss.item()

        if (batch_number + 1) % 20 == 0:

            print(
                f"Epoch {epoch + 1}/{EPOCHS} | "
                f"Batch {batch_number + 1}/{len(train_loader)} | "
                f"Loss: {loss.item():.4f}"
            )

    training_loss /= len(train_loader)


    # ==================================================
    # VALIDATION
    # ==================================================

    model.eval()

    validation_loss = 0.0

    with torch.no_grad():

        for images, targets in val_loader:

            images = images.to(device)
            targets = targets.to(device)

            predictions = model(images)

            losses = criterion(
                predictions,
                targets
            )

            validation_loss += losses["total"].item()


    validation_loss /= len(val_loader)


    print("\n---------------------------------------")

    print(
        f"Epoch {epoch + 1}/{EPOCHS}"
    )

    print(
        f"Training Loss   : {training_loss:.4f}"
    )

    print(
        f"Validation Loss : {validation_loss:.4f}"
    )

    print("---------------------------------------\n")


# ==================================================
# SAVE MODEL
# ==================================================

MODEL_PATH = BASE_DIR / "traffic_detector.pth"

torch.save(
    model.state_dict(),
    MODEL_PATH
)

print("Training complete!")

print(
    "Model saved to:",
    MODEL_PATH
)