import json
import re

# Difficulty maps for SMT categories
difficulty_map = {
    "Team": {i: d for i, d in enumerate([2, 2.5, 3, 3.5, 4, 4.5, 5, 5, 5.5, 5.5, 6, 6, 6.5, 6.5, 7], 1)},
    "General": {i: d for i, d in enumerate(
        [1.5, 1.5, 1.5, 1.5, 1.5, 2, 2, 2, 2, 2, 2.5, 2.5, 2.5, 2.5, 3, 3, 3, 3, 3.5, 3.5, 3.5, 3.5, 4, 4, 4.5], 1)},
    "Guts": {i: d for i, d in enumerate(
        [2.5, 3, 3.5, 2.5, 3, 3.5, 2.5, 3, 3.5, 3, 3.5, 4, 4, 4.5, 5, 4.5, 5, 5.5, 5.5, 6, 6.5, 6, 6.5, 7, 6.5, 7, 7.5], 1)},
    "Geo/Discrete/Alg/Calc/Adv": {i: d for i, d in enumerate(
        [2.5, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5], 1)},
    "Tiebreaker": {1: 2.5, 2: 4, 3: 5.5},
}

category_keywords = {
    "team": "Team",
    "general": "General",
    "guts": "Guts",
    "tiebreaker": "Tiebreaker",
    "tie breaker": "Tiebreaker",
    "geometry": "Geo/Discrete/Alg/Calc/Adv",
    "discrete": "Geo/Discrete/Alg/Calc/Adv",
    "algebra": "Geo/Discrete/Alg/Calc/Adv",
    "calculus": "Geo/Discrete/Alg/Calc/Adv",
    "advanced topics": "Geo/Discrete/Alg/Calc/Adv",
    "adv": "Geo/Discrete/Alg/Calc/Adv",
}

def parse_smt(source, title):
    source = source or ""
    title = title or ""
    combined = f"{source} {title}".lower()

    if "integration bee" in combined:
        return None, None

    category_found = None
    for key, cat in category_keywords.items():
        if key in combined:
            category_found = cat
            break
    if category_found is None:
        category_found = "General"

    m = re.search(r"#(\d+)", combined)
    if m:
        number = int(m.group(1))
        return category_found, number

    m = re.search(r"problem\s*(\d+)", combined)
    if m:
        number = int(m.group(1))
        return category_found, number

    nums = re.findall(r"\b(\d+)\b", combined)
    if nums:
        number = int(nums[0])
        return category_found, number

    return None, None

def main():
    with open("difficulty_updated_bro_please.json") as f:
        problems = json.load(f)

    matched = 0
    unmatched = []
    smt_problems = []

    for prob in problems:
        source = prob.get("source") or ""
        title = prob.get("title") or ""

        if "SMT" not in source:
            continue

        category, number = parse_smt(source, title)
        if category and number:
            diff_map = difficulty_map.get(category)
            if diff_map is None:
                unmatched.append((title, source))
                continue
            diff = diff_map.get(number)
            if diff is not None:
                prob["difficulty"] = diff
                matched += 1
                smt_problems.append(prob)
            else:
                unmatched.append((title, source))
        else:
            unmatched.append((title, source))

    with open("smt_problems_with_difficulty.json", "w") as f:
        json.dump(smt_problems, f, indent=2)

    print(f"✅ Assigned difficulty to {matched} SMT problems.")
    if unmatched:
        print(f"⚠️ {len(unmatched)} SMT problems could not be matched:")
        for title, src in unmatched:
            print(f"- {title}: {src}")
    else:
        print("🎉 All SMT problems matched successfully.")

if __name__ == "__main__":
    main()
