import json
import os

def load_json(filename):
    """Load JSON data from a file."""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {filename}.")
        return None

def save_json(data, filename):
    """Save JSON data to a file."""
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def create_link_to_difficulty_mapping(difficulty_json_file):
    """Create a mapping from links to difficulties from the all_problems_with_all_difficulties.json file."""
    print(f"Loading difficulty data from {difficulty_json_file}...")
    
    data = load_json(difficulty_json_file)
    if data is None:
        return {}
    
    link_to_difficulty = {}
    count = 0
    
    for item in data:
        if 'link' in item and 'difficulty' in item:
            link_to_difficulty[item['link']] = item['difficulty']
            count += 1
    
    print(f"Found {count} entries with link and difficulty")
    return link_to_difficulty

def update_difficulties(target_file, link_to_difficulty):
    """Update the difficulties in the target file based on link matching."""
    print(f"\nUpdating difficulties in {target_file}...")
    
    # Load target file
    target_data = load_json(target_file)
    if target_data is None:
        return
    
    updated_count = 0
    not_found_count = 0
    difficulty_changes = []
    
    # Update each entry in target file
    for item in target_data:
        if 'link' in item:
            link = item['link']
            if link in link_to_difficulty:
                # Store old difficulty for reporting
                old_difficulty = item.get('difficulty', 'None')
                new_difficulty = link_to_difficulty[link]
                
                # Update the difficulty
                item['difficulty'] = new_difficulty
                updated_count += 1
                
                # Track changes for reporting
                if old_difficulty != new_difficulty:
                    difficulty_changes.append({
                        'title': item.get('title', 'Unknown title'),
                        'old': old_difficulty,
                        'new': new_difficulty
                    })
                
                print(f"  Updated: {item.get('title', 'Unknown title')} - Difficulty: {old_difficulty} → {new_difficulty}")
            else:
                not_found_count += 1
                print(f"  No difficulty found for: {item.get('title', 'Unknown title')} - {link}")
    
    # Save the updated data
    output_filename = f"difficulty_updated_{target_file}"
    save_json(target_data, output_filename)
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Total entries in {target_file}: {len(target_data)}")
    print(f"  Successfully updated: {updated_count}")
    print(f"  No matches found: {not_found_count}")
    print(f"  Difficulties actually changed: {len(difficulty_changes)}")
    print(f"  Updated file saved as: {output_filename}")
    
    # Print difficulty changes if any
    if difficulty_changes:
        print(f"\nDifficulty Changes:")
        for change in difficulty_changes:
            print(f"  {change['title']}: {change['old']} → {change['new']}")

def main():
    # File containing correct difficulties
    difficulty_source = "all_problems_with_all_difficulties.json"
    
    # File to update
    target_file = "updated_bro_please.json"
    
    print("Starting difficulty update process...")
    print(f"Source file (with correct difficulties): {difficulty_source}")
    print(f"Target file (to be updated): {target_file}")
    print("-" * 60)
    
    # Create mapping from links to difficulties
    link_to_difficulty = create_link_to_difficulty_mapping(difficulty_source)
    
    if len(link_to_difficulty) == 0:
        print("No link-difficulty mappings found. Please check your source file.")
        return
    
    print(f"Total unique links with difficulties: {len(link_to_difficulty)}")
    
    # Update difficulties in target file
    update_difficulties(target_file, link_to_difficulty)
    
    print("\nProcess completed!")

if __name__ == "__main__":
    main()