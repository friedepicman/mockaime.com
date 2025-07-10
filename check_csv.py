import csv

input_file = 'problems.csv'
output_file = 'problems_fixed.csv'  # output with difficulties fixed, optional

unique_links = set()
null_difficulty_count = 0
total_rows = 0

with open(input_file, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    fieldnames = reader.fieldnames

    rows = []
    for row in reader:
        total_rows += 1

        # Track unique links
        link = row.get('link', '').strip()
        if link:
            unique_links.add(link)

        # Fix difficulty if null or empty string
        difficulty = row.get('difficulty')
        if difficulty is None or difficulty.strip() == '' or difficulty.lower() == 'null':
            null_difficulty_count += 1
            row['difficulty'] = '-1'

        rows.append(row)

print(f"Total rows: {total_rows}")
print(f"Unique link count: {len(unique_links)}")
print(f"Null or empty difficulties replaced: {null_difficulty_count}")

# Optionally, write fixed CSV
with open(output_file, 'w', newline='', encoding='utf-8') as outcsv:
    writer = csv.DictWriter(outcsv, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
