from datasets import load_dataset

ds = load_dataset(
    "iisc-aim/BMD-45",
    split="train",
    streaming=True
)

sample = next(iter(ds))

print(sample)
print(sample.keys())