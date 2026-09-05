from pathlib import Path
import json


BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR / "dataset_v4"


CLASS_NAMES = [
    "Hatchback",
    "Sedan",
    "SUV",
    "MUV",
    "Bus",
    "Truck",
    "Three-wheeler",
    "Two-wheeler",
    "LCV",
    "Mini-bus",
    "Tempo-traveller",
    "Bicycle",
    "Van",
    "Other"
]


def verify_split(split_name):

    image_dir = DATASET_DIR / split_name / "images"
    label_dir = DATASET_DIR / split_name / "labels"

    image_files = sorted(image_dir.glob("*.png"))
    label_files = sorted(label_dir.glob("*.json"))

    print("\n==============================")
    print(split_name.upper())
    print("==============================")

    print("Images:", len(image_files))
    print("Labels:", len(label_files))

    if len(image_files) != len(label_files):
        print("❌ Image / label count mismatch")
    else:
        print("✅ Image / label count matches")


    invalid_boxes = 0
    invalid_classes = 0
    missing_pairs = 0

    class_counts = {
        i: 0
        for i in range(len(CLASS_NAMES))
    }


    for image_path in image_files:

        label_path = (
            label_dir
            / f"{image_path.stem}.json"
        )

        if not label_path.exists():

            print(
                "Missing label for:",
                image_path.name
            )

            missing_pairs += 1
            continue


        with open(
            label_path,
            "r"
        ) as file:

            data = json.load(file)


        image_width = data["image_width"]
        image_height = data["image_height"]

        boxes = data["objects"]["bbox"]
        categories = data["objects"]["categories"]


        if len(boxes) != len(categories):

            print(
                "❌ Box/category mismatch:",
                image_path.name
            )


        for box, class_id in zip(
            boxes,
            categories
        ):

            x, y, w, h = box


            # -----------------------------
            # Validate class
            # -----------------------------

            if (
                class_id < 0
                or
                class_id >= len(CLASS_NAMES)
            ):

                invalid_classes += 1

            else:

                class_counts[
                    class_id
                ] += 1


            # -----------------------------
            # Validate box
            # -----------------------------

            if (
                w <= 0
                or
                h <= 0
                or
                x < 0
                or
                y < 0
                or
                x + w > image_width + 1
                or
                y + h > image_height + 1
            ):

                invalid_boxes += 1


    print(
        "\nMissing image-label pairs:",
        missing_pairs
    )

    print(
        "Invalid boxes:",
        invalid_boxes
    )

    print(
        "Invalid classes:",
        invalid_classes
    )


    print("\nClass distribution:")

    total_objects = 0

    for class_id, count in class_counts.items():

        total_objects += count

        print(
            f"{class_id:2d} "
            f"{CLASS_NAMES[class_id]:18s} "
            f"{count}"
        )


    print(
        "\nTotal objects:",
        total_objects
    )


if __name__ == "__main__":

    verify_split("train")
    verify_split("val")