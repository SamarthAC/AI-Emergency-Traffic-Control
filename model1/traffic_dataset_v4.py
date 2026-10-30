import json
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageEnhance
from torch.utils.data import Dataset


class TrafficDatasetV4(Dataset):

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
        self.augment = augment

        # Support BMD PNG + ambulance JPG/JPEG
        supported_extensions = {
            ".png",
            ".jpg",
            ".jpeg"
        }

        self.image_files = sorted([
            path
            for path in self.image_dir.iterdir()
            if (
                path.is_file()
                and path.suffix.lower()
                in supported_extensions
            )
        ])

    def __len__(self):

        return len(
            self.image_files
        )

    # ======================================================
    # LETTERBOX
    # ======================================================

    def letterbox(
        self,
        image,
        boxes
    ):

        original_width = image.width
        original_height = image.height

        target_size = self.image_size

        scale = min(
            target_size / original_width,
            target_size / original_height
        )

        new_width = int(
            round(
                original_width * scale
            )
        )

        new_height = int(
            round(
                original_height * scale
            )
        )

        resized = image.resize(
            (
                new_width,
                new_height
            ),
            Image.BILINEAR
        )

        pad_x = (
            target_size
            - new_width
        ) // 2

        pad_y = (
            target_size
            - new_height
        ) // 2

        canvas = Image.new(
            "RGB",
            (
                target_size,
                target_size
            ),
            (
                114,
                114,
                114
            )
        )

        canvas.paste(
            resized,
            (
                pad_x,
                pad_y
            )
        )

        updated_boxes = []

        for box in boxes:

            x, y, w, h = box

            # Normalized original coordinates
            # -> original pixel coordinates

            x_px = (
                x * original_width
            )

            y_px = (
                y * original_height
            )

            w_px = (
                w * original_width
            )

            h_px = (
                h * original_height
            )

            # Resize
            x_px *= scale
            y_px *= scale
            w_px *= scale
            h_px *= scale

            # Padding
            x_px += pad_x
            y_px += pad_y

            # Normalize relative to final image
            new_x = (
                x_px / target_size
            )

            new_y = (
                y_px / target_size
            )

            new_w = (
                w_px / target_size
            )

            new_h = (
                h_px / target_size
            )

            updated_boxes.append(
                [
                    new_x,
                    new_y,
                    new_w,
                    new_h
                ]
            )

        return (
            canvas,
            updated_boxes
        )

    # ======================================================
    # AUGMENTATION
    # ======================================================

    def apply_augmentation(
        self,
        image,
        boxes
    ):

        # --------------------------------------------------
        # HORIZONTAL FLIP
        # --------------------------------------------------

        if random.random() < 0.5:

            image = image.transpose(
                Image.FLIP_LEFT_RIGHT
            )

            flipped_boxes = []

            for box in boxes:

                x, y, w, h = box

                new_x = (
                    1.0
                    - x
                    - w
                )

                flipped_boxes.append(
                    [
                        new_x,
                        y,
                        w,
                        h
                    ]
                )

            boxes = flipped_boxes

        # --------------------------------------------------
        # BRIGHTNESS
        # --------------------------------------------------

        if random.random() < 0.5:

            factor = random.uniform(
                0.80,
                1.20
            )

            enhancer = (
                ImageEnhance.Brightness(
                    image
                )
            )

            image = enhancer.enhance(
                factor
            )

        # --------------------------------------------------
        # CONTRAST
        # --------------------------------------------------

        if random.random() < 0.5:

            factor = random.uniform(
                0.80,
                1.20
            )

            enhancer = (
                ImageEnhance.Contrast(
                    image
                )
            )

            image = enhancer.enhance(
                factor
            )

        return (
            image,
            boxes
        )

    # ======================================================
    # READ LABEL FORMAT
    # ======================================================

    def parse_labels(
        self,
        data
    ):

        objects = data.get(
            "objects",
            []
        )

        raw_boxes = []
        raw_classes = []

        # --------------------------------------------------
        # FORMAT 1
        #
        # Existing BMD:
        #
        # "objects": {
        #     "bbox": [...],
        #     "categories": [...]
        # }
        # --------------------------------------------------

        if isinstance(
            objects,
            dict
        ):

            raw_boxes = objects.get(
                "bbox",
                []
            )

            raw_classes = objects.get(
                "categories",
                []
            )

        # --------------------------------------------------
        # FORMAT 2
        #
        # Ambulance:
        #
        # "objects": [
        #     {
        #         "bbox": [...],
        #         "category": 14
        #     }
        # ]
        # --------------------------------------------------

        elif isinstance(
            objects,
            list
        ):

            for obj in objects:

                bbox = obj.get(
                    "bbox"
                )

                category = obj.get(
                    "category"
                )

                if (
                    bbox is None
                    or category is None
                ):
                    continue

                raw_boxes.append(
                    bbox
                )

                raw_classes.append(
                    category
                )

        else:

            raise ValueError(
                "Unsupported objects format."
            )

        return (
            raw_boxes,
            raw_classes
        )

    # ======================================================
    # GET ITEM
    # ======================================================

    def __getitem__(
        self,
        index
    ):

        image_path = (
            self.image_files[index]
        )

        label_path = (
            self.label_dir
            / f"{image_path.stem}.json"
        )

        if not label_path.exists():

            raise FileNotFoundError(
                f"Missing label:\n"
                f"{label_path}"
            )

        # --------------------------------------------------
        # LOAD IMAGE
        # --------------------------------------------------

        image = Image.open(
            image_path
        ).convert(
            "RGB"
        )

        # --------------------------------------------------
        # LOAD JSON
        # --------------------------------------------------

        with open(
            label_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        raw_boxes, raw_classes = (
            self.parse_labels(
                data
            )
        )

        original_width = int(
            data.get(
                "width",
                image.width
            )
        )

        original_height = int(
            data.get(
                "height",
                image.height
            )
        )

        # --------------------------------------------------
        # SUPERVISION TYPE
        # --------------------------------------------------

        supervision = data.get(
            "supervision",
            "full"
        )

        if supervision not in {
            "full",
            "positive_only"
        }:

            raise ValueError(
                f"Unknown supervision type: "
                f"{supervision}"
            )

        # --------------------------------------------------
        # CLEAN BOXES
        # --------------------------------------------------

        boxes = []
        categories = []

        for bbox, category in zip(
            raw_boxes,
            raw_classes
        ):

            if (
                bbox is None
                or len(bbox) != 4
            ):
                continue

            x, y, width, height = bbox

            x = float(x)
            y = float(y)

            width = float(width)
            height = float(height)

            x1 = max(
                0.0,
                min(
                    float(original_width),
                    x
                )
            )

            y1 = max(
                0.0,
                min(
                    float(original_height),
                    y
                )
            )

            x2 = max(
                0.0,
                min(
                    float(original_width),
                    x + width
                )
            )

            y2 = max(
                0.0,
                min(
                    float(original_height),
                    y + height
                )
            )

            if x2 <= x1:
                continue

            if y2 <= y1:
                continue

            width = (
                x2 - x1
            )

            height = (
                y2 - y1
            )

            boxes.append(
                [
                    x1 / original_width,
                    y1 / original_height,
                    width / original_width,
                    height / original_height
                ]
            )

            categories.append(
                int(category)
            )

        # --------------------------------------------------
        # LETTERBOX
        # --------------------------------------------------

        (
            image,
            boxes
        ) = self.letterbox(
            image,
            boxes
        )

        # --------------------------------------------------
        # AUGMENT
        # --------------------------------------------------

        if self.augment:

            (
                image,
                boxes
            ) = self.apply_augmentation(
                image,
                boxes
            )

        # --------------------------------------------------
        # IMAGE -> TENSOR
        # --------------------------------------------------

        image_array = np.asarray(
            image,
            dtype=np.float32
        ) / 255.0

        # copy() avoids negative-stride/read-only numpy issues
        image_array = (
            image_array.copy()
        )

        image_tensor = (
            torch.from_numpy(
                image_array
            )
            .permute(
                2,
                0,
                1
            )
            .contiguous()
        )

        # --------------------------------------------------
        # BOXES -> TENSOR
        # --------------------------------------------------

        if len(boxes) > 0:

            boxes_tensor = torch.tensor(
                boxes,
                dtype=torch.float32
            )

        else:

            boxes_tensor = torch.empty(
                (
                    0,
                    4
                ),
                dtype=torch.float32
            )

        categories_tensor = torch.tensor(
            categories,
            dtype=torch.long
        )

        # --------------------------------------------------
        # RETURN
        # --------------------------------------------------

        return (
            image_tensor,
            boxes_tensor,
            categories_tensor,
            supervision
        )


# ==========================================================
# TEST BOTH DATA SOURCES
# ==========================================================

if __name__ == "__main__":

    BASE_DIR = (
        Path(__file__).parent.parent
    )

    # ======================================================
    # BMD TEST
    # ======================================================

    print(
        "\n"
        + "=" * 65
    )

    print(
        "TESTING BMD DATASET"
    )

    print(
        "=" * 65
    )

    bmd_dataset = TrafficDatasetV4(

        BASE_DIR
        / "dataset"
        / "train"
        / "images",

        BASE_DIR
        / "dataset"
        / "train"
        / "labels",

        image_size=448,

        augment=False
    )

    print(
        "Dataset size:",
        len(bmd_dataset)
    )

    (
        image,
        boxes,
        categories,
        supervision
    ) = bmd_dataset[0]

    print(
        "Image shape:",
        image.shape
    )

    print(
        "Boxes shape:",
        boxes.shape
    )

    print(
        "Categories:",
        categories
    )

    print(
        "Supervision:",
        supervision
    )

    assert (
        supervision == "full"
    )

    assert (
        image.shape
        == (3, 448, 448)
    )

    print(
        "✅ BMD DATASET TEST PASSED"
    )

    # ======================================================
    # AMBULANCE TEST
    # ======================================================

    print(
        "\n"
        + "=" * 65
    )

    print(
        "TESTING AMBULANCE DATASET"
    )

    print(
        "=" * 65
    )

    ambulance_dataset = (
        TrafficDatasetV4(

            BASE_DIR
            / "ambulance_v4"
            / "train"
            / "images",

            BASE_DIR
            / "ambulance_v4"
            / "train"
            / "labels",

            image_size=448,

            augment=False
        )
    )

    print(
        "Dataset size:",
        len(ambulance_dataset)
    )

    (
        image,
        boxes,
        categories,
        supervision
    ) = ambulance_dataset[0]

    print(
        "Image shape:",
        image.shape
    )

    print(
        "Boxes shape:",
        boxes.shape
    )

    print(
        "Categories:",
        categories
    )

    print(
        "Supervision:",
        supervision
    )

    assert (
        supervision
        == "positive_only"
    )

    assert (
        image.shape
        == (3, 448, 448)
    )

    assert (
        len(categories) > 0
    )

    assert torch.all(
        categories == 14
    )

    print(
        "✅ AMBULANCE DATASET TEST PASSED"
    )

    print(
        "\n"
        + "=" * 65
    )

    print(
        "✅ V4 MULTI-SOURCE DATASET TEST PASSED!"
    )

    print(
        "=" * 65
    )