from datasets import load_dataset

# Load the entire dataset (NuminaMath only has a 'train' split)
ds = load_dataset("AI-MO/NuminaMath-1.5", split="train")

# Print some basic stats
print(f"Total examples: {len(ds):,}")
print("Available fields:", ds.column_names)

# Optionally save to disk for reuse
ds.save_to_disk("numina_1.5_full")
