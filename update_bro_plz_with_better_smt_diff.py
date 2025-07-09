import json

def main():
    # Load the SMT problems with correct difficulty
    with open("smt_problems_with_difficulty.json") as f:
        smt_problems = json.load(f)
    
    # Build a dictionary from link -> difficulty
    smt_difficulty_map = {
        prob["link"]: prob["difficulty"]
        for prob in smt_problems
        if "link" in prob and "difficulty" in prob
    }

    # Load the full problem dataset
    with open("difficulty_updated_bro_please.json") as f:
        all_problems = json.load(f)

    updated = 0
    for prob in all_problems:
        link = prob.get("link")
        if link in smt_difficulty_map:
            prob["difficulty"] = smt_difficulty_map[link]
            updated += 1

    # Save the updated dataset
    with open("difficulty_updated_bro_please.json", "w") as f:
        json.dump(all_problems, f, indent=2)

    print(f"✅ Updated difficulty for {updated} SMT problems in the full dataset.")

if __name__ == "__main__":
    main()
