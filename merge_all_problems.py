import json

def load_json(filename):
    with open(filename, "r") as f:
        return json.load(f)

def save_json(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def merge_difficulties(original_file, difficulty_files, output_file):
    # Load original problems
    original = load_json(original_file)
    print(f"Loaded {len(original)} problems from original dataset.")

    # Build a map from problem link (unique ID) to problem dict for quick update
    original_map = {prob["link"]: prob for prob in original if "link" in prob}

    updated_problem_links = set()

    # Process each difficulty file
    for diff_file in difficulty_files:
        difficulty_data = load_json(diff_file)
        print(f"Loaded {len(difficulty_data)} problems from {diff_file}")

        for prob in difficulty_data:
            link = prob.get("link")
            if link and "difficulty" in prob and link in original_map:
                # Update difficulty in original problem
                original_prob = original_map[link]
                if "difficulty" not in original_prob or original_prob["difficulty"] != prob["difficulty"]:
                    original_prob["difficulty"] = prob["difficulty"]
                    updated_problem_links.add(link)

    print(f"Total unique problems updated with difficulty: {len(updated_problem_links)}")

    # Save merged dataset
    save_json(original, output_file)
    print(f"Saved merged dataset as '{output_file}'")

if __name__ == "__main__":
    original_file = "all_problems_with_sources.json"
    difficulty_files = [
        "cmimc_problems_with_difficulty.json",
        "pumac_problems_with_difficulty.json",
        "smt_problems_with_difficulty.json",
        "bmt_problems_with_difficulty.json",
        "hmmt_problems_with_difficulty.json",
    ]
    output_file = "all_problems_with_all_difficulties.json"
    merge_difficulties(original_file, difficulty_files, output_file)
