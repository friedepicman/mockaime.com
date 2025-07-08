import json

# Load your JSON file
with open("all_problems_with_all_difficulties.json", "r") as f:
    problems = json.load(f)

usable_count = 0
invalid_difficulty_count = 0
total_count = 0

for p in problems:
    diff = p.get("difficulty")
    answer_type = p.get("answer_type", "").strip().lower()

    try:
        d = float(diff)
    except (ValueError, TypeError):
        invalid_difficulty_count += 1
        continue

    # Count only if difficulty is in 3–7 and answer type is "positive integer <= 1000"
    if 3 <= d <= 7:
        total_count += 1
        if answer_type == "positive integer <= 1000":
            usable_count += 1

print(f"Total usable problems with difficulty 3–7: {total_count}")
print(f"Usable problems with answer_type = 'positive integer <= 1000': {usable_count}")
print(f"Problems with invalid difficulty: {invalid_difficulty_count}")
