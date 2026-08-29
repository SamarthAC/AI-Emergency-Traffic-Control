import torch
from torch.utils.data import Dataset
from PIL import Image, ImageEnhance
from pathlib import Path
import json
import numpy as np
import random


class TrafficDataset(Dataset):

    def __init__(
        self,
        image_dir,
        label_dir,
        image_size=448,
        augment=False
    ):

        self.image_dir = Path(image_dir)
        self.label_dir = Path(label_dir)
        self.image_size = image_size

        # IMPORTANT:
        # True only for training dataset
        self.augment = augment

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

            # BMD-45:
            # [x, y, width, height]

            x, y, width, height = box


            # ----------------------------------------------
            # xywh -> corners
            # ----------------------------------------------

            x1 = x
            y1 = y

            x2 = x + width
            y2 = y + height


            # ----------------------------------------------
            # Clamp
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
            # Reject invalid boxes
            # ----------------------------------------------

            if (
                x2 <= x1
                or
                y2 <= y1
            ):
                continue


            # ----------------------------------------------
            # Clean xywh
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
            # Normalize 0-1
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


            valid_categories.append(
                category
            )


        # ==================================================
        # V3 DATA AUGMENTATION
        #
        # TRAINING ONLY
        # ==================================================

        if self.augment:

            # ==============================================
            # 1. HORIZONTAL FLIP
            # ==============================================

            if random.random() < 0.50:

                image = image.transpose(
                    Image.Transpose.FLIP_LEFT_RIGHT
                )


                # Boxes are normalized xywh:
                #
                # old:
                # x ----------->
                #
                # After horizontal flip:
                #
                # new_x = 1 - x - width

                for box in normalized_boxes:

                    old_x = box[0]
                    width = box[2]

                    new_x = (
                        1.0
                        - old_x
                        - width
                    )

                    box[0] = new_x


            # ==============================================
            # 2. BRIGHTNESS AUGMENTATION
            # ==============================================

            if random.random() < 0.50:

                brightness_factor = (
                    random.uniform(
                        0.80,
                        1.20
                    )
                )

                enhancer = (
                    ImageEnhance.Brightness(
                        image
                    )
                )

                image = enhancer.enhance(
                    brightness_factor
                )


            # ==============================================
            # 3. CONTRAST AUGMENTATION
            # ==============================================

            if random.random() < 0.50:

                contrast_factor = (
                    random.uniform(
                        0.80,
                        1.20
                    )
                )

                enhancer = (
                    ImageEnhance.Contrast(
                        image
                    )
                )

                image = enhancer.enhance(
                    contrast_factor
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
        # IMAGE -> NUMPY
        # ==================================================

        image_array = np.asarray(
            image,
            dtype=np.float32
        )


        image_array = (
            image_array
            / 255.0
        )


        # ==================================================
        # NUMPY -> PYTORCH
        # ==================================================

        image_tensor = torch.from_numpy(
            image_array
        )


        # HWC -> CHW

        image_tensor = (
            image_tensor.permute(
                2,
                0,
                1
            )
        )


        # ==================================================
        # BOXES -> TENSOR
        # ==================================================

        if len(normalized_boxes) > 0:

            boxes_tensor = torch.tensor(
                normalized_boxes,
                dtype=torch.float32
            )

        else:

            boxes_tensor = torch.empty(
                (0, 4),
                dtype=torch.float32
            )


        # ==================================================
        # CATEGORIES -> TENSOR
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


    # Enable augmentation here so
    # we're testing the V3 training path.

    dataset = TrafficDataset(
        image_dir,
        label_dir,
        image_size=448,
        augment=True
    )


    print(
        "Dataset size:",
        len(dataset)
    )


    # Test several samples instead of only one.
    # This increases the chance that random
    # augmentation paths are exercised.

    for index in range(
        min(10, len(dataset))
    ):

        image, boxes, categories = (
            dataset[index]
        )


        assert (
            image.shape
            ==
            (
                3,
                448,
                448
            )
        )


        assert (
            len(boxes)
            ==
            len(categories)
        )


        if len(boxes) > 0:

            assert torch.all(
                boxes >= 0
            )

            assert torch.all(
                boxes <= 1
            )


    print(
        "\nV3 dataset augmentation test passed!"
    )