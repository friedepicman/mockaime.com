import json
import os

def combine_problem_files(filenames, output_file="combined_problems.json"):
    combined = []
    stats = {
        "total": 0,
        "with_solutions": 0,
        "per_source": {}
    }

    for filename in filenames:
        if not os.path.isfile(filename):
            print(f"❌ File not found: {filename}")
            continue

        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        source_name = filename.split("_")[0]  # e.g., 'bmt' from 'bmt_problems_deduped.json'

        source_problem_count = 0
        source_with_solution_count = 0

        for year_data in data:
            year = year_data.get("year", "unknown")
            for problem in year_data.get("problems", []):
                problem["source"] = source_name
                problem["year"] = year
                combined.append(problem)
                stats["total"] += 1
                source_problem_count += 1
                if problem.get("solution"):
                    stats["with_solutions"] += 1
                    source_with_solution_count += 1

        stats["per_source"][source_name] = {
            "problems": source_problem_count,
            "with_solutions": source_with_solution_count
        }

    # Save combined output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n✅ Combined Summary:")
    print(f"🧮 Total problems: {stats['total']}")
    print(f"✅ With solutions: {stats['with_solutions']}")
    print("📊 Per source breakdown:")
    for source, counts in stats["per_source"].items():
        print(f"  - {source}: {counts['problems']} problems, {counts['with_solutions']} with solutions")

    print(f"\n📁 Output saved to: {output_file}")

# Example usage:
if __name__ == "__main__":
    input_files = [
        "BMT_problems_with_solutions.json",
        "CMIMC_problems_with_solutions.json",
        "HMMT_problems_with_solutions.json",
        "SMT_problems_with_solutions.json",
        "PUMaC_problems_with_solutions.json"
    ]
    combine_problem_files(input_files)
