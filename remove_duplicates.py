import json

INPUT_FILE = "combined_problems.json"
OUTPUT_FILE = "combined_with_answers.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    problems = json.load(f)

seen_links = set()
unique_problems = []

for prob in problems:
    link = prob.get("link")
    if link and link not in seen_links:
        seen_links.add(link)
        unique_problems.append(prob)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(unique_problems, f, indent=2, ensure_ascii=False)

print(f"✅ Deduplicated: {len(unique_problems)} unique problems saved to {OUTPUT_FILE}")
