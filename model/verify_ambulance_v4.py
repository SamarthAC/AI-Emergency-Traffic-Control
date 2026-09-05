from pathlib import Path
from collections import defaultdict
import hashlib
import json
import re


# ==========================================================
# SETTINGS
# ==========================================================

BASE_DIR = Path(__file__).parent.parent
DATASET_ROOT = BASE_DIR / "ambulance_v4"

SPLITS = ["train", "valid", "test"]

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}

EXPECTED_CLASS = 14
EXPECTED_SUPERVISION = "positive_only"


# ==========================================================
# HELPERS
# ==========================================================

def get_base_key(filename):
    stem = Path(filename).stem

    stem = re.sub(
        r"\.rf\.[A-Za-z0-9_-]+$",
        "",
        stem
    )

    return stem.lower()


def calculate_sha256(path):
    hasher = hashlib.sha256()

    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            hasher.update(chunk)

    return hasher.hexdigest()


# ==========================================================
# VERIFY ONE SPLIT
# ==========================================================

def verify_split(split):
    split_dir = DATASET_ROOT / split

    images_dir = split_dir / "images"
    labels_dir = split_dir / "labels"

    if not images_dir.exists():
        raise FileNotFoundError(
            f"Missing images directory:\n{images_dir}"
        )

    if not labels_dir.exists():
        raise FileNotFoundError(
            f"Missing labels directory:\n{labels_dir}"
        )

    images = sorted([
        path
        for path in images_dir.iterdir()
        if (
            path.is_file()
            and path.suffix.lower()
            in IMAGE_EXTENSIONS
        )
    ])

    labels = sorted(
        labels_dir.glob("*.json")
    )

    image_stems = {
        path.stem
        for path in images
    }

    label_stems = {
        path.stem
        for path in labels
    }

    missing_labels = (
        image_stems - label_stems
    )

    missing_images = (
        label_stems - image_stems
    )

    invalid_json = 0
    wrong_supervision = 0
    wrong_classes = 0
    empty_objects = 0
    invalid_boxes = 0
    image_name_mismatches = 0

    total_boxes = 0

    base_keys = set()

    hash_map = defaultdict(list)

    class_counts = defaultdict(int)

    # ------------------------------------------------------
    # IMAGE KEYS + HASHES
    # ------------------------------------------------------

    for image_path in images:
        base_keys.add(
            get_base_key(
                image_path.name
            )
        )

        image_hash = calculate_sha256(
            image_path
        )

        hash_map[
            image_hash
        ].append(
            image_path.name
        )

    # ------------------------------------------------------
    # VERIFY LABELS
    # ------------------------------------------------------

    for label_path in labels:
        try:
            with open(
                label_path,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

        except Exception:
            invalid_json += 1
            continue

        # ----------------------------------------------
        # Image filename
        # ----------------------------------------------

        expected_image_stem = (
            label_path.stem
        )

        label_image = data.get(
            "image"
        )

        if (
            not label_image
            or Path(label_image).stem
            != expected_image_stem
        ):
            image_name_mismatches += 1

        # ----------------------------------------------
        # Supervision
        # ----------------------------------------------

        if (
            data.get("supervision")
            != EXPECTED_SUPERVISION
        ):
            wrong_supervision += 1

        # ----------------------------------------------
        # Objects
        # ----------------------------------------------

        objects = data.get(
            "objects",
            []
        )

        if not objects:
            empty_objects += 1
            continue

        width = data.get("width")
        height = data.get("height")

        for obj in objects:
            category = obj.get(
                "category"
            )

            class_counts[
                category
            ] += 1

            if category != EXPECTED_CLASS:
                wrong_classes += 1

            bbox = obj.get(
                "bbox"
            )

            if (
                not bbox
                or len(bbox) != 4
            ):
                invalid_boxes += 1
                continue

            try:
                x, y, w, h = map(
                    float,
                    bbox
                )

            except (
                TypeError,
                ValueError
            ):
                invalid_boxes += 1
                continue

            if (
                width is None
                or height is None
            ):
                invalid_boxes += 1
                continue

            if (
                w <= 0
                or h <= 0
                or x < 0
                or y < 0
                or x + w > float(width) + 1e-6
                or y + h > float(height) + 1e-6
            ):
                invalid_boxes += 1
                continue

            total_boxes += 1

    duplicate_hash_groups = {
        image_hash: filenames
        for image_hash, filenames
        in hash_map.items()
        if len(filenames) > 1
    }

    return {
        "images": len(images),
        "labels": len(labels),
        "boxes": total_boxes,

        "missing_labels":
            missing_labels,

        "missing_images":
            missing_images,

        "invalid_json":
            invalid_json,

        "wrong_supervision":
            wrong_supervision,

        "wrong_classes":
            wrong_classes,

        "empty_objects":
            empty_objects,

        "invalid_boxes":
            invalid_boxes,

        "image_name_mismatches":
            image_name_mismatches,

        "base_keys":
            base_keys,

        "hash_map":
            hash_map,

        "duplicate_hash_groups":
            duplicate_hash_groups,

        "class_counts":
            dict(class_counts),
    }


# ==========================================================
# MAIN
# ==========================================================

print("=" * 80)
print("VERIFYING FINAL AMBULANCE V4 DATASET")
print("=" * 80)

print(
    "\nDataset:",
    DATASET_ROOT
)


results = {}


for split in SPLITS:
    print(
        f"\nChecking {split}..."
    )

    results[split] = verify_split(
        split
    )


# ==========================================================
# SPLIT SUMMARY
# ==========================================================

print(
    "\n"
    + "=" * 80
)

print("SPLIT SUMMARY")
print("=" * 80)


for split in SPLITS:
    result = results[split]

    print(
        f"\n{split.upper()}"
    )

    print(
        "Images:",
        result["images"]
    )

    print(
        "Labels:",
        result["labels"]
    )

    print(
        "Valid ambulance boxes:",
        result["boxes"]
    )

    print(
        "Class counts:",
        result["class_counts"]
    )

    print(
        "Missing labels:",
        len(
            result["missing_labels"]
        )
    )

    print(
        "Labels without image:",
        len(
            result["missing_images"]
        )
    )

    print(
        "Invalid JSON:",
        result["invalid_json"]
    )

    print(
        "Wrong supervision:",
        result["wrong_supervision"]
    )

    print(
        "Wrong classes:",
        result["wrong_classes"]
    )

    print(
        "Empty object labels:",
        result["empty_objects"]
    )

    print(
        "Invalid boxes:",
        result["invalid_boxes"]
    )

    print(
        "Image-name mismatches:",
        result["image_name_mismatches"]
    )

    print(
        "Within-split exact duplicate groups:",
        len(
            result[
                "duplicate_hash_groups"
            ]
        )
    )


# ==========================================================
# CROSS-SPLIT BASE NAME CHECK
# ==========================================================

print(
    "\n"
    + "=" * 80
)

print("CROSS-SPLIT BASE-IMAGE CHECK")
print("=" * 80)


pairs = [
    ("train", "valid"),
    ("train", "test"),
    ("valid", "test"),
]


base_overlap_total = 0


for split_a, split_b in pairs:
    overlap = (
        results[split_a]["base_keys"]
        &
        results[split_b]["base_keys"]
    )

    base_overlap_total += len(
        overlap
    )

    print(
        f"{split_a.upper()} "
        f"<-> "
        f"{split_b.upper()}: "
        f"{len(overlap)}"
    )


# ==========================================================
# CROSS-SPLIT SHA256 CHECK
# ==========================================================

print(
    "\n"
    + "=" * 80
)

print("CROSS-SPLIT EXACT-CONTENT CHECK")
print("=" * 80)


hash_overlap_total = 0


for split_a, split_b in pairs:
    hashes_a = set(
        results[
            split_a
        ]["hash_map"].keys()
    )

    hashes_b = set(
        results[
            split_b
        ]["hash_map"].keys()
    )

    overlap = (
        hashes_a
        &
        hashes_b
    )

    hash_overlap_total += len(
        overlap
    )

    print(
        f"{split_a.upper()} "
        f"<-> "
        f"{split_b.upper()}: "
        f"{len(overlap)}"
    )


# ==========================================================
# FINAL VALIDATION
# ==========================================================

dataset_ok = True


for split in SPLITS:
    result = results[split]

    if result["images"] == 0:
        dataset_ok = False

    if (
        result["images"]
        != result["labels"]
    ):
        dataset_ok = False

    if result["missing_labels"]:
        dataset_ok = False

    if result["missing_images"]:
        dataset_ok = False

    if result["invalid_json"] > 0:
        dataset_ok = False

    if result["wrong_supervision"] > 0:
        dataset_ok = False

    if result["wrong_classes"] > 0:
        dataset_ok = False

    if result["empty_objects"] > 0:
        dataset_ok = False

    if result["invalid_boxes"] > 0:
        dataset_ok = False

    if (
        result[
            "image_name_mismatches"
        ]
        > 0
    ):
        dataset_ok = False


if base_overlap_total > 0:
    dataset_ok = False


if hash_overlap_total > 0:
    dataset_ok = False


# ==========================================================
# FINAL RESULT
# ==========================================================

print(
    "\n"
    + "=" * 80
)

print("FINAL RESULT")
print("=" * 80)

print(
    "\nBase-name cross-split overlaps:",
    base_overlap_total
)

print(
    "Exact-content cross-split overlaps:",
    hash_overlap_total
)


if dataset_ok:
    print(
        "\n"
        "✅ AMBULANCE V4 DATASET VERIFIED!"
    )

    print(
        "✅ Image/label pairs valid."
    )

    print(
        "✅ All labels use class 14."
    )

    print(
        "✅ All samples use positive_only supervision."
    )

    print(
        "✅ Bounding boxes valid."
    )

    print(
        "✅ No filename-based cross-split leakage."
    )

    print(
        "✅ No exact-content cross-split leakage."
    )

else:
    print(
        "\n"
        "❌ AMBULANCE V4 VERIFICATION FAILED!"
    )


print("=" * 80)