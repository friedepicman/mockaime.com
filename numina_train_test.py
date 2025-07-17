from datasets import load_dataset, DatasetDict

# Load the full dataset
ds = load_dataset("AI-MO/NuminaMath-CoT")

# Calculate sizes
total = len(ds["train"])
test_size = 10000
val_size = 1000
train_size = total - test_size - val_size

# Shuffle and split
ds_shuffled = ds["train"].shuffle(seed=42)
train_split = ds_shuffled.select(range(0, train_size))
val_split = ds_shuffled.select(range(train_size, train_size + val_size))
test_split = ds_shuffled.select(range(train_size + val_size, train_size + val_size + test_size))

# Bundle the splits
new_splits = DatasetDict({
    "train": train_split,
    "validation": val_split,
    "test": test_split
})

# Save splits locally
new_splits.save_to_disk("numina_splits")
