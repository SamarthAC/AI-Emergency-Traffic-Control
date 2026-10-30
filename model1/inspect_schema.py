from datasets import load_dataset

ds = load_dataset(
    "iisc-aim/BMD-45",
    split="train",
    streaming=True
)

print("\n===== DATASET FEATURES =====")
print(ds.features)

print("\n===== FIRST SAMPLE =====")
sample = next(iter(ds))

print(sample.keys())

print("\n===== OBJECTS =====")
print(sample["objects"])

print("\n===== IMAGE =====")
print(sample["image"])