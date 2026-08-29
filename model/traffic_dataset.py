import torch
from torch.utils.data import Dataset
from PIL import Image
from pathlib import Path
import json
import numpy as np


class TrafficDataset(Dataset):

    def __init__(self, image_dir, label_dir, image_size=448):

        self.image_dir = Path(image_dir)
        self.label_dir = Path(label_dir)
        self.image_size = image_size

        self.images = sorted(
            self.image_dir.glob("*.png")
        )

    def __len__(self):

        return len(self.images)

    def __getitem__(self, index):

        # ==================================================
        # LOAD IMAGE
        # ==================================================

        image_path = self.images[index]

        image = Image.open(
            image_path
        ).convert("RGB")

        original_width, original_height = (
            image.size
        )


        # ==================================================
        # LOAD ANNOTATION
        # ==================================================

        label_path = (
            self.label_dir
            / f"{image_path.stem}.json"
        )

        with open(
            label_path,
            "r"
        ) as f:

            annotation = json.load(f)


        objects = annotation["objects"]

        boxes = objects["bbox"]
        categories = objects["categories"]


        # ==================================================
        # CLEAN + NORMALIZE BOUNDING BOXES
        # ==================================================

        normalized_boxes = []
        valid_categories = []


        for box, category in zip(
            boxes,
            categories
        ):

            # BMD-45 format:
            # [x, y, width, height]

            x, y, width, height = box


            # ----------------------------------------------
            # Convert xywh → corner coordinates
            # ----------------------------------------------

            x1 = x
            y1 = y

            x2 = x + width
            y2 = y + height


            # ----------------------------------------------
            # Clamp coordinates to image boundaries
            # ----------------------------------------------

            x1 = max(
                0.0,
                min(
                    float(original_width),
                    x1
                )
            )

            y1 = max(
                0.0,
                min(
                    float(original_height),
                    y1
                )
            )

            x2 = max(
                0.0,
                min(
                    float(original_width),
                    x2
                )
            )

            y2 = max(
                0.0,
                min(
                    float(original_height),
                    y2
                )
            )


            # ----------------------------------------------
            # Skip completely invalid boxes
            # ----------------------------------------------

            if x2 <= x1 or y2 <= y1:
                continue


            # ----------------------------------------------
            # Convert corners → xywh again
            # ----------------------------------------------

            clean_x = x1
            clean_y = y1

            clean_width = (
                x2 - x1
            )

            clean_height = (
                y2 - y1
            )


            # ----------------------------------------------
            # Normalize to 0-1
            # ----------------------------------------------

            normalized_x = (
                clean_x
                / original_width
            )

            normalized_y = (
                clean_y
                / original_height
            )

            normalized_width = (
                clean_width
                / original_width
            )

            normalized_height = (
                clean_height
                / original_height
            )


            normalized_boxes.append(
                [
                    normalized_x,
                    normalized_y,
                    normalized_width,
                    normalized_height
                ]
            )


            # IMPORTANT:
            # Only keep category if its box was valid

            valid_categories.append(
                category
            )


        # ==================================================
        # RESIZE IMAGE
        # ==================================================

        image = image.resize(
            (
                self.image_size,
                self.image_size
            )
        )


        # ==================================================
        # IMAGE → NUMPY
        # ==================================================

        image_array = np.asarray(
            image,
            dtype=np.float32
        )


        # Normalize:
        # 0-255 → 0-1

        image_array = (
            image_array
            / 255.0
        )


        # ==================================================
        # NUMPY → PYTORCH
        # ==================================================

        image_tensor = torch.from_numpy(
            image_array
        )


        # HWC → CHW
        #
        # [448,448,3]
        #       ↓
        # [3,448,448]

        image_tensor = image_tensor.permute(
            2,
            0,
            1
        )


        # ==================================================
        # BOXES → TENSOR
        # ==================================================

        if len(normalized_boxes) > 0:

            boxes_tensor = torch.tensor(
                normalized_boxes,
                dtype=torch.float32
            )

        else:

            # Correct shape even when image
            # contains zero valid objects

            boxes_tensor = torch.empty(
                (0, 4),
                dtype=torch.float32
            )


        # ==================================================
        # CATEGORIES → TENSOR
        # ==================================================

        categories_tensor = torch.tensor(
            valid_categories,
            dtype=torch.long
        )


        return (
            image_tensor,
            boxes_tensor,
            categories_tensor
        )


# ==================================================
# TEST DATASET
# ==================================================

if __name__ == "__main__":

    base_dir = (
        Path(__file__)
        .parent
        .parent
    )


    image_dir = (
        base_dir
        / "dataset"
        / "train"
        / "images"
    )

    label_dir = (
        base_dir
        / "dataset"
        / "train"
        / "labels"
    )


    dataset = TrafficDataset(
        image_dir,
        label_dir,
        image_size=448
    )


    print(
        "Dataset size:",
        len(dataset)
    )


    image, boxes, categories = (
        dataset[0]
    )


    print(
        "\nImage tensor shape:"
    )

    print(
        image.shape
    )


    print(
        "\nBounding boxes:"
    )

    print(
        boxes
    )


    print(
        "\nCategories:"
    )

    print(
        categories
    )


    print(
        "\nNumber of boxes:",
        len(boxes)
    )

    print(
        "Number of categories:",
        len(categories)
    )


    # Make sure every box has a category

    assert (
        len(boxes)
        ==
        len(categories)
    )


    # Make sure normalized coordinates
    # are inside 0-1

    if len(boxes) > 0:

        assert torch.all(
            boxes >= 0
        )

        assert torch.all(
            boxes <= 1
        )


    print(
        "\nDataset test passed!"
    )