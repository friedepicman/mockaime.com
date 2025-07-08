import json
from datetime import datetime

CURRENT_YEAR = 2025

def get_difficulty_amc8(num):
    if num <= 10: return 1
    if num <= 17: return 1.5
    if num <= 23: return 2
    return 2.5

def get_difficulty_amc10(num):
    if num <= 5: return 1
    if num <= 9: return 1.5
    if num <= 14: return 2
    if num <= 17: return 2.5
    if num <= 20: return 3
    if num <= 22: return 3.5
    if num <= 24: return 4
    return 4.5

def get_difficulty_amc12(num):
    if num <= 5: return 1.5
    if num <= 10: return 2
    if num <= 14: return 2.5
    if num <= 17: return 3
    if num <= 20: return 3.5
    if num == 21: return 4
    if num == 22: return 4.5
    if num == 23: return 5
    if num == 24: return 5.5
    return 6

def get_difficulty_aime(num):
    if num <= 3: return 3
    if num <= 5: return 3.5
    if num <= 8: return 4
    if num <= 10: return 4.5
    if num == 11: return 5
    if num == 12: return 5.5
    if num == 13: return 6
    if num == 14: return 6.5
    return 7

def adjust_difficulty(base, year):
    age = CURRENT_YEAR - year
    if age <= 8:
        return base
    elif age <= 16:
        return max(1, base - 0.5)
    else:
        return max(1, base - 1)
    

def tag_and_save(input_file, output_file, get_base_difficulty):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for p in data:
        base = get_base_difficulty(p["problem_number"])
        difficulty = adjust_difficulty(base, p["year"])
        p["difficulty"] = difficulty

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ {output_file} updated with difficulty tags.")


def main():
    tag_and_save("amc8_problems_with_solutions.json", "amc8_tagged.json", get_difficulty_amc8)
    tag_and_save("amc10_problems_with_solutions.json", "amc10_tagged.json", get_difficulty_amc10)
    tag_and_save("amc12_problems_with_solutions.json", "amc12_tagged.json", get_difficulty_amc12)
    tag_and_save("aime_problems_with_solutions.json", "aime_tagged.json", get_difficulty_aime)

if __name__ == "__main__":
    main()
