from datasets import load_dataset, DatasetDict

# Load the full dataset
ds = load_dataset("AI-MO/NuminaMath-1.5")

# Filter function to keep only integer answers
def is_integer_answer(example):
    ans = example.get("answer", None)
    if ans is None:
        return False
    if isinstance(ans, int):
        return True
    if isinstance(ans, str):
        ans = ans.strip()
        if ans.startswith("-"):
            ans = ans[1:]
        return ans.isdigit()
    return False

# Apply filtering
int_ds = ds["train"].filter(is_integer_answer)

# Sanity check
total = len(int_ds)
print(f"Filtered dataset has {total} examples with integer answers.")

# Split sizes
test_size = 1000
val_size = 100
train_size = total - test_size - val_size

# Shuffle and split
shuffled = int_ds.shuffle(seed=42)
train_split = shuffled.select(range(0, train_size))
val_split = shuffled.select(range(train_size, train_size + val_size))
test_split = shuffled.select(range(train_size + val_size, train_size + val_size + test_size))

# Combine into DatasetDict
new_splits = DatasetDict({
    "train": train_split,
    "validation": val_split,
    "test": test_split
})

# Save to disk
new_splits.save_to_disk("numina_integer_splits")
