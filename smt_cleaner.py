import json

INPUT_FILE = "SMT_problems_with_solutions_final.json"
OUTPUT_FILE = "smt_problems_deduped.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    all_year_data = json.load(f)

seen_links = set()
deduped_data = []
total_before = 0
total_after = 0
no_solution_count = 0
dupe_count = 0

for year_entry in all_year_data:
    unique_problems = []
    for prob in year_entry["problems"]:
        total_before += 1
        if prob["link"] in seen_links:
            dupe_count += 1
            continue
        seen_links.add(prob["link"])
        unique_problems.append(prob)
        if not prob.get("solution") or prob["solution"].strip() == "":
            no_solution_count += 1
    year_entry["problems"] = unique_problems
    total_after += len(unique_problems)
    deduped_data.append(year_entry)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(deduped_data, f, indent=2, ensure_ascii=False)

print("✅ Deduplication complete.")
print(f"📦 Total problems before deduplication: {total_before}")
print(f"📉 Duplicates removed: {dupe_count}")
print(f"📈 Total problems after deduplication: {total_after}")
print(f"❓ Problems missing solutions: {no_solution_count}")
print(f"📁 Output saved to: {OUTPUT_FILE}")
