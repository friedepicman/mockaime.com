import re

difficulty_map = {
    "Algebra": {1: 1.5, 2: 2, 3: 2.5, 4: 3, 5: 3.5, 6: 4, 7: 5, 8: 5.5, 9: 6, 10: 7},
    "Geometry": {1: 1.5, 2: 2, 3: 2.5, 4: 3, 5: 3.5, 6: 4, 7: 5, 8: 5.5, 9: 6, 10: 7},
    "NT": {1: 1.5, 2: 2, 3: 2.5, 4: 3, 5: 3.5, 6: 4, 7: 5, 8: 5.5, 9: 6, 10: 7},
    "Discrete": {1: 1.5, 2: 2, 3: 2.5, 4: 3, 5: 3.5, 6: 4, 7: 5, 8: 5.5, 9: 6, 10: 7},
    "Analysis": {1: 1.5, 2: 2, 3: 2.5, 4: 3, 5: 3.5, 6: 4, 7: 5, 8: 5.5, 9: 6, 10: 7},
    "Team": {1: 1.5, 2: 2, 3: 2.5, 4: 3, 5: 3.5, 6: 4, 7: 5, 8: 5.5, 9: 6, 10: 7},
    "General": {
        **{i: 1 for i in range(1, 6)},
        **{i: 1.5 for i in range(6, 10)},
        **{i: 2 for i in range(10, 13)},
        **{i: 2.5 for i in range(13, 15)},
        **{i: 3 for i in range(15, 18)},
        **{i: 3.5 for i in range(18, 20)},
        20: 4, 21: 4.5, 22: 5, 23: 5.5, 24: 6, 25: 6.5
    }
}

def parse_subject_and_number(trimmed):
    subject_keywords = ["Algebra", "Geometry", "NT", "Discrete", "Analysis", "Team", "General", "Guts", "Individual"]
    subject_aliases = {
        "Individual": "General",
        "Team Round": "Team",
    }

    subject = None
    for subj in subject_keywords + list(subject_aliases.keys()):
        if subj in trimmed:
            subject = subject_aliases.get(subj, subj)
            break

    candidates = re.findall(r"#(\d+)|p(\d+)|\b(\d{1,2})\b", trimmed)
    nums = [int(n) for tup in candidates for n in tup if n]
    nums = [n for n in nums if n < 100]
    number = nums[0] if nums else None

    return subject, number

failures = [
    "2023 BMT General #4: BMT 2023 same as Geometry 1 #4",
    "2023 BMT General #7: BMT 2023 same as Discrete 1 #7",
    "2023 BMT General #8: BMT 2023 same as Discrete 1 #8",
    "2023 BMT General #9: BMT 2023 same as Discrete 1 #9",
    "2023 BMT General #12: BMT 2023 same as Algebra 3 #12",
    "2023 BMT General #16: BMT 2023 same as Discrete 3 #16"
]

matched = 0
for failure in failures:
    # Split into title and source
    if ": " not in failure:
        print(f"⚠️ Skipping malformed failure: {failure}")
        continue

    title, source = failure.split(": ", 1)

    # Find all 'BMT' positions
    bmt_positions = [m.start() for m in re.finditer("BMT", source)]
    if len(bmt_positions) < 2:
        print(f"⚠️ Cannot fix '{source}': fewer than 2 'BMT' occurrences.")
        continue

    trimmed = source[:bmt_positions[1]].strip()

    # Append problem number from title to trimmed (in case it's lost)
    num_match = re.search(r"#(\d+)", title)
    if num_match:
        trimmed += f" #{num_match.group(1)}"

    subject, number = parse_subject_and_number(trimmed)

    difficulty = None
    if subject in difficulty_map and number in difficulty_map[subject]:
        difficulty = difficulty_map[subject][number]

    print(f"Title: {title}")
    print(f"Source: {source}")
    print(f"Trimmed: '{trimmed}'")
    print(f"Parsed subject: {subject}, number: {number}")
    print(f"Assigned difficulty: {difficulty}")
    print("---")

    if difficulty is not None:
        matched += 1

print(f"✅ Matched difficulties for {matched} out of {len(failures)} failures.")
