from pathlib import Path
from collections import defaultdict
import hashlib


# ==========================================================
# SETTINGS
# ==========================================================

BASE_DIR = Path(__file__).parent.parent

DATASET_ROOT = (
    BASE_DIR
    / "ambulance_clean"
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
# HASH IMAGE FILE
# ==========================================================

def calculate_sha256(path):

    hasher = hashlib.sha256()

    with open(path, "rb") as file:

        while True:

            chunk = file.read(
                1024 * 1024
            )

            if not chunk:
                break

            hasher.update(
                chunk
            )

    return hasher.hexdigest()


# ==========================================================
# COLLECT IMAGE HASHES
# ==========================================================

def collect_hashes(split):

    split_dir = (
        DATASET_ROOT
        / split
    )

    if not split_dir.exists():

        raise FileNotFoundError(
            f"Split not found:\n"
            f"{split_dir}"
        )


    hash_map = defaultdict(list)

    image_count = 0


    for path in split_dir.iterdir():

        if (
            path.is_file()
            and
            path.suffix.lower()
            in IMAGE_EXTENSIONS
        ):

            image_hash = (
                calculate_sha256(
                    path
                )
            )

            hash_map[
                image_hash
            ].append(
                path.name
            )

            image_count += 1


    return (
        hash_map,
        image_count
    )


# ==========================================================
# START
# ==========================================================

print("=" * 80)
print("AMBULANCE IMAGE-CONTENT LEAKAGE CHECK")
print("=" * 80)

print(
    "\nDataset:",
    DATASET_ROOT
)


# ==========================================================
# HASH ALL SPLITS
# ==========================================================

split_hashes = {}

split_image_counts = {}


for split in SPLITS:

    print(
        f"\nHashing {split}..."
    )

    (
        hash_map,
        image_count
    ) = collect_hashes(
        split
    )

    split_hashes[
        split
    ] = hash_map

    split_image_counts[
        split
    ] = image_count


    print(
        f"{split:10s}: "
        f"{image_count} images"
    )

    print(
        f"{'':10s}  "
        f"{len(hash_map)} unique hashes"
    )


# ==========================================================
# IDENTICAL FILES WITHIN EACH SPLIT
# ==========================================================

print(
    "\n"
    + "=" * 80
)

print(
    "IDENTICAL IMAGE FILES WITHIN EACH SPLIT"
)

print(
    "=" * 80
)


for split in SPLITS:

    duplicates = {

        image_hash: filenames

        for image_hash, filenames
        in split_hashes[
            split
        ].items()

        if len(
            filenames
        ) > 1
    }


    duplicate_file_count = sum(

        len(
            filenames
        ) - 1

        for filenames
        in duplicates.values()
    )


    print(
        f"\n{split.upper()}"
    )

    print(
        "Duplicate hash groups:",
        len(
            duplicates
        )
    )

    print(
        "Extra identical files:",
        duplicate_file_count
    )


    shown = 0

    for image_hash, filenames in (
        duplicates.items()
    ):

        if shown >= 5:
            break

        print(
            f"\n  SHA256: "
            f"{image_hash[:16]}..."
        )

        for filename in filenames:

            print(
                f"    {filename}"
            )

        shown += 1


    if len(
        duplicates
    ) > 5:

        print(
            f"\n  ... "
            f"{len(duplicates) - 5} "
            f"more duplicate groups"
        )


# ==========================================================
# CROSS-SPLIT HASH LEAKAGE
# ==========================================================

print(
    "\n"
    + "=" * 80
)

print(
    "CROSS-SPLIT IDENTICAL IMAGE CHECK"
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

    hashes_a = set(
        split_hashes[
            split_a
        ].keys()
    )

    hashes_b = set(
        split_hashes[
            split_b
        ].keys()
    )


    overlap = (
        hashes_a
        &
        hashes_b
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
        "Identical image hashes:",
        len(
            overlap
        )
    )


    shown = 0

    for image_hash in sorted(
        overlap
    ):

        if shown >= 10:
            break


        print(
            f"\n  SHA256: "
            f"{image_hash[:16]}..."
        )


        print(
            f"  {split_a}:"
        )

        for filename in split_hashes[
            split_a
        ][image_hash]:

            print(
                f"    {filename}"
            )


        print(
            f"  {split_b}:"
        )

        for filename in split_hashes[
            split_b
        ][image_hash]:

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
            f"more overlaps"
        )


# ==========================================================
# FINAL RESULT
# ==========================================================

total_pairwise_overlaps = sum(

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


print(
    "\nTrain images:",
    split_image_counts[
        "train"
    ]
)

print(
    "Valid images:",
    split_image_counts[
        "valid"
    ]
)

print(
    "Test images:",
    split_image_counts[
        "test"
    ]
)


print(
    "\nTotal pairwise identical "
    "cross-split hashes:",
    total_pairwise_overlaps
)


if total_pairwise_overlaps == 0:

    print(
        "\n"
        "✅ NO EXACT IMAGE-CONTENT "
        "LEAKAGE DETECTED!"
    )

else:

    print(
        "\n"
        "⚠️ EXACT IMAGE-CONTENT "
        "LEAKAGE DETECTED!"
    )

    print(
        "\nDo NOT start V4 training yet."
    )


print(
    "\nNOTE:"
)

print(
    "SHA-256 detects byte-identical images."
)

print(
    "Different crops, resizing, compression, "
    "or augmentation can still produce visually "
    "similar images with different hashes."
)

print("=" * 80)