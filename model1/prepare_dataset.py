from datasets import load_dataset
from pathlib import Path
import json


# ==================================================
# SETTINGS
# ==================================================

TRAIN_LIMIT = 3000
VAL_LIMIT = 500


# ==================================================
# PATHS
# ==================================================

BASE_DIR = Path(__file__).parent.parent

DATASET_DIR = BASE_DIR / "dataset"


# ==================================================
# SAVE SPLIT
# ==================================================

def save_split(split_name, limit):

    print(
        f"\nPreparing {split_name} dataset..."
    )

    image_dir = (
        DATASET_DIR
        / split_name
        / "images"
    )

    label_dir = (
        DATASET_DIR
        / split_name
        / "labels"
    )

    image_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    label_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    # ----------------------------------------------
    # Load BMD-45 using streaming
    # ----------------------------------------------

    dataset = load_dataset(
        "iisc-aim/BMD-45",
        split=split_name,
        streaming=True
    )


    # ----------------------------------------------
    # Save samples
    # ----------------------------------------------

    for index, sample in enumerate(dataset):

        if index >= limit:
            break


        image = sample["image"].convert(
            "RGB"
        )


        image_width, image_height = (
            image.size
        )


        # ------------------------------------------
        # File names
        # ------------------------------------------

        image_name = (
            f"{split_name}_{index:04d}.png"
        )

        label_name = (
            f"{split_name}_{index:04d}.json"
        )


        image_path = (
            image_dir
            / image_name
        )

        label_path = (
            label_dir
            / label_name
        )


        # ------------------------------------------
        # Save image
        # ------------------------------------------

        image.save(
            image_path
        )


        # ------------------------------------------
        # Save annotation
        # ------------------------------------------

        label_data = {

            "image_width":
                image_width,

            "image_height":
                image_height,

            "objects":
                sample["objects"]
        }


        with open(
            label_path,
            "w"
        ) as file:

            json.dump(
                label_data,
                file
            )


        # ------------------------------------------
        # Progress
        # ------------------------------------------

        if (index + 1) % 100 == 0:

            print(
                f"{split_name}: "
                f"{index + 1}/{limit}"
            )


    print(
        f"{split_name} completed!"
    )


# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":

    save_split(
        "train",
        TRAIN_LIMIT
    )

    save_split(
        "val",
        VAL_LIMIT
    )

    print(
        "\nDataset preparation complete!"
    )