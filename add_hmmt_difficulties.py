import json
import re

# === HMMT difficulty mappings ===
difficulty_map = {
    "HMMT General": {1: 1, 2: 2, 3: 3, 4: 4, 5: 4.5, 6: 5, 7: 5.5, 8: 6, 9: 6.5, 10: 7},
    "HMMT Theme": {1: 2, 2: 3, 3: 4, 4: 4.5, 5: 5, 6: 5.5, 7: 6, 8: 6.5, 9: 7, 10: 7.5},
    "HMMT Guts": {
        1: 1.5, 2: 2, 3: 2.5, 4: 2, 5: 2.5, 6: 3, 7: 2.5, 8: 3, 9: 3.5, 10: 3.5,
        11: 4, 12: 3, 13: 3.5, 14: 4, 15: 3, 16: 3.5, 17: 4.5, 18: 5, 19: 5.5,
        20: 6, 21: 6.5, 22: 5.5, 23: 6, 24: 6.5, 25: 6, 26: 6.5, 27: 7, 28: 6.5,
        29: 7, 30: 7.5, 31: 6.5, 32: 7, 33: 7.5
    },
    "HMMT Team": {1: 2.5, 2: 3, 3: 3.5, 4: 4, 5: 4, 6: 4.5, 7: 5, 8: 5.5, 9: 6, 10: 6.5},
    "HMMT General Part 1": {1: 2, 2: 3, 3: 3.5, 4: 4, 5: 4, 6: 4, 7: 4, 8: 4.5, 9: 4.5, 10: 5},
    "HMMT General Part 2": {1: 2.5, 2: 3, 3: 3.5, 4: 4, 5: 4, 6: 4.5, 7: 5, 8: 5.5, 9: 6, 10: 6.5},
}

# Keywords for identifying rounds
keywords = ["General", "Theme", "Guts", "Team"]

# Handle HMMT General parts specifically
hmmtspecial = ["General Part 1", "General Part 2"]

def parse_hmmt_subject_and_number(source, title):
    if "HMMT" not in source:
        return None, None
    
    text = source.split("same as")[0].strip()

    # Check for General Part 1/2 first
    for part in hmmtspecial:
        if part.lower() in text.lower():
            m = re.search(r"(?:#|P)?(\d+)", text)
            if m:
                return f"HMMT {part}", int(m.group(1))

    # Search for keywords and problem number
    tokens = text.split()
    subject = None
    number = None

    for i, word in enumerate(tokens):
        # Case insensitive match for keywords
        for kw in keywords:
            if kw.lower() == word.lower():
                subject = "HMMT " + kw
                # Look ahead 1-3 tokens for problem number
                for j in range(i+1, min(i+4, len(tokens))):
                    m = re.search(r"(?:#|P)?(\d+)", tokens[j])
                    if m:
                        number = int(m.group(1))
                        break
                break
        if subject is not None:
            break

    # Fallback to title if needed
    if subject is None or number is None:
        m = re.search(r"(General|Theme|Guts|Team).*?(?:#|P)?(\d+)", title, re.I)
        if m:
            subject = "HMMT " + m.group(1).title()
            number = int(m.group(2))

    # Tiebreaker check
    if subject and re.search(r"tie", text, re.I):
        subject += " Tiebreaker"

    return subject, number

def assign_hmmt_difficulties(problems):
    matched = 0
    unmatched = []

    for prob in problems:
        source = prob.get("source", "")
        title = prob.get("title", "")

        if "HMMT" not in source:
            continue

        subject, number = parse_hmmt_subject_and_number(source, title)
        if subject and number:
            diff = difficulty_map.get(subject, {}).get(number)
            if diff is not None:
                prob["difficulty"] = diff
                matched += 1
            else:
                unmatched.append((title, source))
        else:
            unmatched.append((title, source))

    total = sum(1 for p in problems if "HMMT" in p.get("source", ""))
    print(f"✅ Assigned difficulty to {matched} / {total} HMMT problems.")
    if unmatched:
        print(f"⚠️ {len(unmatched)} HMMT problems could not be matched:")
        for title, src in unmatched:
            print(f"- {title}: {src}")
    else:
        print("🎉 All HMMT problems matched successfully.")

    return problems

if __name__ == "__main__":
    with open("all_problems_with_sources.json") as f:
        problems = json.load(f)

    updated = assign_hmmt_difficulties(problems)

    with open("hmmt_problems_with_difficulty.json", "w") as f:
        json.dump(updated, f, indent=2)
