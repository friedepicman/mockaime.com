import json
import re

def extract_year_from_source(source):
    match = re.search(r"\b(19\d{2}|20\d{2})\b", source)
    return int(match.group()) if match else None

def main():
    with open("difficulty_updated_bro_please.json") as f:
        problems = json.load(f)

    adjusted = 0
    updated_years = 0

    for prob in problems:
        source = prob.get("source", "")
        extracted_year = extract_year_from_source(source)

        if extracted_year:
            prob["year"] = extracted_year
            updated_years += 1

            # Only adjust difficulty if it's a number
            if isinstance(prob.get("difficulty"), (int, float)):
                original = prob["difficulty"]
                if extracted_year < 2005:
                    prob["difficulty"] = max(0, original - 1.0)
                    adjusted += 1
                elif extracted_year < 2015:
                    prob["difficulty"] = max(0, original - 0.5)
                    adjusted += 1

    with open("bro_please_please.json", "w") as f:
        json.dump(problems, f, indent=2)

    print(f"✅ Updated year for {updated_years} problems.")
    print(f"✅ Adjusted difficulty for {adjusted} problems.")

if __name__ == "__main__":
    main()
