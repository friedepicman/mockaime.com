import json
import re

# Difficulty mappings based exactly on your data

difficulty_map = {
    'BMT': {
        'Algebra':       [1.5, 2, 2.5, 3, 3.5, 4, 5, 5.5, 6, 7],
        'Geometry':      [1.5, 2, 2.5, 3, 3.5, 4, 5, 5.5, 6, 7],
        'NT':            [1.5, 2, 2.5, 3, 3.5, 4, 5, 5.5, 6, 7],
        'Discrete':      [1.5, 2, 2.5, 3, 3.5, 4, 5, 5.5, 6, 7],
        'Analysis':      [1.5, 2, 2.5, 3, 3.5, 4, 5, 5.5, 6, 7],
        'Team':          [1.5, 2, 2.5, 3, 3.5, 4, 5, 5.5, 6, 7],
        'Tiebreaker Algebra': {1:1.5, 2:3, 3:4.5},
        'Tiebreaker Geometry': {1:1.5, 2:3, 3:4.5},
        'Tiebreaker NT': {1:1.5, 2:3, 3:4.5},
        'Tiebreaker Discrete': {1:1.5, 2:3, 3:4.5},
        'Tiebreaker Analysis': {1:1.5, 2:3, 3:4.5},
        'General Tiebreaker': {1:1.5, 2:3, 3:3.5, 4:4, 5:4.5},
        'General': {
            **{i: 1 for i in range(1, 6)},
            **{i: 1.5 for i in range(6, 10)},
            **{i: 2 for i in range(10, 13)},
            **{i: 2.5 for i in range(13, 15)},
            **{i: 3 for i in range(15, 18)},
            **{i: 3.5 for i in range(18, 20)},
            20: 4, 21: 4.5, 22: 5, 23: 5.5, 24: 6, 25: 6.5
        },
        'Guts': {
            1:1.5, 2:2, 3:2.5, 4:2, 5:2.5, 6:3, 7:3, 8:3.5, 9:4, 10:3.5,
            11:4, 12:4.5, 13:4, 14:4.5, 15:5, 16:5, 17:5.5, 18:6, 19:5.5,
            20:6, 21:6.5, 22:6, 23:6.5, 24:7, 25:6.5, 26:7, 27:7.5
        },
    },
    'CMIMC': {
        # CMIMC Algebra, Combinatorics, Geometry, Number Theory all use this list (subject normalized)
        'Algebra':       [1.5, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6.5, 7],
        'Team_10':       [3, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8],  # 10-problem team rounds
        'Team_15':       [2, 2, 2.5, 2.5, 3, 3.5, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5],  # 15-problem team rounds
        'Tiebreakers':   {1:4, 2:4.5, 3:5},
        'Theoretical Computer Science': [2,2.5,3,3.5,4,4.5,5,5.5,6,6.5],  # example, can be adjusted
        'Computer Science': [2,2.5,3,3.5,4,4.5,5,5.5,6,6.5],  # example, if needed
    },
    'HMMT': {
        'General':       [1,2,3,4,4.5,5,5.5,6,6.5,7],
        'Theme':         [2,3,4,4.5,5,5.5,6,6.5,7,7.5],
        'Guts': {
            1:1.5, 2:2, 3:2.5, 4:2, 5:2.5, 6:3, 7:2.5, 8:3, 9:3.5, 10:3.5,
            11:4, 12:3, 13:3.5, 14:4, 15:3, 16:3.5, 17:4.5, 18:5, 19:5.5,
            20:6, 21:6.5, 22:5.5, 23:6, 24:6.5, 25:6, 26:6.5, 27:7, 28:6.5,
            29:7, 30:7.5, 31:6.5, 32:7, 33:7.5
        },
        'Team':          [2.5, 3, 3.5, 4, 4, 4.5, 5, 5.5, 6, 6.5],
        'General Part 1': [2,3,3.5,4,4,4,4,4.5,4.5,5],
        'General Part 2': [2.5,3,3.5,4,4,4.5,5,5.5,6,6.5],
    },
    'SMT': {
        'Team':          [2,2.5,3,3.5,4,4.5,5,5,5.5,5.5,6,6,6.5,6.5,7],
        'Geometry':      [2.5,3.5,4,4.5,5,5.5,6,6.5,7,7.5],
        'Discrete':      [2.5,3.5,4,4.5,5,5.5,6,6.5,7,7.5],
        'Algebra':       [2.5,3.5,4,4.5,5,5.5,6,6.5,7,7.5],
        'Calculus':      [2.5,3.5,4,4.5,5,5.5,6,6.5,7,7.5],
        'Advanced Topics':[2.5,3.5,4,4.5,5,5.5,6,6.5,7,7.5],
        'Tiebreaker':    {1:2.5, 2:4, 3:5.5},
        'Guts': {
            1:2.5, 2:3, 3:3.5, 4:2.5, 5:3, 6:3.5, 7:2.5, 8:3, 9:3.5, 10:3,
            11:3.5, 12:4, 13:4, 14:4.5, 15:5, 16:4.5, 17:5, 18:5.5, 19:5.5,
            20:6, 21:6.5, 22:6, 23:6.5, 24:7, 25:6.5, 26:7, 27:7.5
        },
        'General': {
            1:1.5, 2:1.5, 3:1.5, 4:1.5, 5:1.5, 6:2, 7:2, 8:2, 9:2, 10:2,
            11:2.5, 12:2.5, 13:2.5, 14:2.5, 15:3, 16:3, 17:3, 18:3,
            19:3.5, 20:3.5, 21:3.5, 22:3.5, 23:4, 24:4, 25:4.5
        },
    },
    'PUMaC': {
        # Division A: algebra, combinatorics, geometry, number theory — normalized to 'Division A'
        'Division A':    [3,3,3.5,3.5,4,4.5,5,5.5,6,6.5],
        # Division B: algebra, combinatorics, geometry, number theory — normalized to 'Division B'
        'Division B':    [1,1.5,2,2.5,2.5,3,3.5,3.5,4,4],
        'Team Round':    [3,3.5,4,4,4.5,5,5.5,6,6.5,7]
    }
}

# Years that have 15 CMIMC Team problems instead of 10:
cmimc_team_15_years = set(range(2016, 2024))  # Example: 2016 to 2023 inclusive

# PUMaC years with Division A/B structure (assuming recent years)
pumac_division_a_years = set(range(2017, 2026))  # e.g. 2017+ years have Division A/B, adjust as needed

# Subjects normalization maps (to unify multiple subjects to one key)
subject_normalization = {
    'CMIMC': {
        'Combinatorics': 'Algebra',
        'Geometry': 'Algebra',
        'Number Theory': 'Algebra',
        # Algebra stays Algebra
    },
    'PUMaC': {
        # All four normalized to Division A or Division B depending on year
        'Algebra': None,  # Will assign dynamically based on year
        'Combinatorics': None,
        'Geometry': None,
        'Number Theory': None,
    },
    # For BMT Tiebreakers, normalize subjects to 'Tiebreaker <Subject>'
    'BMT Tiebreaker': {
        'Algebra': 'Tiebreaker Algebra',
        'Geometry': 'Tiebreaker Geometry',
        'NT': 'Tiebreaker NT',
        'Discrete': 'Tiebreaker Discrete',
        'Analysis': 'Tiebreaker Analysis'
    }
}

def parse_source(source):
    s = source.lower()

    # Identify contest
    contest_match = re.search(r'\b(bmt|cmimc|hmmt|smt|pumac)\b', s)
    contest = contest_match.group(1).upper() if contest_match else None

    # Year extraction (4 digit number)
    year_match = re.search(r'\b(20\d{2})\b', s)
    year = int(year_match.group(1)) if year_match else None

    # Identify if it's a tiebreaker
    is_tiebreaker = bool(re.search(r'\b(tie|tb|tiebreaker)\b', s))

    # Identify subject with special patterns (priority order)
    # Look for specific words or letter+number combos like A1, C3, G2, NT, etc.
    subject = None

    subject_keywords = [
        'algebra', 'geometry', 'nt', 'number theory', 'discrete', 'analysis',
        'combinatorics', 'calculus', 'advanced topics', 'team', 'guts',
        'general part 1', 'general part 2', 'general',
        'division a', 'division b', 'team round', 'theoretical computer science', 'computer science'
    ]

    # Search subject keywords
    for key in subject_keywords:
        if key in s:
            subject = key.title()
            # Fix capitalization
            if key == 'nt' or key == 'number theory':
                subject = 'NT'
            elif key == 'team round':
                subject = 'Team Round'
            elif key == 'division a':
                subject = 'Division A'
            elif key == 'division b':
                subject = 'Division B'
            elif key == 'general part 1':
                subject = 'General Part 1'
            elif key == 'general part 2':
                subject = 'General Part 2'
            elif key == 'theoretical computer science':
                subject = 'Theoretical Computer Science'
            elif key == 'computer science':
                subject = 'Computer Science'
            break

    # If no subject keyword found, check for letter+number combos, e.g. A1, B3, C2, NT1
    if subject is None:
        # Match patterns like "A1", "B3", "NT1" etc in source
        letter_number_match = re.search(r'\b([A-Z]{1,2})(\d+)\b', source, re.I)
        if letter_number_match:
            letter = letter_number_match.group(1).upper()
            # Map letters to subjects if possible (common)
            letter_subject_map = {
                'A': 'Algebra',
                'B': 'Combinatorics',
                'C': 'Geometry',
                'G': 'Geometry',
                'N': 'NT',
                'D': 'Discrete',
            }
            subject = letter_subject_map.get(letter)
        else:
            # fallback, no subject found
            subject = None

    # Extract problem number:
    # Try to find #number or #letter+number (take first number after #)
    number = None
    # Look for #number or #letter+number (like #A3)
    number_match = re.search(r'#([A-Z]?)(\d+)', source, re.I)
    if number_match:
        number = int(number_match.group(2))
    else:
        # fallback: if no #number, look for first number in source
        any_number_match = re.search(r'\b(\d+)\b', source)
        if any_number_match:
            number = int(any_number_match.group(1))

    # Normalize subject for specific contests:

    if contest == 'CMIMC':
        if subject in ['Algebra', 'Combinatorics', 'Geometry', 'NT', 'Number Theory']:
            # normalize all to Algebra
            subject = 'Algebra'
        if subject == 'Theoretical Computer Science' or subject == 'Computer Science':
            # keep as is (have separate difficulty list if you want)
            pass
        if subject == 'Team Round' or subject == 'Team':
            # Decide team length based on year (15 or 10)
            if year in cmimc_team_15_years:
                subject = 'Team_15'
            else:
                subject = 'Team_10'

    if contest == 'PUMAC':
        # Normalize all algebra, combinatorics, geometry, number theory to Division A or B based on year
        if subject in ['Algebra', 'Combinatorics', 'Geometry', 'NT', 'Number Theory']:
            if year in pumac_division_a_years:
                subject = 'Division A'
            else:
                subject = 'Division B'

    if contest == 'BMT' and is_tiebreaker:
        # Normalize subject to tiebreaker variants for BMT
        norm = subject_normalization['BMT Tiebreaker'].get(subject)
        if norm:
            subject = norm
        else:
            # Fallback for general tiebreaker if no specific subject match
            subject = 'General Tiebreaker'

    # Return everything
    return contest, subject, number, year


def get_difficulty(source):
    contest, subject, number, year = parse_source(source)
    if contest is None or subject is None or number is None:
        # Cannot assign difficulty
        return None

    # Select difficulty list/dict for contest/subject
    contest_map = difficulty_map.get(contest)
    if contest_map is None:
        return None

    # Special handling for BMT General and BMT Guts which use dicts keyed by problem number
    if contest == 'BMT' and subject in ['General', 'Guts', 'General Tiebreaker']:
        difficulty_dict = contest_map.get(subject)
        if difficulty_dict:
            if isinstance(difficulty_dict, dict):
                return difficulty_dict.get(number)
            else:
                # If list, number-1 indexing
                idx = number - 1
                if 0 <= idx < len(difficulty_dict):
                    return difficulty_dict[idx]
        return None

    # Special handling for BMT Tiebreaker Algebra etc. which are dicts
    if contest == 'BMT' and subject.startswith('Tiebreaker'):
        difficulty_dict = contest_map.get(subject)
        if difficulty_dict:
            return difficulty_dict.get(number)

    # CMIMC tiebreakers are dicts
    if contest == 'CMIMC' and subject == 'Tiebreakers':
        return contest_map['Tiebreakers'].get(number)

    # Otherwise typical case: list indexed by problem number (1-based)
    difficulty_list = contest_map.get(subject)

    if difficulty_list is None:
        # Subject missing for this contest
        return None

    # If dict type (like HMMT Guts, SMT Guts, SMT General, etc)
    if isinstance(difficulty_list, dict):
        return difficulty_list.get(number)

    # If list, index with number-1
    idx = number - 1
    if 0 <= idx < len(difficulty_list):
        return difficulty_list[idx]

    # No matching difficulty
    return None

unmatched = []

with open('all_problems_with_sources.json', 'r') as f:
    problems = json.load(f)

unmatched = []

for problem in problems:
    source = problem.get('source', '')
    difficulty = get_difficulty(source)
    if difficulty is None:
        unmatched.append((problem.get('title', 'NO TITLE'), source))
    else:
        problem['difficulty'] = difficulty

with open('all_problems_with_difficulty.json', 'w') as f:
    json.dump(problems, f, indent=2)

if unmatched:
    print(f"⚠️ {len(unmatched)} problems could not be matched for difficulty:")
    for title, src in unmatched:
        print(f"- {title}: {src}")
else:
    print("✅ All problems assigned difficulty successfully.")
