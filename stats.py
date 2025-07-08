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

def main():
    filename = "all_problems_with_all_difficulties.json"
    with open(filename, "r") as f:
        problems = json.load(f)

    total_problems = len(problems)

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

if __name__ == "__main__":
    main()