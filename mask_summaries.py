import json
import random

# === CONFIGURATION ===
INPUT_FILE = "all_problems_cleaned_with_source.json"
OUTPUT_FILE = "all_problems_with_masked_summary.json"
MASK_TOKEN = "[MASK]"
MASK_PROPORTION = 0.15  # Mask ~15% of words

def mask_random_words(text, proportion=0.15):
    words = text.split()
    n = len(words)
    k = max(1, int(n * proportion))  # number of words to mask

    mask_indices = sorted(random.sample(range(n), k))
    for idx in mask_indices:
        words[idx] = MASK_TOKEN
    return " ".join(words)

# === PROCESSING ===
with open(INPUT_FILE, "r") as f:
    data = json.load(f)

for obj in data:
    if "solution_summary" in obj and obj["solution_summary"]:
        obj["masked_summary"] = mask_random_words(obj["solution_summary"], MASK_PROPORTION)

# === OUTPUT ===
with open(OUTPUT_FILE, "w") as f:
    json.dump(data, f, indent=2)

print(f"✅ Done! Masked summaries written to: {OUTPUT_FILE}")
