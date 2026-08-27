from datasets import load_dataset
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Load dataset in streaming mode
ds = load_dataset(
    "iisc-aim/BMD-45",
    split="train",
    streaming=True
)

# Get one image
sample = next(iter(ds))

image = sample["image"]
objects = sample["objects"]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

ax.imshow(image)

# Draw bounding boxes
for i, bbox in enumerate(objects["bbox"]):
    x, y, width, height = bbox

    rectangle = patches.Rectangle(
        (x, y),
        width,
        height,
        linewidth=2,
        edgecolor="red",
        facecolor="none"
    )

    ax.add_patch(rectangle)

    category = objects["categories"][i]

    ax.text(
        x,
        y - 5,
        f"Category {category}",
        color="red",
        fontsize=12,
        backgroundcolor="white"
    )

ax.axis("off")

plt.tight_layout()

# Save image
plt.savefig("sample_with_boxes.png", dpi=150)

print("Saved as sample_with_boxes.png")
print("Number of vehicles:", len(objects["bbox"]))
print("Categories:", objects["categories"])