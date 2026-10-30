from pathlib import Path
from collections import defaultdict
import json
import random
import re
import shutil


# ==========================================================
# SETTINGS
# ==========================================================

SEED = 42

TRAIN_RATIO = 0.80
VALID_RATIO = 0.10
TEST_RATIO = 0.10

BASE_DIR = Path(__file__).parent.parent

SOURCE_ROOT = BASE_DIR / "ambulance_raw"
OUTPUT_ROOT = BASE_DIR / "ambulance_clean"

SPLITS = ["train", "valid", "test"]

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


# ==========================================================
# NORMALIZE ROBOFLOW FILENAME
# ==========================================================

def get_base_key(filename):

    stem = Path(filename).stem

    stem = re.sub(
        r"\.rf\.[A-Za-z0-9_-]+$",
        "",
        stem
    )

    return stem.lower()


# ==========================================================
# LOAD ALL SOURCE DATA
# ==========================================================

print("=" * 75)
print("CREATING CLEAN AMBULANCE DATASET")
print("=" * 75)

print("\nSource:")
print(SOURCE_ROOT)

print("\nOutput:")
print(OUTPUT_ROOT)


all_records = []

category_definitions = None


for split in SPLITS:

    split_dir = SOURCE_ROOT / split

    annotation_path = (
        split_dir
        / "_annotations.coco.json"
    )

    if not annotation_path.exists():

        raise FileNotFoundError(
            f"Annotation file missing:\n"
            f"{annotation_path}"
        )

    with open(
        annotation_path,
        "r",
        encoding="utf-8"
    ) as file:

        coco = json.load(file)


    if category_definitions is None:

        category_definitions = coco.get(
            "categories",
            []
        )


    # ------------------------------------------------------
    # Map image ID -> annotations
    # ------------------------------------------------------

    annotations_by_image = defaultdict(list)

    for annotation in coco.get(
        "annotations",
        []
    ):

        annotations_by_image[
            annotation["image_id"]
        ].append(
            annotation
        )


    # ------------------------------------------------------
    # Read images
    # ------------------------------------------------------

    for image_info in coco.get(
        "images",
        []
    ):

        filename = image_info[
            "file_name"
        ]

        image_path = (
            split_dir
            / filename
        )

        if not image_path.exists():

            continue


        all_records.append(
            {
                "source_split": split,

                "path": image_path,

                "filename": filename,

                "base_key": get_base_key(
                    filename
                ),

                "image_info": image_info,

                "annotations":
                    annotations_by_image.get(
                        image_info["id"],
                        []
                    )
            }
        )


print(
    "\nTotal source image records:",
    len(all_records)
)


# ==========================================================
# GROUP ROBOFLOW VARIANTS
# ==========================================================

groups = defaultdict(list)


for record in all_records:

    groups[
        record["base_key"]
    ].append(
        record
    )


group_keys = list(
    groups.keys()
)


print(
    "Unique base-image groups:",
    len(group_keys)
)


# ==========================================================
# SHUFFLE GROUPS
# ==========================================================

random.seed(SEED)

random.shuffle(
    group_keys
)


# ==========================================================
# SPLIT BY BASE IMAGE GROUP
# ==========================================================

total_groups = len(
    group_keys
)


train_end = int(
    total_groups
    * TRAIN_RATIO
)

valid_end = (
    train_end
    +
    int(
        total_groups
        * VALID_RATIO
    )
)


assigned_groups = {

    "train":
        group_keys[
            :train_end
        ],

    "valid":
        group_keys[
            train_end:valid_end
        ],

    "test":
        group_keys[
            valid_end:
        ]
}


print(
    "\nGroup allocation:"
)

for split in SPLITS:

    print(
        f"{split:10s}: "
        f"{len(assigned_groups[split])}"
    )


# ==========================================================
# SAFETY CHECK — GROUP OVERLAP
# ==========================================================

train_keys = set(
    assigned_groups["train"]
)

valid_keys = set(
    assigned_groups["valid"]
)

test_keys = set(
    assigned_groups["test"]
)


assert len(
    train_keys & valid_keys
) == 0

assert len(
    train_keys & test_keys
) == 0

assert len(
    valid_keys & test_keys
) == 0


print(
    "\n✅ Group assignments contain no overlap"
)


# ==========================================================
# PREPARE OUTPUT DIRECTORY
# ==========================================================

if OUTPUT_ROOT.exists():

    print(
        "\nRemoving previous ambulance_clean..."
    )

    shutil.rmtree(
        OUTPUT_ROOT
    )


for split in SPLITS:

    (
        OUTPUT_ROOT
        / split
    ).mkdir(
        parents=True,
        exist_ok=True
    )


# ==========================================================
# WRITE EACH SPLIT
# ==========================================================

final_statistics = {}


for split in SPLITS:

    print(
        "\n"
        + "=" * 75
    )

    print(
        f"BUILDING {split.upper()}"
    )

    print(
        "=" * 75
    )


    new_images = []
    new_annotations = []

    new_image_id = 1
    new_annotation_id = 1


    image_count = 0
    annotation_count = 0


    for base_key in assigned_groups[
        split
    ]:

        records = groups[
            base_key
        ]


        # --------------------------------------------------
        # ALL variants stay in SAME split
        # --------------------------------------------------

        for record in records:

            source_path = record[
                "path"
            ]

            destination_path = (
                OUTPUT_ROOT
                / split
                / record["filename"]
            )


            shutil.copy2(
                source_path,
                destination_path
            )


            # --------------------------------------------------
            # NEW COCO IMAGE ENTRY
            # --------------------------------------------------

            old_image_info = record[
                "image_info"
            ]


            new_image_info = dict(
                old_image_info
            )


            new_image_info[
                "id"
            ] = new_image_id


            new_images.append(
                new_image_info
            )


            # --------------------------------------------------
            # COPY ANNOTATIONS WITH NEW IDS
            # --------------------------------------------------

            for old_annotation in record[
                "annotations"
            ]:

                new_annotation = dict(
                    old_annotation
                )


                new_annotation[
                    "id"
                ] = new_annotation_id


                new_annotation[
                    "image_id"
                ] = new_image_id


                new_annotations.append(
                    new_annotation
                )


                new_annotation_id += 1

                annotation_count += 1


            new_image_id += 1

            image_count += 1


    # ======================================================
    # CREATE COCO FILE
    # ======================================================

    output_coco = {

        "images":
            new_images,

        "annotations":
            new_annotations,

        "categories":
            category_definitions
    }


    annotation_output_path = (
        OUTPUT_ROOT
        / split
        / "_annotations.coco.json"
    )


    with open(
        annotation_output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output_coco,
            file
        )


    final_statistics[
        split
    ] = {

        "groups":
            len(
                assigned_groups[
                    split
                ]
            ),

        "images":
            image_count,

        "annotations":
            annotation_count
    }


    print(
        "Base groups:",
        len(
            assigned_groups[
                split
            ]
        )
    )

    print(
        "Images:",
        image_count
    )

    print(
        "Annotations:",
        annotation_count
    )


# ==========================================================
# VERIFY OUTPUT FILES
# ==========================================================

print(
    "\n"
    + "=" * 75
)

print(
    "VERIFYING OUTPUT"
)

print(
    "=" * 75
)


verification_ok = True


for split in SPLITS:

    split_dir = (
        OUTPUT_ROOT
        / split
    )

    annotation_path = (
        split_dir
        / "_annotations.coco.json"
    )


    with open(
        annotation_path,
        "r",
        encoding="utf-8"
    ) as file:

        coco = json.load(file)


    missing_images = 0


    for image_info in coco[
        "images"
    ]:

        image_path = (
            split_dir
            / image_info[
                "file_name"
            ]
        )


        if not image_path.exists():

            missing_images += 1


    print(
        f"{split:10s} | "
        f"images = {len(coco['images']):6d} | "
        f"annotations = {len(coco['annotations']):6d} | "
        f"missing = {missing_images}"
    )


    if missing_images > 0:

        verification_ok = False


# ==========================================================
# VERIFY CLEAN LEAKAGE
# ==========================================================

output_base_keys = {}


for split in SPLITS:

    split_dir = (
        OUTPUT_ROOT
        / split
    )


    keys = set()


    for path in split_dir.iterdir():

        if (
            path.is_file()
            and
            path.suffix.lower()
            in IMAGE_EXTENSIONS
        ):

            keys.add(
                get_base_key(
                    path.name
                )
            )


    output_base_keys[
        split
    ] = keys


train_valid_overlap = (
    output_base_keys["train"]
    &
    output_base_keys["valid"]
)

train_test_overlap = (
    output_base_keys["train"]
    &
    output_base_keys["test"]
)

valid_test_overlap = (
    output_base_keys["valid"]
    &
    output_base_keys["test"]
)


print(
    "\nCross-split overlaps:"
)

print(
    "Train <-> Valid:",
    len(
        train_valid_overlap
    )
)

print(
    "Train <-> Test :",
    len(
        train_test_overlap
    )
)

print(
    "Valid <-> Test :",
    len(
        valid_test_overlap
    )
)


leakage_ok = (

    len(
        train_valid_overlap
    )
    == 0

    and

    len(
        train_test_overlap
    )
    == 0

    and

    len(
        valid_test_overlap
    )
    == 0
)


# ==========================================================
# FINAL SUMMARY
# ==========================================================

print(
    "\n"
    + "=" * 75
)

print(
    "FINAL CLEAN DATASET SUMMARY"
)

print(
    "=" * 75
)


for split in SPLITS:

    stats = final_statistics[
        split
    ]

    print(
        f"{split.upper():10s} | "
        f"groups = {stats['groups']:5d} | "
        f"images = {stats['images']:6d} | "
        f"annotations = {stats['annotations']:6d}"
    )


print(
    "\nOriginal unique groups:",
    total_groups
)


assigned_total = sum(

    len(
        assigned_groups[
            split
        ]
    )

    for split in SPLITS
)


print(
    "Assigned unique groups:",
    assigned_total
)


# ==========================================================
# FINAL RESULT
# ==========================================================

if (
    verification_ok
    and
    leakage_ok
    and
    assigned_total
    ==
    total_groups
):

    print(
        "\n"
        "✅ CLEAN AMBULANCE DATASET CREATED!"
    )

    print(
        "✅ Every base-image group belongs "
        "to exactly one split."
    )

    print(
        "✅ COCO annotations rebuilt."
    )

    print(
        "✅ Source ambulance_raw was untouched."
    )

else:

    print(
        "\n"
        "❌ CLEAN DATASET VERIFICATION FAILED!"
    )


print(
    "=" * 75
)