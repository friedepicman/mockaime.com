import json

input_file = "combined_problems.json"
output_file = "combined_problems.json"
remove_phrase = "Click to reveal hidden text Click to reveal hidden text "

with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

cleaned_count = 0
for problem in data:
    text = problem.get("solution", "")
    if text and text.startswith(remove_phrase):
        problem["solution"] = text[len(remove_phrase):].lstrip()
        cleaned_count += 1

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✅ Finished cleaning. Removed phrase from {cleaned_count} problems.")
print(f"💾 Cleaned data saved to {output_file}")
