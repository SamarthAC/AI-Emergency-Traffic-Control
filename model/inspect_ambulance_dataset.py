from pathlib import Path
import json
from collections import Counter, defaultdict


# ==========================================================
# PATHS
# ==========================================================

BASE_DIR = Path(__file__).parent.parent

AMBULANCE_ROOT = BASE_DIR / "ambulance_raw"

SPLITS = {
    "train": AMBULANCE_ROOT / "train",
    "valid": AMBULANCE_ROOT / "valid",
    "test": AMBULANCE_ROOT / "test",
}


# ==========================================================
# HELPERS
# ==========================================================

def load_coco(split_dir):
    annotation_file = split_dir / "_annotations.coco.json"

    with open(
        annotation_file,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def analyze_split(split_name, split_dir):

    print("\n" + "=" * 75)
    print(f"SPLIT: {split_name.upper()}")
    print("=" * 75)

    data = load_coco(split_dir)

    images = data.get("images", [])
    annotations = data.get("annotations", [])
    categories = data.get("categories", [])

    category_map = {
        category["id"]: category["name"]
        for category in categories
    }

    print(
        f"Images       : {len(images)}"
    )

    print(
        f"Annotations  : {len(annotations)}"
    )

    print(
        f"Categories   : {len(categories)}"
    )

    print("\nCATEGORY LIST")
    print("-" * 75)

    for category in categories:

        print(
            f'ID {category["id"]:3d} -> '
            f'{category["name"]}'
        )


    # ======================================================
    # COUNT ANNOTATIONS BY CATEGORY
    # ======================================================

    category_counts = Counter()

    images_per_category = defaultdict(set)

    image_map = {
        image["id"]: image
        for image in images
    }


    for annotation in annotations:

        category_id = annotation["category_id"]

        category_counts[
            category_id
        ] += 1

        images_per_category[
            category_id
        ].add(
            annotation["image_id"]
        )


    print("\nANNOTATION COUNTS")
    print("-" * 75)

    sorted_categories = sorted(
        category_map.keys()
    )

    for category_id in sorted_categories:

        category_name = category_map[
            category_id
        ]

        box_count = category_counts[
            category_id
        ]

        image_count = len(
            images_per_category[
                category_id
            ]
        )

        print(
            f"{category_id:3d} | "
            f"{category_name:30s} | "
            f"boxes = {box_count:6d} | "
            f"images = {image_count:6d}"
        )


    # ======================================================
    # FIND AMBULANCE-RELATED CLASSES
    # ======================================================

    ambulance_categories = []

    for category_id, category_name in category_map.items():

        if "ambulance" in category_name.lower():

            ambulance_categories.append(
                (
                    category_id,
                    category_name
                )
            )


    print("\nAMBULANCE-RELATED CATEGORIES")
    print("-" * 75)

    if not ambulance_categories:

        print(
            "No ambulance-related categories found."
        )

    else:

        for category_id, category_name in ambulance_categories:

            print(
                f"{category_id:3d} | "
                f"{category_name:30s} | "
                f"boxes = "
                f"{category_counts[category_id]:6d} | "
                f"images = "
                f"{len(images_per_category[category_id]):6d}"
            )


    # ======================================================
    # BBOX STATISTICS FOR AMBULANCE-RELATED CLASSES
    # ======================================================

    print("\nAMBULANCE BBOX STATISTICS")
    print("-" * 75)

    for category_id, category_name in ambulance_categories:

        widths = []
        heights = []
        areas = []


        for annotation in annotations:

            if annotation["category_id"] != category_id:
                continue


            bbox = annotation.get(
                "bbox",
                []
            )


            if len(bbox) != 4:
                continue


            x, y, w, h = bbox


            if w <= 0 or h <= 0:
                continue


            widths.append(w)
            heights.append(h)

            areas.append(
                w * h
            )


        if not widths:

            continue


        widths_sorted = sorted(widths)
        heights_sorted = sorted(heights)
        areas_sorted = sorted(areas)


        def percentile(values, fraction):

            index = int(
                (len(values) - 1)
                * fraction
            )

            return values[index]


        print(
            f"\nClass: {category_name}"
        )

        print(
            f"Boxes: {len(widths)}"
        )

        print(
            f"Width median : "
            f"{percentile(widths_sorted, 0.50):.2f}px"
        )

        print(
            f"Height median: "
            f"{percentile(heights_sorted, 0.50):.2f}px"
        )

        print(
            f"Area median  : "
            f"{percentile(areas_sorted, 0.50):.2f}px²"
        )

        print(
            f"Width 10%-90%: "
            f"{percentile(widths_sorted, 0.10):.2f}"
            f" - "
            f"{percentile(widths_sorted, 0.90):.2f}px"
        )

        print(
            f"Height 10%-90%: "
            f"{percentile(heights_sorted, 0.10):.2f}"
            f" - "
            f"{percentile(heights_sorted, 0.90):.2f}px"
        )


# ==========================================================
# MAIN
# ==========================================================

print("=" * 75)
print("AMBULANCE DATASET INSPECTION")
print("=" * 75)


for split_name, split_dir in SPLITS.items():

    if not split_dir.exists():

        print(
            f"\nMissing split: "
            f"{split_dir}"
        )

        continue

    analyze_split(
        split_name,
        split_dir
    )


print("\n" + "=" * 75)
print("✅ AMBULANCE DATASET INSPECTION COMPLETE")
print("=" * 75)