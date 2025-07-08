import json

# Load the punctuated CMIMC JSON (list of dicts with problems inside)
with open("cmimc_punctuated.json", "r") as f:
    cmimc_list = json.load(f)

# Load existing all problems JSON (list of problem dicts)
with open("problems.json", "r") as f:
    all_problems = json.load(f)

# Remove old CMIMC problems
all_problems = [p for p in all_problems if p.get("source") != "CMIMC"]

# Flatten CMIMC problems and add source/year tags
for cmimc_year_block in cmimc_list:
    year = cmimc_year_block.get("year", "unknown")
    for problem in cmimc_year_block.get("problems", []):
        problem["source"] = "CMIMC"
        problem["year"] = year
        all_problems.append(problem)

# Save merged output
with open("all_problems_merged.json", "w") as f:
    json.dump(all_problems, f, indent=2)
