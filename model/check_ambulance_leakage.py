from pathlib import Path
from collections import defaultdict
import re


# ==========================================================
# SETTINGS
# ==========================================================

BASE_DIR = Path(__file__).parent.parent

AMBULANCE_RAW_DIR = (
    BASE_DIR
    / "ambulance_raw"
)

SPLITS = [
    "train",
    "valid",
    "test"
]

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png"
}


# ==========================================================
# HELPERS
# ==========================================================

def normalize_filename(filename):
    """
    Remove Roboflow augmentation/hash suffix.

    Example:

    ambulance123.rf.abcdef123456.jpg

    becomes:

    ambulance123
    """

    stem = Path(filename).stem

    # Remove Roboflow .rf.<hash>
    stem = re.sub(
        r"\.rf\.[A-Za-z0-9_-]+$",
        "",
        stem
    )

    return stem.lower()


def collect_images(split_dir):
    """
    Collect all images from a Roboflow split.

    Supports both:

    split/images/*.jpg

    and

    split/*.jpg
    """

    images_dir = split_dir / "images"

    if images_dir.exists():
        search_dir = images_dir
    else:
        search_dir = split_dir

    if not search_dir.exists():
        raise FileNotFoundError(
            f"Split directory not found:\n"
            f"{search_dir}"
        )

    records = []

    for path in search_dir.iterdir():

        if (
            path.is_file()
            and path.suffix.lower()
            in IMAGE_EXTENSIONS
        ):

            records.append(
                {
                    "path": path,
                    "filename": path.name,
                    "base_key": normalize_filename(
                        path.name
                    )
                }
            )

    return records

# ==========================================================
# START
# ==========================================================

print("=" * 80)
print("AMBULANCE DATASET LEAKAGE CHECK")
print("=" * 80)

print(
    "\nDataset:",
    AMBULANCE_RAW_DIR
)


# ==========================================================
# LOAD SPLITS
# ==========================================================

split_records = {}


for split in SPLITS:

    split_dir = (
        AMBULANCE_RAW_DIR
        / split
    )

    records = collect_images(
        split_dir
    )

    split_records[
        split
    ] = records

    print(
        f"{split:10s}: "
        f"{len(records)} images"
    )


# ==========================================================
# BUILD BASE-NAME INDEX
# ==========================================================

split_keys = {}


for split in SPLITS:

    key_map = defaultdict(
        list
    )

    for record in split_records[
        split
    ]:

        key_map[
            record["base_key"]
        ].append(
            record["filename"]
        )

    split_keys[
        split
    ] = key_map


# ==========================================================
# CHECK DUPLICATES INSIDE EACH SPLIT
# ==========================================================

print(
    "\n"
    + "=" * 80
)

print(
    "DUPLICATES WITHIN EACH SPLIT"
)

print(
    "=" * 80
)


internal_duplicates = {}


for split in SPLITS:

    duplicates = {

        key: filenames

        for key, filenames
        in split_keys[
            split
        ].items()

        if len(
            filenames
        ) > 1
    }


    internal_duplicates[
        split
    ] = duplicates


    print(
        f"\n{split.upper()}"
    )

    print(
        "Duplicate base images:",
        len(
            duplicates
        )
    )


    shown = 0

    for key, filenames in duplicates.items():

        if shown >= 10:
            break

        print(
            f"\n  Base key: {key}"
        )

        for filename in filenames:

            print(
                f"    {filename}"
            )

        shown += 1


    if len(
        duplicates
    ) > 10:

        print(
            f"\n  ... "
            f"{len(duplicates) - 10} "
            f"more duplicate groups"
        )


# ==========================================================
# CHECK CROSS-SPLIT LEAKAGE
# ==========================================================

print(
    "\n"
    + "=" * 80
)

print(
    "CROSS-SPLIT LEAKAGE"
)

print(
    "=" * 80
)


split_pairs = [
    (
        "train",
        "valid"
    ),
    (
        "train",
        "test"
    ),
    (
        "valid",
        "test"
    )
]


cross_split_results = {}


for split_a, split_b in split_pairs:

    keys_a = set(
        split_keys[
            split_a
        ].keys()
    )

    keys_b = set(
        split_keys[
            split_b
        ].keys()
    )


    overlap = (
        keys_a
        &
        keys_b
    )


    cross_split_results[
        (
            split_a,
            split_b
        )
    ] = overlap


    print(
        f"\n{split_a.upper()} "
        f"<-> "
        f"{split_b.upper()}"
    )

    print(
        "Overlapping base images:",
        len(
            overlap
        )
    )


    shown = 0

    for key in sorted(
        overlap
    ):

        if shown >= 10:
            break


        print(
            f"\n  Base key: {key}"
        )


        print(
            f"  {split_a}:"
        )

        for filename in split_keys[
            split_a
        ][key]:

            print(
                f"    {filename}"
            )


        print(
            f"  {split_b}:"
        )

        for filename in split_keys[
            split_b
        ][key]:

            print(
                f"    {filename}"
            )


        shown += 1


    if len(
        overlap
    ) > 10:

        print(
            f"\n  ... "
            f"{len(overlap) - 10} "
            f"more overlapping groups"
        )


# ==========================================================
# UNIQUE ORIGINAL COUNTS
# ==========================================================

print(
    "\n"
    + "=" * 80
)

print(
    "UNIQUE BASE IMAGE COUNTS"
)

print(
    "=" * 80
)


all_keys = set()


for split in SPLITS:

    keys = set(
        split_keys[
            split
        ].keys()
    )

    all_keys.update(
        keys
    )

    print(
        f"{split:10s}: "
        f"{len(keys)} unique base images"
    )


print(
    "\nTotal unique base images:",
    len(
        all_keys
    )
)


# ==========================================================
# FINAL RESULT
# ==========================================================

total_cross_split_leaks = sum(

    len(
        overlap
    )

    for overlap
    in cross_split_results.values()
)


print(
    "\n"
    + "=" * 80
)

print(
    "FINAL RESULT"
)

print(
    "=" * 80
)


if total_cross_split_leaks == 0:

    print(
        "\n✅ NO CROSS-SPLIT BASE-FILENAME "
        "LEAKAGE DETECTED!"
    )

    print(
        "\nTrain / valid / test appear separated "
        "based on Roboflow base filenames."
    )

else:

    print(
        "\n⚠️ POSSIBLE DATASET LEAKAGE DETECTED!"
    )

    print(
        "\nTotal pairwise overlapping "
        "base-image groups:",
        total_cross_split_leaks
    )

    print(
        "\nDo NOT start final V4 training yet."
    )

    print(
        "We should clean the split first."
    )


print(
    "\nNOTE:"
)

print(
    "This test detects filename-based Roboflow duplicates."
)

print(
    "It does not yet detect visually identical images "
    "with completely different filenames."
)

print("=" * 80)