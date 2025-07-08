import json
import re

# === Difficulty mappings ===
difficulty_map = {
    "Algebra": {i: d for i, d in enumerate([1.5, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6.5, 7], 1)},
    "Combinatorics": {i: d for i, d in enumerate([1.5, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6.5, 7], 1)},
    "Geometry": {i: d for i, d in enumerate([1.5, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6.5, 7], 1)},
    "NT": {i: d for i, d in enumerate([1.5, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6.5, 7], 1)},
    "Number Theory": {i: d for i, d in enumerate([1.5, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6.5, 7], 1)},
    "Team": {i: d for i, d in enumerate([3, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8], 1)},
    "Team-15": {i: d for i, d in enumerate(
        [2, 2, 2.5, 2.5, 3, 3.5, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5], 1)},
    "Tiebreaker": {1: 4, 2: 4.5, 3: 5},
}

# === Aliases and keywords ===
aliases = {
    "Number Theory": "NT",
    "Combo": "Combinatorics",
    "Combo/CS": "Combinatorics",
    "Combinatorics and Computer Science": "Combinatorics",
    "Computer Science": "Combinatorics",
    "CS": "Combinatorics",
    "C/CS": "Combinatorics",
    "TCS": "Combinatorics",
    "A/NT": "NT",
    "Algebra/NT": "NT",
    "Alg": "Algebra",
    "NT": "NT",
    "Team Round": "Team",
    "Individual": "General",
}

keywords = set([
    "Algebra", "Combinatorics", "Geometry", "NT", "Number Theory",
    "Team", "Tiebreaker", "General"
])

def normalize_token(token):
    t = token.strip(",.").capitalize()
    return aliases.get(t, t)

def parse_source_subject_and_number(source, title):
    if "CMIMC" not in source:
        return None, None

    # Skip Integration Bee or Estimation problems
    if any(skip in source.lower() or skip in title.lower()
           for skip in ["integration bee", "estimation"]):
        return None, None

    text = source.split("same as")[0].strip()

    # Normalize known aliases in text
    for alias, canonical in aliases.items():
        text = re.sub(r"\b" + re.escape(alias) + r"\b", canonical, text, flags=re.I)

    tokens = text.split()
    subject = None
    number = None

    # First try normal token-based matching
    for i, token in enumerate(tokens):
        norm_token = normalize_token(token)
        if norm_token in difficulty_map:
            subject = norm_token
            # Search for number
            for j in range(i + 1, min(i + 4, len(tokens))):
                m = re.search(r"(?:#|P)?(\d+)", tokens[j])
                if m:
                    number = int(m.group(1))
                    break
            break

    # If failed, try full-string fallback regex
    if subject is None or number is None:
        pattern = re.compile(
            r"(Algebra|Combinatorics(?: & Computer Science| and Computer Science)?|Geometry|NT|Number Theory|Team|Tiebreaker|General|Combo/CS|C/CS|TCS|A/NT|Algebra/NT)[^\d]*(\d+)",
            re.I
        )
        m = pattern.search(text)
        if m:
            subject_raw = m.group(1)
            subject = aliases.get(subject_raw.strip(), subject_raw.strip())
            number = int(m.group(2))

    # Final fallback: try title
    if subject is None or number is None:
        m = re.search(r"(Algebra|Combinatorics|Geometry|NT|Number Theory|Team|Tiebreaker|General)[^\d]*(\d+)", title, re.I)
        if m:
            subject_raw = m.group(1)
            subject = aliases.get(subject_raw.strip(), subject_raw.strip())
            number = int(m.group(2))

    if subject is None or number is None:
        return None, None

    # Handle tiebreakers
    if re.search(r"tie", text, re.I) or re.search(r"tie", title, re.I):
        subject = "Tiebreaker"

    # Handle Team-15 override (2019–2023)
    year_match = re.search(r"20\d{2}", source)
    year = int(year_match.group()) if year_match else None
    if subject == "Team" and year in {2019, 2020, 2021, 2022, 2023}:
        subject = "Team-15"

    return subject, number

def main():
    with open("all_problems_with_sources.json") as f:
        problems = json.load(f)

    matched = 0
    unmatched = []

    for prob in problems:
        source = prob.get("source", "")
        title = prob.get("title", "")

        if "CMIMC" not in source:
            continue

        subject, number = parse_source_subject_and_number(source, title)
        if subject and number:
            diff = difficulty_map.get(subject, {}).get(number)
            if diff is not None:
                prob["difficulty"] = diff
                matched += 1
            else:
                unmatched.append((title, source))
        else:
            unmatched.append((title, source))

    with open("cmimc_problems_with_difficulty.json", "w") as f:
        json.dump(problems, f, indent=2)

    total_cmimc = sum(1 for p in problems if "CMIMC" in p.get("source", ""))
    print(f"✅ Assigned difficulty to {matched} / {total_cmimc} CMIMC problems.")
    if unmatched:
        print(f"⚠️ {len(unmatched)} CMIMC problems could not be matched:")
        for title, src in unmatched:
            print(f"- {title}: {src}")
    else:
        print("🎉 All CMIMC problems matched successfully.")

if __name__ == "__main__":
    main()
