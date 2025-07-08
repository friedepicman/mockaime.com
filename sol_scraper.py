import requests
from bs4 import BeautifulSoup
import json
import time
import re

def get_aime_solution(year, variant, problem_number):
    base_url = "https://artofproblemsolving.com/wiki/index.php"

    if year < 2000:
        # Pre-2000 single AIME, no variant in URL
        page = f"{year}_AIME_Problems/Problem_{problem_number}"
        variant_label = ""
    else:
        # Post-2000 AIME I or II
        page = f"{year}_AIME_{variant}_Problems/Problem_{problem_number}"
        variant_label = variant

    url = f"{base_url}?title={page}&action=edit&section=2"
    print(f"  📝 Scraping solution for {year} AIME {variant_label} Problem {problem_number}: {url}")

    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            return None
    except Exception as e:
        print(f"    ⚠️ Request error: {e}")
        return None

    soup = BeautifulSoup(res.text, 'html.parser')
    textarea = soup.find('textarea')

    if textarea and textarea.text.strip():
        raw = textarea.text.strip()
        raw = re.sub(r"^==\s*Solution.*?==\s*", "", raw)
        return raw

    return None

def main():
    # Load problems
    with open("aime_problems.json", "r", encoding="utf-8") as f:
        problems = json.load(f)

    print(f"📥 Loaded {len(problems)} AIME problems. Scraping solutions...")

    for p in problems:
        year = p["year"]
        variant = p["variant"] if p["variant"] != "" else None
        problem_number = p["problem_number"]

        sol = get_aime_solution(year, variant, problem_number)
        if sol:
            p["solution"] = sol
        else:
            print(f"  ❌ Missing solution for {year} AIME {variant if variant else ''} Problem {problem_number}")

        time.sleep(0.5)

    # Save updated file
    with open("aime_problems_with_solutions.json", "w", encoding="utf-8") as f:
        json.dump(problems, f, indent=2, ensure_ascii=False)

    print("✅ Done! Solutions saved to aime_problems_with_solutions.json")


if __name__ == "__main__":
    main()
