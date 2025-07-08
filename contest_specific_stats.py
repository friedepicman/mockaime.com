import json

def count_problems_in_json(filename):
    """Count total problems in a JSON file with year/problems structure"""
    with open(filename, "r") as f:
        data = json.load(f)
    
    total_problems = 0
    year_counts = {}
    
    # Handle case where data is a list of year objects
    if isinstance(data, list):
        for year_obj in data:
            if isinstance(year_obj, dict) and "problems" in year_obj:
                year = year_obj.get("year", "unknown")
                problem_count = len(year_obj["problems"])
                year_counts[year] = problem_count
                total_problems += problem_count
    
    # Handle case where data is a single year object
    elif isinstance(data, dict) and "problems" in data:
        year = data.get("year", "unknown")
        problem_count = len(data["problems"])
        year_counts[year] = problem_count
        total_problems += problem_count
    
    return total_problems, year_counts

def main():
    filename = input("Enter the JSON filename: ")
    
    try:
        total_problems, year_counts = count_problems_in_json(filename)
        
        print(f"Total problems in dataset: {total_problems}")
        print("\nProblems by year:")
        for year in sorted(year_counts.keys()):
            print(f"  {year}: {year_counts[year]}")
            
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{filename}'.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()