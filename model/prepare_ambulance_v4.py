from pathlib import Path
import json
import shutil
from collections import defaultdict


# ==========================================================
# SETTINGS
# ==========================================================

BASE_DIR = Path(__file__).parent.parent

SOURCE_ROOT = BASE_DIR / "ambulance_clean"

OUTPUT_ROOT = BASE_DIR / "ambulance_v4"

SPLITS = [
    "train",
    "valid",
    "test",
]

# Roboflow category ID
SOURCE_AMBULANCE_CLASS = 3

# Our final detector category ID
TARGET_AMBULANCE_CLASS = 14


# ==========================================================
# HELPERS
# ==========================================================

def load_coco(annotation_path):

    with open(
        annotation_path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def clean_bbox(
    bbox,
    image_width,
    image_height
):

    if not bbox or len(bbox) != 4:
        return None

    x, y, w, h = bbox

    try:
        x = float(x)
        y = float(y)
        w = float(w)
        h = float(h)

    except (TypeError, ValueError):
        return None


    if w <= 0 or h <= 0:
        return None


    # Convert to corner coordinates
    x1 = x
    y1 = y
    x2 = x + w
    y2 = y + h


    # Clamp to image
    x1 = max(
        0.0,
        min(
            x1,
            float(image_width)
        )
    )

    y1 = max(
        0.0,
        min(
            y1,
            float(image_height)
        )
    )

    x2 = max(
        0.0,
        min(
            x2,
            float(image_width)
        )
    )

    y2 = max(
        0.0,
        min(
            y2,
            float(image_height)
        )
    )


    new_w = x2 - x1
    new_h = y2 - y1


    if new_w <= 1 or new_h <= 1:
        return None


    return [
        x1,
        y1,
        new_w,
        new_h
    ]


# ==========================================================
# PROCESS ONE SPLIT
# ==========================================================

def process_split(split_name):

    print("\n" + "=" * 75)
    print(
        f"PROCESSING SPLIT: "
        f"{split_name.upper()}"
    )
    print("=" * 75)


    source_dir = (
        SOURCE_ROOT
        / split_name
    )

    annotation_path = (
        source_dir
        / "_annotations.coco.json"
    )


    if not annotation_path.exists():

        raise FileNotFoundError(
            f"Missing annotation file:\n"
            f"{annotation_path}"
        )


    output_split_dir = (
        OUTPUT_ROOT
        / split_name
    )

    output_images_dir = (
        output_split_dir
        / "images"
    )

    output_labels_dir = (
        output_split_dir
        / "labels"
    )


    output_images_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_labels_dir.mkdir(
        parents=True,
        exist_ok=True
    )


    # ------------------------------------------------------
    # LOAD COCO
    # ------------------------------------------------------

    data = load_coco(
        annotation_path
    )


    image_map = {
        image["id"]: image
        for image in data.get(
            "images",
            []
        )
    }


    ambulance_annotations = defaultdict(
        list
    )


    for annotation in data.get(
        "annotations",
        []
    ):

        if (
            annotation.get(
                "category_id"
            )
            != SOURCE_AMBULANCE_CLASS
        ):
            continue


        ambulance_annotations[
            annotation["image_id"]
        ].append(
            annotation
        )


    # ------------------------------------------------------
    # STATS
    # ------------------------------------------------------

    copied_images = 0
    written_boxes = 0

    invalid_boxes = 0
    missing_images = 0

    multiple_ambulance_images = 0


    # ------------------------------------------------------
    # PROCESS IMAGES CONTAINING AMBULANCE
    # ------------------------------------------------------

    for image_id, annotations in ambulance_annotations.items():

        image_info = image_map.get(
            image_id
        )


        if image_info is None:
            continue


        file_name = image_info[
            "file_name"
        ]

        image_width = int(
            image_info["width"]
        )

        image_height = int(
            image_info["height"]
        )


        source_image_path = (
            source_dir
            / file_name
        )


        if not source_image_path.exists():

            print(
                "Missing image:",
                source_image_path
            )

            missing_images += 1

            continue


        clean_objects = []


        for annotation in annotations:

            bbox = clean_bbox(
                annotation.get(
                    "bbox"
                ),
                image_width,
                image_height
            )


            if bbox is None:

                invalid_boxes += 1

                continue


            clean_objects.append(
                {
                    "bbox": bbox,

                    # Our final class
                    "category": (
                        TARGET_AMBULANCE_CLASS
                    ),

                    # Helpful metadata
                    "source_category_id": (
                        SOURCE_AMBULANCE_CLASS
                    ),

                    "source_annotation_id": (
                        annotation.get(
                            "id"
                        )
                    )
                }
            )


        # If every ambulance box was invalid,
        # don't copy the image.
        if not clean_objects:
            continue


        if len(clean_objects) > 1:

            multiple_ambulance_images += 1


        # --------------------------------------------------
        # COPY IMAGE
        # --------------------------------------------------

        destination_image_path = (
            output_images_dir
            / file_name
        )


        shutil.copy2(
            source_image_path,
            destination_image_path
        )


        # --------------------------------------------------
        # WRITE OUR JSON LABEL
        # --------------------------------------------------

        label_name = (
            Path(file_name).stem
            + ".json"
        )


        label_path = (
            output_labels_dir
            / label_name
        )


        label_data = {

            "image": file_name,

            "width": image_width,

            "height": image_height,

            # Important:
            # other traffic objects in these images
            # are not guaranteed to use our BMD labels.
            #
            # Later the loss will use this field to
            # disable negative/background objectness
            # supervision for these samples.
            "supervision": "positive_only",

            "source": (
                "indian_emergency_vehicles"
            ),

            "objects": clean_objects
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


        copied_images += 1

        written_boxes += len(
            clean_objects
        )


    # ------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------

    print(
        f"Images containing usable ambulance: "
        f"{copied_images}"
    )

    print(
        f"Ambulance boxes written: "
        f"{written_boxes}"
    )

    print(
        f"Images with >1 ambulance: "
        f"{multiple_ambulance_images}"
    )

    print(
        f"Invalid boxes skipped: "
        f"{invalid_boxes}"
    )

    print(
        f"Missing source images: "
        f"{missing_images}"
    )


    return {
        "images": copied_images,
        "boxes": written_boxes,
        "invalid": invalid_boxes,
        "missing": missing_images
    }


# ==========================================================
# MAIN
# ==========================================================

print("=" * 75)
print("PREPARING V4 AMBULANCE DATASET")
print("=" * 75)

print(
    f"Source class "
    f"{SOURCE_AMBULANCE_CLASS}"
    f" -> "
    f"Target class "
    f"{TARGET_AMBULANCE_CLASS}"
)

print(
    f"Output root:\n"
    f"{OUTPUT_ROOT}"
)

# ==========================================================
# CLEAN OLD OUTPUT
# ==========================================================

if OUTPUT_ROOT.exists():

    print(
        "\nRemoving previous ambulance_v4 dataset..."
    )

    shutil.rmtree(
        OUTPUT_ROOT
    )


OUTPUT_ROOT.mkdir(
    parents=True,
    exist_ok=True
)


print(
    "\nClean output directory created."
)

all_stats = {}


for split in SPLITS:

    all_stats[
        split
    ] = process_split(
        split
    )


# ==========================================================
# FINAL SUMMARY
# ==========================================================

print("\n" + "=" * 75)
print("FINAL SUMMARY")
print("=" * 75)


total_images = 0
total_boxes = 0


for split in SPLITS:

    stats = all_stats[
        split
    ]

    total_images += stats[
        "images"
    ]

    total_boxes += stats[
        "boxes"
    ]


    print(
        f"{split.upper():5s} | "
        f"images = "
        f"{stats['images']:5d} | "
        f"boxes = "
        f"{stats['boxes']:5d}"
    )


print("-" * 75)

print(
    f"TOTAL IMAGES: "
    f"{total_images}"
)

print(
    f"TOTAL AMBULANCE BOXES: "
    f"{total_boxes}"
)


print("\n✅ V4 AMBULANCE DATASET PREPARED")
print("=" * 75)