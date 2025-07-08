import requests
from bs4 import BeautifulSoup
import json
import time
import re

def get_aime_problem(year, roman, problem_number):
    base_url = "https://artofproblemsolving.com/wiki/index.php"
    
    if roman is None:
        page = f"{year}_AIME_Problems/Problem_{problem_number}"
        variant_label = ""
    else:
        page = f"{year}_AIME_{roman}_Problems/Problem_{problem_number}"
        variant_label = roman

    url = f"{base_url}?title={page}&action=edit&section=1"
    print(f"  🔗 {year} AIME {variant_label} Problem {problem_number}: {url}")

    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if res.status_code != 200:
        return None

    soup = BeautifulSoup(res.text, 'html.parser')
    textarea = soup.find('textarea')

    if textarea and textarea.text.strip():
        raw = textarea.text.strip()
        raw = re.sub(r"^==\s*Problem\s*==\s*", "", raw)
        return raw

    return None


all_problems = []

for year in range(1983, 2026):
    variants = [None] if year < 2000 else ["I", "II"]
    
    for roman in variants:
        print(f"\n📘 Scraping AIME {roman if roman else ''} {year}...")
        for problem_number in range(1, 16):  # AIME has 15 problems
            latex = get_aime_problem(year, roman, problem_number)
            if latex:
                all_problems.append({
                    "year": year,
                    "variant": roman if roman else "I",  # Treat pre-2000 as "I"
                    "problem_number": problem_number,
                    "latex": latex
                })
            else:
                print(f"  ❌ Missing: {year} AIME {roman if roman else ''} Problem {problem_number}")
            time.sleep(0.5)

# ✅ Save to file
with open("aime_problems.json", "w", encoding="utf-8") as f:
    json.dump(all_problems, f, indent=2, ensure_ascii=False)

print("✅ Done! Saved to aime_problems.json")
