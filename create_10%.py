from datasets import load_from_disk, DatasetDict
import random

SEED = 42
random.seed(SEED)

# Load full dataset with only one split "train"
full_ds = load_from_disk("numina_1.5_full")  # change if needed

train_full = full_ds

# Shuffle full dataset
train_shuffled = train_full.shuffle(seed=SEED)

# Define sizes for splits
test_size = 1000
val_size = 100
train_size = len(train_shuffled) - test_size - val_size

# Create splits
train_split = train_shuffled.select(range(0, train_size))
val_split = train_shuffled.select(range(train_size, train_size + val_size))
test_split = train_shuffled.select(range(train_size + val_size, train_size + val_size + test_size))

# Optional: take 1% of train for a smaller training set
train_1pct_size = int(0.10 * len(train_split))
train_1pct = train_split.select(range(train_1pct_size))

# Create DatasetDict with splits
new_ds = DatasetDict({
    "train": train_1pct,     # or use train_split if you want full training set
    "validation": val_split,
    "test": test_split,
})

# Save new splits to disk
new_ds.save_to_disk("numinamath_1.5_split_10pct")

print("✅ Created 1% dataset with new splits.")
print(f"Train: {len(train_1pct)} | Val: {len(val_split)} | Test: {len(test_split)}")
