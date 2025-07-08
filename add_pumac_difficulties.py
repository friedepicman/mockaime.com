import json
import re

# === Difficulty mappings for PUMaC ===
difficulty_map = {
    "division a": {
        "algebra": {i: d for i, d in enumerate([3, 3, 3.5, 3.5, 4, 4.5, 5, 5.5, 6, 6.5], 1)},
        "combinatorics": {i: d for i, d in enumerate([3, 3, 3.5, 3.5, 4, 4.5, 5, 5.5, 6, 6.5], 1)},
        "geometry": {i: d for i, d in enumerate([3, 3, 3.5, 3.5, 4, 4.5, 5, 5.5, 6, 6.5], 1)},
        "number theory": {i: d for i, d in enumerate([3, 3, 3.5, 3.5, 4, 4.5, 5, 5.5, 6, 6.5], 1)},
    },
    "division b": {
        "algebra": {i: d for i, d in enumerate([1, 1.5, 2, 2.5, 2.5, 3, 3.5, 3.5, 4, 4], 1)},
        "combinatorics": {i: d for i, d in enumerate([1, 1.5, 2, 2.5, 2.5, 3, 3.5, 3.5, 4, 4], 1)},
        "geometry": {i: d for i, d in enumerate([1, 1.5, 2, 2.5, 2.5, 3, 3.5, 3.5, 4, 4], 1)},
        "number theory": {i: d for i, d in enumerate([1, 1.5, 2, 2.5, 2.5, 3, 3.5, 3.5, 4, 4], 1)},
    },
    "team": {
        1: 2.5, 2: 3, 3: 3.5, 4: 4, 5: 4.5, 6: 4.5, 7: 5, 8: 5, 9: 5,
        10: 5.5, 11: 5.5, 12: 6, 13: 6.5, 14: 7, 15: 7.5
        # 16+ handled dynamically
    }
}

# Normalize subject keywords
subject_aliases = {
    "alg": "algebra",
    "algebra": "algebra",
    "combinatorics": "combinatorics",
    "combo": "combinatorics",
    "number theory": "number theory",
    "nt": "number theory",
    "geometry": "geometry"
}

def parse_pumac(source, title):
    source = source or ""
    title = title or ""
    text = (source + " " + title).lower()

    # Check if it's team round with problem number
    team_match = re.search(r"team(?: problem)?\s*#?(\d+)", text)
    if team_match:
        number = int(team_match.group(1))
        return "team", None, number

    # Determine division A or B (default A)
    if "division b" in text or "b division" in text or re.search(r"\bdivision\s*b\b", text):
        division = "division b"
    else:
        division = "division a"

    # Try to find subject keyword in text
    subject = None
    for key in subject_aliases:
        if key in text:
            subject = subject_aliases[key]
            break
    if not subject:
        # fallback: check title
        for key in subject_aliases:
            if key in title.lower():
                subject = subject_aliases[key]
                break

    # Find first A# or B# problem number in source/title
    # Pattern matches a or b followed by number, or number followed by a or b
    match = re.search(r"\b([ab]?)(\d+)([ab]?)\b", text)
    number = None
    if match:
        letter1, num_str, letter2 = match.groups()
        number = int(num_str)
        # If no division yet, infer from letter
        if letter1 == "b" or letter2 == "b":
            division = "division b"
        elif letter1 == "a" or letter2 == "a":
            division = "division a"
    else:
        # fallback: try just a number preceded by # or problem
        match_num = re.search(r"(?:#|problem\s*)(\d+)", text)
        if match_num:
            number = int(match_num.group(1))

    return division, subject, number

def get_difficulty(division, subject, number):
    if division == "team":
        # Use team difficulties with dynamic extension beyond 15
        base_map = difficulty_map["team"]
        if number <= 15:
            return base_map.get(number)
        else:
            # Add 0.5 for each problem beyond 15
            extra = 0.5 * (number - 15)
            return base_map[15] + extra

    # If no subject or division unknown, can't assign
    if division not in difficulty_map or subject not in difficulty_map[division]:
        return None
    if number is None:
        return None

    # Cap number at max defined difficulty index
    subject_map = difficulty_map[division][subject]
    max_num = max(subject_map.keys())
    capped_num = number if number <= max_num else max_num
    return subject_map.get(capped_num)

def main():
    with open("all_problems_with_sources.json") as f:
        problems = json.load(f)

    matched = 0
    unmatched = []

    for prob in problems:
        source = prob.get("source")
        title = prob.get("title")

        # Only process PUMaC problems
        if not source or "pumac" not in source.lower():
            continue

        division, subject, number = parse_pumac(source, title)

        # For team problems division is "team"
        if division not in difficulty_map and division != "team":
            unmatched.append((title, source))
            continue

        diff = get_difficulty(division, subject, number)

        if diff is not None:
            prob["difficulty"] = diff
            matched += 1
        else:
            unmatched.append((title, source))

    with open("pumac_problems_with_difficulty.json", "w") as f:
        json.dump(problems, f, indent=2)

    total_pumac = sum(1 for p in problems if p.get("source") and "pumac" in p.get("source").lower())
    print(f"✅ Assigned difficulty to {matched} / {total_pumac} PUMaC problems.")
    if unmatched:
        print(f"⚠️ {len(unmatched)} PUMaC problems could not be matched:")
        for title, src in unmatched:
            print(f"- {title}: {src}")
    else:
        print("🎉 All PUMaC problems matched successfully.")

if __name__ == "__main__":
    main()
