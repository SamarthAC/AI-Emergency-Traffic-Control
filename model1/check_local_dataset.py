from pathlib import Path
import json
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Project directories
BASE_DIR = Path(__file__).parent.parent
IMAGE_DIR = BASE_DIR / "dataset" / "train" / "images"
LABEL_DIR = BASE_DIR / "dataset" / "train" / "labels"

# Pick the first image
image_path = sorted(IMAGE_DIR.glob("*.png"))[0]
label_path = LABEL_DIR / f"{image_path.stem}.json"

print("Image:", image_path)
print("Label:", label_path)

# Load image
image = Image.open(image_path)

# Load annotation
with open(label_path, "r") as f:
    annotation = json.load(f)

objects = annotation["objects"]

print("Image size:", image.size)
print("Number of objects:", len(objects["bbox"]))
print("Categories:", objects["categories"])

# Display image
fig, ax = plt.subplots(figsize=(16, 9))
ax.imshow(image)

# Draw boxes
for i, bbox in enumerate(objects["bbox"]):

    x, y, width, height = bbox

    rect = patches.Rectangle(
        (x, y),
        width,
        height,
        linewidth=2,
        edgecolor="red",
        facecolor="none"
    )

    ax.add_patch(rect)

    category = objects["categories"][i]

    ax.text(
        x,
        y,
        f"Class {category}",
        fontsize=10,
        color="red",
        backgroundcolor="white"
    )

ax.axis("off")
plt.tight_layout()

output_path = BASE_DIR / "dataset_check.png"
plt.savefig(output_path, dpi=150)

print("\nSaved visualization to:")
print(output_path)