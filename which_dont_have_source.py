import json
import os

# Load your tagged problems file
with open("all_problems_with_sources.json", "r") as f:
    all_problems = json.load(f)

# Load all link-to-source mappings
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
            link_to_source.update(json.load(f))
    else:
        print(f"⚠️  Warning: {filename} not found")

# Collect unmatched problems
unmatched_problems = []

for problem in all_problems:
    link = problem.get("link")
    if link not in link_to_source:
        unmatched_problems.append(problem)

# Print summary
print("🔍 Unmatched Problems")
print(f"Total unmatched problems: {len(unmatched_problems)}\n")

# Print details
for i, prob in enumerate(unmatched_problems, 1):
    print(f"{i}. {prob.get('title', 'Untitled')}")
    print(f"   {prob.get('link', 'No link')}")
    print(f"   Current source: {prob.get('source', 'None')}\n")

# Optional: Save to file
with open("unmatched_problems.json", "w") as f:
    json.dump(unmatched_problems, f, indent=2)
