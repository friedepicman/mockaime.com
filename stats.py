import json
from collections import Counter

def is_positive_integer_under_1000(val):
    if isinstance(val, int):
        return 0 < val < 1000
    if isinstance(val, str):
        try:
            intval = int(val)
            return 0 < intval < 1000
        except:
            return False
    return False

def count_contest_problems(problems, contest_names):
    """Count problems from specific contests based on source field"""
    contest_counts = {}
    
    for contest in contest_names:
        count = 0
        for problem in problems:
            source = problem.get("source", "")
            if isinstance(source, str) and contest in source:
                count += 1
        contest_counts[contest] = count
    
    return contest_counts

def count_duplicates(problems):
    """Count duplicate problems based on link tag"""
    link_counts = Counter()
    link_to_sources = {}
    
    for problem in problems:
        link = problem.get("link", "")
        if link:  # Only count problems that have a link
            link_counts[link] += 1
            source = problem.get("source", "")
            if link not in link_to_sources:
                link_to_sources[link] = []
            link_to_sources[link].append(source)
    
    # Count how many links appear more than once
    duplicates = sum(1 for count in link_counts.values() if count > 1)
    
    # Count total duplicate instances (e.g., if a link appears 3 times, that's 2 duplicates)
    total_duplicate_instances = sum(count - 1 for count in link_counts.values() if count > 1)
    
    # Get duplicate links and their sources
    duplicate_links = {link: sources for link, sources in link_to_sources.items() if link_counts[link] > 1}
    
    return duplicates, total_duplicate_instances, link_counts, duplicate_links

def main():
    filename = "bro_please_please.json"
    with open(filename, "r") as f:
        problems = json.load(f)

    total_problems = len(problems)

    # Count duplicates
    unique_links_with_duplicates, total_duplicate_instances, link_counts, duplicate_links = count_duplicates(problems)

    # Problems with difficulty assigned (any answer)
    with_diff_all = [p for p in problems if "difficulty" in p]
    total_with_diff_all = len(with_diff_all)
    difficulty_values_all = [p["difficulty"] for p in with_diff_all if isinstance(p["difficulty"], (int, float))]
    rounded_diffs_all = [round(d * 2) / 2 for d in difficulty_values_all]
    distribution_all = Counter(rounded_diffs_all)

    # Problems with positive integer answers < 1000 and difficulty assigned
    filtered = [p for p in problems if is_positive_integer_under_1000(p.get("answer"))]
    total_filtered = len(filtered)
    with_diff_filtered = [p for p in filtered if "difficulty" in p]
    total_with_diff_filtered = len(with_diff_filtered)
    difficulty_values_filtered = [p["difficulty"] for p in with_diff_filtered if isinstance(p["difficulty"], (int, float))]
    rounded_diffs_filtered = [round(d * 2) / 2 for d in difficulty_values_filtered]
    distribution_filtered = Counter(rounded_diffs_filtered)

    # Count problems from specific contests
    contest_names = ["BMT", "SMT", "HMMT", "CMIMC", "PUMaC"]
    contest_counts = count_contest_problems(problems, contest_names)

    print(f"Total problems in dataset: {total_problems}")
    print(f"Unique links with duplicates: {unique_links_with_duplicates}")
    print(f"Total duplicate instances: {total_duplicate_instances}")
    print(f"Problems with difficulty assigned (all): {total_with_diff_all}")
    print("Difficulty distribution (all problems with difficulty):")
    for diff in sorted(distribution_all):
        print(f"  {diff} : {distribution_all[diff]}")

    print()
    print(f"Problems with positive integer answers < 1000: {total_filtered}")
    print(f"Of these, problems with difficulty assigned: {total_with_diff_filtered}")
    print("Difficulty distribution (filtered problems):")
    for diff in sorted(distribution_filtered):
        print(f"  {diff} : {distribution_filtered[diff]}")

    print()
    print("Problems by contest source:")
    for contest in contest_names:
        print(f"  {contest}: {contest_counts[contest]}")

    print()
    print("Duplicate links and their sources:")
    for link, sources in duplicate_links.items():
        print(f"  {link}:")
        for source in sources:
            print(f"    - {source}")
        print()

if __name__ == "__main__":
    main()