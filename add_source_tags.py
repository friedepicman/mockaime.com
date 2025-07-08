import json
import os

# Load the merged problems list
with open("all_problems_merged.json", "r") as f:
    all_problems = json.load(f)

# Load all link-to-source mapping files
mapping_files = [
    "BMT_link_source_map.json",
    "CMIMC_link_source_map.json",
    "HMMT_link_source_map.json",
    "PUMaC_link_source_map.json",
    "SMT_link_source_map.json"
]

link_to_source = {}
for filename in mapping_files:
    if os.path.exists(filename):
        with open(filename, "r") as f:
            data = json.load(f)
            link_to_source.update(data)
    else:
        print(f"⚠️  Warning: {filename} not found")

# Stats counters
total_problems = len(all_problems)
updated_count = 0
unchanged_but_correct = 0
no_match_count = 0

# Apply source updates
for problem in all_problems:
    link = problem.get("link")
    current_source = problem.get("source")
    new_source = link_to_source.get(link)

    if new_source:
        if current_source != new_source:
            problem["source"] = new_source
            updated_count += 1
        else:
            unchanged_but_correct += 1
    else:
        no_match_count += 1

# Save updated problem set
with open("all_problems_with_sources.json", "w") as f:
    json.dump(all_problems, f, indent=2)

# Print summary
print("📊 Update Summary")
print(f"Total problems:               {total_problems}")
print(f"Source updated via mapping:   {updated_count}")
print(f"Source already correct:       {unchanged_but_correct}")
print(f"No matching link found:       {no_match_count}")
