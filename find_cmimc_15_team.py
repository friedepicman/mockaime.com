import json
import re
from collections import defaultdict

with open('all_problems_with_sources.json', 'r') as f:
    problems = json.load(f)

team_problem_counts = defaultdict(set)

for problem in problems:
    source = problem.get('source', '')
    if 'CMIMC' in source:
        year_match = re.search(r'CMIMC\s+(\d{4})', source)
        if not year_match:
            continue
        year = int(year_match.group(1))

        # Try to find Team problem number in different formats:
        # 1) Team #number or Team Round number
        match1 = re.search(r'Team(?: Round)?\s*#?(\d+)', source, re.IGNORECASE)
        # 2) Team X-Y or Team X-Y/Z-W style
        match2 = re.search(r'Team\s+(\d+)[-/](\d+)', source, re.IGNORECASE)

        if match1:
            prob_num = int(match1.group(1))
            team_problem_counts[year].add(prob_num)
        elif match2:
            # For ranges like 'Team 1-1/1-2' just extract first number (1)
            prob_num = int(match2.group(1))
            team_problem_counts[year].add(prob_num)

# Print counts per year
print("Year : Number of unique CMIMC Team problems")
for year in sorted(team_problem_counts):
    print(f"{year} : {len(team_problem_counts[year])}")
