from datasets import load_dataset
from pathlib import Path
import json

# -----------------------------
# SETTINGS
# -----------------------------
TRAIN_IMAGES = 400
VAL_IMAGES = 100

BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR / "dataset"

# -----------------------------
# CREATE FOLDERS
# -----------------------------
train_images_dir = DATASET_DIR / "train" / "images"
train_labels_dir = DATASET_DIR / "train" / "labels"

val_images_dir = DATASET_DIR / "val" / "images"
val_labels_dir = DATASET_DIR / "val" / "labels"

for directory in [
    train_images_dir,
    train_labels_dir,
    val_images_dir,
    val_labels_dir
]:
    directory.mkdir(parents=True, exist_ok=True)

# -----------------------------
# LOAD DATASET
# -----------------------------
print("Connecting to BMD-45...")

train_ds = load_dataset(
    "iisc-aim/BMD-45",
    split="train",
    streaming=True
)

val_ds = load_dataset(
    "iisc-aim/BMD-45",
    split="val",
    streaming=True
)

# -----------------------------
# SAVE TRAINING DATA
# -----------------------------
print("\nSaving training images...")

for i, sample in enumerate(train_ds):

    image = sample["image"]
    objects = sample["objects"]

    image_path = train_images_dir / f"train_{i:04d}.png"
    label_path = train_labels_dir / f"train_{i:04d}.json"

    image.save(image_path)

    annotation = {
        "image_width": image.width,
        "image_height": image.height,
        "objects": objects
    }

    with open(label_path, "w") as f:
        json.dump(annotation, f)

    if (i + 1) % 25 == 0:
        print(f"Training: {i + 1}/{TRAIN_IMAGES}")

    if i + 1 >= TRAIN_IMAGES:
        break

# -----------------------------
# SAVE VALIDATION DATA
# -----------------------------
print("\nSaving validation images...")

for i, sample in enumerate(val_ds):

    image = sample["image"]
    objects = sample["objects"]

    image_path = val_images_dir / f"val_{i:04d}.png"
    label_path = val_labels_dir / f"val_{i:04d}.json"

    image.save(image_path)

    annotation = {
        "image_width": image.width,
        "image_height": image.height,
        "objects": objects
    }

    with open(label_path, "w") as f:
        json.dump(annotation, f)

    if (i + 1) % 25 == 0:
        print(f"Validation: {i + 1}/{VAL_IMAGES}")

    if i + 1 >= VAL_IMAGES:
        break

print("\n==============================")
print("DATASET PREPARATION COMPLETE")
print("==============================")

print(f"Training images: {TRAIN_IMAGES}")
print(f"Validation images: {VAL_IMAGES}")
print(f"Dataset location: {DATASET_DIR}")