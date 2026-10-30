from datasets import load_dataset
from collections import Counter

ds = load_dataset(
    "iisc-aim/BMD-45",
    split="train",
    streaming=True
)

counter = Counter()

print("Reading first 100 samples...")

for i, sample in enumerate(ds):

    for category in sample["objects"]["categories"]:
        counter[category] += 1

    if i + 1 >= 100:
        break

print("\n===== CLASS DISTRIBUTION =====")

for category_id, count in sorted(counter.items()):
    print(f"Category {category_id}: {count}")

print("\nTotal annotations:", sum(counter.values()))