from pathlib import Path
from collections import Counter
import json
import math


# ==========================================================
# SETTINGS
# ==========================================================

BASE_DIR = Path(__file__).parent.parent

BMD_TRAIN_LABELS = (
    BASE_DIR
    / "dataset_v4"
    / "train"
    / "labels"
)

AMBULANCE_TRAIN_LABELS = (
    BASE_DIR
    / "ambulance_v4"
    / "train"
    / "labels"
)

NUM_CLASSES = 15


CLASS_NAMES = {
    0: "Hatchback",
    1: "Sedan",
    2: "SUV",
    3: "MUV",
    4: "Bus",
    5: "Truck",
    6: "Three-wheeler",
    7: "Two-wheeler",
    8: "LCV",
    9: "Mini-bus",
    10: "Tempo-traveller",
    11: "Bicycle",
    12: "Van",
    13: "Other",
    14: "Ambulance",
}


# ==========================================================
# READ BMD
# ==========================================================

def count_bmd():

    counts = Counter()

    label_files = list(
        BMD_TRAIN_LABELS.glob("*.json")
    )

    print(
        f"BMD label files: "
        f"{len(label_files)}"
    )

    for label_path in label_files:

        with open(
            label_path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        objects = data.get(
            "objects",
            []
        )

        # Supports both:
        # objects = {"bbox": [...], "category": [...]}
        # and
        # objects = [{"bbox": ..., "category": ...}, ...]

        if isinstance(objects, dict):

            categories = objects.get(
                "categories",
                []
            )

            for category in categories:

                category = int(category)

                if 0 <= category < 14:
                    counts[category] += 1

        elif isinstance(objects, list):

            for obj in objects:

                category = obj.get(
                    "category"
                )

                if category is None:
                    continue

                category = int(category)

                if 0 <= category < 14:
                    counts[category] += 1

    return counts


# ==========================================================
# READ AMBULANCE
# ==========================================================

def count_ambulance():

    counts = Counter()

    label_files = list(
        AMBULANCE_TRAIN_LABELS.glob(
            "*.json"
        )
    )

    print(
        f"Ambulance label files: "
        f"{len(label_files)}"
    )

    positive_only_files = 0
    wrong_supervision = 0

    for label_path in label_files:

        with open(
            label_path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if (
            data.get("supervision")
            == "positive_only"
        ):
            positive_only_files += 1
        else:
            wrong_supervision += 1

        for obj in data.get(
            "objects",
            []
        ):

            category = obj.get(
                "category"
            )

            if category is None:
                continue

            category = int(category)

            counts[category] += 1

    print(
        "Positive-only ambulance files:",
        positive_only_files
    )

    print(
        "Wrong ambulance supervision:",
        wrong_supervision
    )

    return counts


# ==========================================================
# CALCULATE COUNTS
# ==========================================================

print("=" * 80)
print("V4 TRAINING CLASS DISTRIBUTION")
print("=" * 80)


bmd_counts = count_bmd()

ambulance_counts = count_ambulance()


combined_counts = Counter()

combined_counts.update(
    bmd_counts
)

combined_counts.update(
    ambulance_counts
)


# ==========================================================
# DISPLAY DISTRIBUTION
# ==========================================================

print(
    "\n"
    + "=" * 80
)

print("CLASS DISTRIBUTION")
print("=" * 80)


total_objects = sum(
    combined_counts.values()
)


for class_id in range(
    NUM_CLASSES
):

    bmd = bmd_counts[
        class_id
    ]

    ambulance = ambulance_counts[
        class_id
    ]

    total = combined_counts[
        class_id
    ]

    percentage = (
        total / total_objects * 100
        if total_objects > 0
        else 0
    )

    print(
        f"{class_id:2d} "
        f"{CLASS_NAMES[class_id]:18s} | "
        f"BMD={bmd:6d} | "
        f"AMB={ambulance:6d} | "
        f"TOTAL={total:6d} | "
        f"{percentage:6.2f}%"
    )


print("-" * 80)

print(
    "TOTAL OBJECTS:",
    total_objects
)


# ==========================================================
# CLASS WEIGHTS
# ==========================================================
#
# sqrt inverse-frequency:
#
# raw_weight = sqrt(
#     average_nonzero_count / class_count
# )
#
# Then normalize active weights so
# their average is approximately 1.
#
# Classes with zero samples receive weight 0.
# ==========================================================

nonzero_counts = [

    combined_counts[class_id]

    for class_id in range(
        NUM_CLASSES
    )

    if combined_counts[class_id] > 0
]


average_count = (
    sum(nonzero_counts)
    / len(nonzero_counts)
)


raw_weights = []


for class_id in range(
    NUM_CLASSES
):

    count = combined_counts[
        class_id
    ]

    if count == 0:

        weight = 0.0

    else:

        weight = math.sqrt(
            average_count
            / count
        )

    raw_weights.append(
        weight
    )


active_weights = [
    weight
    for weight in raw_weights
    if weight > 0
]


weight_mean = (
    sum(active_weights)
    / len(active_weights)
)


normalized_weights = [

    (
        weight / weight_mean
        if weight > 0
        else 0.0
    )

    for weight in raw_weights
]


# ==========================================================
# DISPLAY WEIGHTS
# ==========================================================

print(
    "\n"
    + "=" * 80
)

print("SUGGESTED SQRT INVERSE-FREQUENCY WEIGHTS")
print("=" * 80)


for class_id in range(
    NUM_CLASSES
):

    print(
        f"{class_id:2d} "
        f"{CLASS_NAMES[class_id]:18s} | "
        f"count={combined_counts[class_id]:6d} | "
        f"weight={normalized_weights[class_id]:.4f}"
    )


print(
    "\nPython list:"
)

print(
    "["
    +
    ", ".join(
        f"{weight:.4f}"
        for weight
        in normalized_weights
    )
    +
    "]"
)


# ==========================================================
# IMPORTANT WARNINGS
# ==========================================================

print(
    "\n"
    + "=" * 80
)

print("CHECKS")
print("=" * 80)


if combined_counts[14] == 0:

    print(
        "❌ ERROR: No ambulance objects found."
    )

else:

    print(
        f"✅ Ambulance objects found: "
        f"{combined_counts[14]}"
    )


if combined_counts[13] == 0:

    print(
        "⚠️ Class 13 (Other) has zero "
        "training examples."
    )

    print(
        "   Its class-loss weight will remain 0."
    )


if ambulance_counts[14] > 0:

    print(
        "✅ Ambulance correctly mapped "
        "to class 14."
    )


wrong_ambulance_classes = [

    class_id

    for class_id, count
    in ambulance_counts.items()

    if (
        class_id != 14
        and count > 0
    )
]


if wrong_ambulance_classes:

    print(
        "❌ Unexpected classes in "
        "ambulance_v4:",
        wrong_ambulance_classes
    )

else:

    print(
        "✅ ambulance_v4 contains only "
        "class 14 objects."
    )


print("=" * 80)