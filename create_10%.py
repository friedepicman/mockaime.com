from datasets import load_from_disk, DatasetDict
import random

SEED = 42
random.seed(SEED)

# Load previously split dataset from disk
full_ds = load_from_disk("numina_integer_splits")  # change if your folder is named differently

# Get existing test and validation sets
test_set = full_ds["test"]
val_set = full_ds["validation"]

# Take 10% of training data
train_full = full_ds["train"]
train_10pct_size = int(0.10 * len(train_full))
train_10pct = train_full.shuffle(seed=SEED).select(range(train_10pct_size))

# Create new 10% dataset
new_ds = DatasetDict({
    "train": train_10pct,
    "validation": val_set,
    "test": test_set
})

# Save to disk
new_ds.save_to_disk("numinamath_integer_split_10pct")

print("✅ Created 10% dataset.")
print(f"Train: {len(train_10pct)} | Val: {len(val_set)} | Test: {len(test_set)}")
