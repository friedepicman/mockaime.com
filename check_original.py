import json
from collections import Counter

def main():
    with open("all_problems_with_sources.json", "r") as f:
        problems = json.load(f)

    comp_counts = Counter()

    for prob in problems:
        source = prob.get("source", "")
        if source:
            # Extract competition name from source string.
            # Assuming the competition is the first word or a keyword in the source.
            # You can customize this extraction based on your source format.
            # For example, get the first word before a space:
            comp_name = source.split()[0]
            comp_counts[comp_name] += 1
        else:
            comp_counts["Unknown"] += 1

    print("Problem counts by competition:")
    for comp, count in comp_counts.most_common():
        print(f"{comp}: {count}")

if __name__ == "__main__":
    main()
