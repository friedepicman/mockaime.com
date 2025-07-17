import json
import random

# === CONFIGURATION ===
INPUT_PATH = "all_problems_cleaned_with_source.json"
OUTPUT_PATH = "all_problems_with_masked_summary.json"
MASK_TOKEN = "[MASK]"
MIN_WORDS = 6           # Minimum words required in summary to be maskable
MASK_RANGE = (3, 8)     # Randomly mask 3–8 words

# === Function to mask summary ===
def mask_summary(summary, mask_token=MASK_TOKEN, min_words=MIN_WORDS, mask_range=MASK_RANGE):
    words = summary.split()
    if len(words) < min_words:
        return None

    max_start = len(words) - mask_range[1]
    if max_start <= 0:
        return None

    start = random.randint(0, max_start)
    mask_len = random.randint(*mask_range)
    end = start + mask_len

    masked_span = [mask_token] * mask_len
    masked_words = words[:start] + masked_span + words[end:]
    return " ".join(masked_words)

# === Load JSON ===
with open(INPUT_PATH, "r", encoding="utf-8") as f:
    problems = json.load(f)

# === Apply masking ===
for problem in problems:
    summary = problem.get("solution_summary", "")
    if isinstance(summary, str):
        masked = mask_summary(summary)
        if masked:
            problem["masked_summary"] = masked

# === Save updated JSON ===
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(problems, f, indent=2)

print(f"✅ Masked summaries added and saved to: {OUTPUT_PATH}")
