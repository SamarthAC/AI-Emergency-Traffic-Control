import torch
from pathlib import Path

from traffic_dataset import TrafficDataset
from target_generator import create_target_grid
from model import TrafficCNN
from loss import DetectionLoss


BASE_DIR = Path(__file__).parent.parent

image_dir = BASE_DIR / "dataset" / "train" / "images"
label_dir = BASE_DIR / "dataset" / "train" / "labels"


# Load dataset
dataset = TrafficDataset(
    image_dir,
    label_dir
)

image, boxes, categories = dataset[0]


# Create target
target = create_target_grid(
    boxes,
    categories
)


# Add batch dimensions
image = image.unsqueeze(0)

target = target.unsqueeze(0)


# Create model
model = TrafficCNN(
    num_classes=14
)


# Prediction
prediction = model(image)


print("Prediction:")
print(prediction.shape)

print("Target:")
print(target.shape)


# Create loss
criterion = DetectionLoss()


# Calculate loss
losses = criterion(
    prediction,
    target
)


print("\n===== LOSSES =====")

for name, value in losses.items():

    print(
        f"{name:10s}: "
        f"{value.item():.4f}"
    )