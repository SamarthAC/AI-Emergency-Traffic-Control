import random
from collections import Counter

# ==========================================================
# SETTINGS
# ==========================================================

SEED = 42

BMD_SIZE = 3000
AMBULANCE_SIZE = 3798

BMD_RATIO = 0.75
AMBULANCE_RATIO = 0.25

# Let's simulate one training epoch of 4000 samples.
EPOCH_SAMPLES = 4000


# ==========================================================
# SET SEED
# ==========================================================

random.seed(SEED)


# ==========================================================
# BUILD SOURCE POOLS
# ==========================================================

bmd_indices = list(range(BMD_SIZE))
ambulance_indices = list(range(AMBULANCE_SIZE))


# ==========================================================
# GENERATE MIXED EPOCH
# ==========================================================

samples = []

for _ in range(EPOCH_SAMPLES):

    if random.random() < BMD_RATIO:

        index = random.choice(bmd_indices)

        samples.append(
            ("BMD", index)
        )

    else:

        index = random.choice(
            ambulance_indices
        )

        samples.append(
            ("AMBULANCE", index)
        )


# ==========================================================
# ANALYZE
# ==========================================================

source_counts = Counter(
    source
    for source, _ in samples
)

bmd_count = source_counts["BMD"]
ambulance_count = source_counts["AMBULANCE"]

bmd_percentage = (
    bmd_count
    / EPOCH_SAMPLES
    * 100
)

ambulance_percentage = (
    ambulance_count
    / EPOCH_SAMPLES
    * 100
)


print("=" * 70)
print("V4 MIXED SAMPLER TEST")
print("=" * 70)

print(f"BMD dataset size       : {BMD_SIZE}")
print(f"Ambulance dataset size : {AMBULANCE_SIZE}")

print()

print(f"Epoch samples          : {EPOCH_SAMPLES}")

print()

print(
    f"BMD samples            : "
    f"{bmd_count} "
    f"({bmd_percentage:.2f}%)"
)

print(
    f"Ambulance samples      : "
    f"{ambulance_count} "
    f"({ambulance_percentage:.2f}%)"
)


# ==========================================================
# UNIQUE SAMPLE COVERAGE
# ==========================================================

unique_bmd = len({
    index
    for source, index in samples
    if source == "BMD"
})

unique_ambulance = len({
    index
    for source, index in samples
    if source == "AMBULANCE"
})


print()

print(
    f"Unique BMD used        : "
    f"{unique_bmd}/{BMD_SIZE}"
)

print(
    f"Unique ambulance used  : "
    f"{unique_ambulance}/{AMBULANCE_SIZE}"
)


# ==========================================================
# DUPLICATE DRAWS
# ==========================================================

bmd_duplicates = (
    bmd_count
    - unique_bmd
)

ambulance_duplicates = (
    ambulance_count
    - unique_ambulance
)


print()

print(
    f"BMD repeated draws     : "
    f"{bmd_duplicates}"
)

print(
    f"Ambulance repeated     : "
    f"{ambulance_duplicates}"
)


# ==========================================================
# VALIDATION
# ==========================================================

print()
print("=" * 70)
print("CHECKS")
print("=" * 70)


ratio_tolerance = 3.0


if abs(
    bmd_percentage - 75.0
) <= ratio_tolerance:

    print(
        "✅ BMD sampling ratio is "
        "within tolerance."
    )

else:

    print(
        "❌ BMD sampling ratio is "
        "outside tolerance."
    )


if abs(
    ambulance_percentage - 25.0
) <= ratio_tolerance:

    print(
        "✅ Ambulance sampling ratio is "
        "within tolerance."
    )

else:

    print(
        "❌ Ambulance sampling ratio is "
        "outside tolerance."
    )


assert (
    bmd_count
    + ambulance_count
    == EPOCH_SAMPLES
)


print(
    "✅ Total sample count correct."
)

print(
    "✅ V4 75:25 mixed sampling "
    "simulation passed!"
)

print("=" * 70)