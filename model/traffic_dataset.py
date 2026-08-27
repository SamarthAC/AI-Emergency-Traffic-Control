import torch
from torch.utils.data import Dataset
from PIL import Image
from pathlib import Path
import json


class TrafficDataset(Dataset):

    def __init__(self, image_dir, label_dir, image_size=224):

        self.image_dir = Path(image_dir)
        self.label_dir = Path(label_dir)
        self.image_size = image_size

        self.images = sorted(self.image_dir.glob("*.png"))

    def __len__(self):
        return len(self.images)

    def __getitem__(self, index):

        # -----------------------------
        # Load image
        # -----------------------------
        image_path = self.images[index]

        image = Image.open(image_path).convert("RGB")

        original_width, original_height = image.size

        # -----------------------------
        # Load annotation
        # -----------------------------
        label_path = self.label_dir / f"{image_path.stem}.json"

        with open(label_path, "r") as f:
            annotation = json.load(f)

        objects = annotation["objects"]

        boxes = objects["bbox"]
        categories = objects["categories"]

        # -----------------------------
        # Resize image
        # -----------------------------
        image = image.resize(
            (self.image_size, self.image_size)
        )

        # -----------------------------
        # Convert bounding boxes
        # -----------------------------
        normalized_boxes = []

        for box in boxes:

            x, y, width, height = box

            # Normalize to 0-1
            x = x / original_width
            y = y / original_height
            width = width / original_width
            height = height / original_height

            normalized_boxes.append(
                [x, y, width, height]
            )

        # -----------------------------
        # Convert to tensors
        # -----------------------------
        image_tensor = torch.tensor(
            list(image.getdata()),
            dtype=torch.float32
        )

        image_tensor = image_tensor.reshape(
            self.image_size,
            self.image_size,
            3
        )

        # Change HWC → CHW
        image_tensor = image_tensor.permute(2, 0, 1)

        # Normalize pixels 0-255 → 0-1
        image_tensor = image_tensor / 255.0

        boxes_tensor = torch.tensor(
            normalized_boxes,
            dtype=torch.float32
        )

        categories_tensor = torch.tensor(
            categories,
            dtype=torch.long
        )

        return image_tensor, boxes_tensor, categories_tensor


# ------------------------------------------------
# TEST THE DATASET
# ------------------------------------------------

if __name__ == "__main__":

    base_dir = Path(__file__).parent.parent

    image_dir = base_dir / "dataset" / "train" / "images"
    label_dir = base_dir / "dataset" / "train" / "labels"

    dataset = TrafficDataset(
        image_dir,
        label_dir
    )

    print("Dataset size:", len(dataset))

    image, boxes, categories = dataset[0]

    print("\nImage tensor shape:")
    print(image.shape)

    print("\nBounding boxes:")
    print(boxes)

    print("\nCategories:")
    print(categories)