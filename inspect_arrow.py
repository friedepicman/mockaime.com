from datasets import Dataset, load_from_disk

# Update this path to where your Arrow dataset is stored
DATASET_PATH = "./numinamath_split_10pct"

print("🔍 Inspecting dataset...")

# Load the dataset (either a split or whole dataset folder)
dataset = load_from_disk(DATASET_PATH)

# If it's a DatasetDict (multiple splits), list and show each
if isinstance(dataset, dict) or hasattr(dataset, 'keys'):
    print(f"✅ Found splits: {list(dataset.keys())}")
    for split_name in dataset:
        split = dataset[split_name]
        print(f"\n📄 Split: {split_name}")
        print(f"📦 Number of rows: {len(split)}")
        print(f"🧱 Column names: {split.column_names}")
        print("🧪 First example:")
        print(split[0])
else:
    print(f"📦 Number of rows: {len(dataset)}")
    print(f"🧱 Column names: {dataset.column_names}")
    print("🧪 First example:")
    print(dataset[0])
