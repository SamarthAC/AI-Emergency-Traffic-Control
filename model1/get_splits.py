from datasets import get_dataset_split_names

splits = get_dataset_split_names("iisc-aim/BMD-45")
print(splits)  # Output: ['train', 'val']