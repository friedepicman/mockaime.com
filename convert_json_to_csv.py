import json
import csv

# Load JSON file
with open('docs/with_aime_answers.json') as f:
    data = json.load(f)

# Assuming data is a list of dicts with consistent keys
keys = data[0].keys()

with open('problems.csv', 'w', newline='', encoding='utf-8') as f:
    dict_writer = csv.DictWriter(f, keys)
    dict_writer.writeheader()
    dict_writer.writerows(data)
