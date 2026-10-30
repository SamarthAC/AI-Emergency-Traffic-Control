import torch
from pathlib import Path

from traffic_dataset import TrafficDataset
from model import TrafficCNN


# -----------------------------------------
# Paths
# -----------------------------------------

BASE_DIR = Path(__file__).parent.parent

image_dir = BASE_DIR / "dataset" / "train" / "images"
label_dir = BASE_DIR / "dataset" / "train" / "labels"


# -----------------------------------------
# Load dataset
# -----------------------------------------

dataset = TrafficDataset(
    image_dir,
    label_dir
)

print("Dataset size:", len(dataset))


# -----------------------------------------
# Get one real image
# -----------------------------------------

image, boxes, categories = dataset[0]

print("\nOriginal image tensor:")
print(image.shape)

print("\nBounding boxes:")
print(boxes.shape)

print("\nCategories:")
print(categories)


# -----------------------------------------
# Add batch dimension
# -----------------------------------------

image = image.unsqueeze(0)

print("\nImage after adding batch:")
print(image.shape)


# -----------------------------------------
# Create CNN
# -----------------------------------------

model = TrafficCNN(num_classes=14)


# -----------------------------------------
# Run image through CNN
# -----------------------------------------

with torch.no_grad():

    prediction = model(image)


# -----------------------------------------
# Display output
# -----------------------------------------

print("\nCNN prediction shape:")
print(prediction.shape)