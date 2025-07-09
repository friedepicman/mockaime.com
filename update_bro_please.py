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

def create_link_to_text_mapping(json_files):
    """Create a mapping from links to text from the 5 JSON files."""
    link_to_text = {}
    
    for filename in json_files:
        print(f"Processing {filename}...")
        data = load_json(filename)
        if data is None:
            continue
            
        # Count how many entries we're processing
        count = 0
        for item in data:
            if 'link' in item and 'text' in item:
                link_to_text[item['link']] = item['text']
                count += 1
        
        print(f"  Found {count} entries with link and text")
    
    return link_to_text

def update_bro_please_json(bro_filename, link_to_text):
    """Update the bro_please.json file with new text based on link matching."""
    print(f"\nUpdating {bro_filename}...")
    
    # Load bro_please.json
    bro_data = load_json(bro_filename)
    if bro_data is None:
        return
    
    updated_count = 0
    not_found_count = 0
    
    # Update each entry in bro_please.json
    for item in bro_data:
        if 'link' in item:
            link = item['link']
            if link in link_to_text:
                # Update the text field
                old_text = item.get('text', '')
                new_text = link_to_text[link]
                item['text'] = new_text
                updated_count += 1
                print(f"  Updated: {item.get('title', 'Unknown title')}")
            else:
                not_found_count += 1
                print(f"  No match found for: {item.get('title', 'Unknown title')} - {link}")
    
    # Save the updated data
    output_filename = f"updated_{bro_filename}"
    save_json(bro_data, output_filename)
    
    print(f"\nSummary:")
    print(f"  Total entries in {bro_filename}: {len(bro_data)}")
    print(f"  Successfully updated: {updated_count}")
    print(f"  No matches found: {not_found_count}")
    print(f"  Updated file saved as: {output_filename}")

def main():
    # List of the 5 JSON files to process
    json_files = [
        "BMT_problems_only.json",
        "CMIMC_problems_only.json",
        "HMMT_problems_only.json",
        "PUMaC_problems_only.json",
        "SMT_problems_only.json"
    ]
    
    # Main JSON file to update
    bro_filename = "bro_please.json"
    
    print("Starting JSON text matching and updating process...")
    print(f"Looking for files: {', '.join(json_files)}")
    print(f"Target file: {bro_filename}")
    print("-" * 50)
    
    # Create mapping from links to text
    link_to_text = create_link_to_text_mapping(json_files)
    
    print(f"\nTotal unique links found: {len(link_to_text)}")
    
    if len(link_to_text) == 0:
        print("No link-text mappings found. Please check your JSON files.")
        return
    
    # Update bro_please.json
    update_bro_please_json(bro_filename, link_to_text)
    
    print("\nProcess completed!")

if __name__ == "__main__":
    main()