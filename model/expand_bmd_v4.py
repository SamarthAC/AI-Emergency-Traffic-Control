from pathlib import Path
import json
import shutil
from io import BytesIO

from PIL import Image
from datasets import load_dataset


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_ROOT = BASE_DIR / "dataset_v4"

TRAIN_LIMIT = 12_000
VAL_LIMIT = 2_000

DATASET_NAME = "iisc-aim/BMD-45"


# ============================================================
# HELPERS
# ============================================================

def prepare_directories(split_name):
    split_root = OUTPUT_ROOT / split_name

    images_dir = split_root / "images"
    labels_dir = split_root / "labels"

    images_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    labels_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    return images_dir, labels_dir


def get_image(sample):
    """
    Handles common Hugging Face Image representations.
    """

    image = sample.get("image")

    if image is None:
        raise ValueError(
            "Sample does not contain 'image'."
        )

    if isinstance(image, Image.Image):
        return image.convert("RGB")

    if isinstance(image, dict):

        if image.get("bytes") is not None:
            return Image.open(
                BytesIO(image["bytes"])
            ).convert("RGB")

        if image.get("path") is not None:
            return Image.open(
                image["path"]
            ).convert("RGB")

    raise TypeError(
        f"Unsupported image type: {type(image)}"
    )


def extract_objects(sample):
    """
    Extracts BMD bounding boxes and categories.

    Output format:
        boxes      -> [[x, y, w, h], ...]
        categories -> [class_id, ...]
    """

    objects = sample.get(
        "objects",
        {}
    )

    if not isinstance(objects, dict):
        raise ValueError(
            "Expected BMD 'objects' to be a dictionary."
        )

    boxes = objects.get(
        "bbox",
        []
    )

    # BMD/HF versions may expose either spelling.
    categories = objects.get(
        "categories",
        objects.get(
            "category",
            []
        )
    )

    if len(boxes) != len(categories):
        raise ValueError(
            "bbox/category length mismatch: "
            f"{len(boxes)} vs {len(categories)}"
        )

    return boxes, categories


def clean_objects(
    boxes,
    categories,
    image_width,
    image_height
):
    """
    Clamp boxes to image boundaries and remove invalid boxes.
    """

    clean_boxes = []
    clean_categories = []

    invalid_boxes = 0

    for bbox, category in zip(
        boxes,
        categories
    ):

        if bbox is None or len(bbox) != 4:
            invalid_boxes += 1
            continue

        try:
            x, y, w, h = map(
                float,
                bbox
            )

            category = int(
                category
            )

        except (TypeError, ValueError):
            invalid_boxes += 1
            continue

        # BMD traffic classes are 0-13.
        if not 0 <= category <= 13:
            continue

        x1 = max(
            0.0,
            min(x, float(image_width))
        )

        y1 = max(
            0.0,
            min(y, float(image_height))
        )

        x2 = max(
            0.0,
            min(
                x + w,
                float(image_width)
            )
        )

        y2 = max(
            0.0,
            min(
                y + h,
                float(image_height)
            )
        )

        new_w = x2 - x1
        new_h = y2 - y1

        if new_w <= 0 or new_h <= 0:
            invalid_boxes += 1
            continue

        clean_boxes.append([
            x1,
            y1,
            new_w,
            new_h
        ])

        clean_categories.append(
            category
        )

    return (
        clean_boxes,
        clean_categories,
        invalid_boxes
    )


# ============================================================
# EXPORT SPLIT
# ============================================================

def export_split(
    hf_split,
    output_split,
    limit
):

    print()
    print("=" * 80)
    print(
        f"EXPORTING {hf_split.upper()} "
        f"-> {output_split.upper()}"
    )
    print("=" * 80)

    images_dir, labels_dir = (
        prepare_directories(
            output_split
        )
    )

    print(
        f"Loading official '{hf_split}' "
        f"split in streaming mode..."
    )

    dataset = load_dataset(
        DATASET_NAME,
        split=hf_split,
        streaming=True
    )

    saved_images = 0
    saved_objects = 0
    invalid_boxes_total = 0
    empty_images = 0
    skipped_samples = 0

    for sample_index, sample in enumerate(
        dataset
    ):

        if saved_images >= limit:
            break

        try:
            image = get_image(
                sample
            )

            width, height = image.size

            boxes, categories = (
                extract_objects(
                    sample
                )
            )

            (
                boxes,
                categories,
                invalid_boxes
            ) = clean_objects(
                boxes,
                categories,
                width,
                height
            )

            invalid_boxes_total += (
                invalid_boxes
            )

            if len(boxes) == 0:
                empty_images += 1

            filename = (
                f"{output_split}_"
                f"{saved_images:05d}.png"
            )

            label_filename = (
                f"{output_split}_"
                f"{saved_images:05d}.json"
            )

            image_path = (
                images_dir
                / filename
            )

            label_path = (
                labels_dir
                / label_filename
            )

            image.save(
                image_path,
                format="PNG"
            )

            label_data = {
                "image_width": width,
                "image_height": height,

                "objects": {
                    "bbox": boxes,
                    "categories": categories
                },

                # BMD supplies normal/full
                # background supervision.
                "supervision": "full"
            }

            with open(
                label_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    label_data,
                    f,
                    indent=2
                )

            saved_images += 1
            saved_objects += len(
                boxes
            )

            if (
                saved_images % 500
                == 0
            ):
                print(
                    f"{output_split}: "
                    f"{saved_images}/{limit} "
                    f"images saved | "
                    f"objects={saved_objects}"
                )

        except Exception as exc:

            skipped_samples += 1

            print(
                f"⚠️ Skipping source sample "
                f"{sample_index}: {exc}"
            )

    print()
    print(
        f"{output_split.upper()} COMPLETE"
    )

    print(
        f"Images saved       : "
        f"{saved_images}"
    )

    print(
        f"Objects saved      : "
        f"{saved_objects}"
    )

    print(
        f"Invalid boxes      : "
        f"{invalid_boxes_total}"
    )

    print(
        f"Empty images       : "
        f"{empty_images}"
    )

    print(
        f"Skipped samples    : "
        f"{skipped_samples}"
    )

    if saved_images != limit:
        raise RuntimeError(
            f"Expected {limit} images "
            f"but saved {saved_images}."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("BMD-45 V4 DATASET EXPANSION")
    print("=" * 80)

    print(
        f"Output: {OUTPUT_ROOT}"
    )

    print(
        f"Train target: {TRAIN_LIMIT}"
    )

    print(
        f"Val target  : {VAL_LIMIT}"
    )

    # --------------------------------------------------------
    # Safety:
    # remove ONLY dataset_v4.
    #
    # Existing dataset/ containing the known-good
    # 3000/500 subset is NOT touched.
    # --------------------------------------------------------

    if OUTPUT_ROOT.exists():

        print()
        print(
            "Removing previous dataset_v4..."
        )

        shutil.rmtree(
            OUTPUT_ROOT
        )

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True
    )

    # Official BMD train split
    export_split(
        hf_split="train",
        output_split="train",
        limit=TRAIN_LIMIT
    )

    # Official BMD validation split
    export_split(
        hf_split="val",
        output_split="val",
        limit=VAL_LIMIT
    )

    print()
    print("=" * 80)
    print("✅ BMD V4 EXPANSION COMPLETE")
    print("=" * 80)

    print(
        "Created:"
    )

    print(
        OUTPUT_ROOT
        / "train"
        / "images"
    )

    print(
        OUTPUT_ROOT
        / "train"
        / "labels"
    )

    print(
        OUTPUT_ROOT
        / "val"
        / "images"
    )

    print(
        OUTPUT_ROOT
        / "val"
        / "labels"
    )

    print()
    print(
        "Original dataset/ was NOT modified."
    )


if __name__ == "__main__":
    main()