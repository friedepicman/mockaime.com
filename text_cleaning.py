import json
import re
from pathlib import Path

import re

def clean_latex(text):
    if not text:
        return ""

    # Decode HTML entities
    text = text.replace("&lt;", "<").replace("&gt;", ">")

    # Keep math content: <math>...</math> and <cmath>...</cmath>
    text = re.sub(r"<(math|cmath).*?>(.*?)</\1>", r"\2", text, flags=re.DOTALL | re.IGNORECASE)

    # Strip \begin{} and \end{} tags, but preserve inner content
    text = re.sub(r"\\begin\{.*?\}", "", text)
    text = re.sub(r"\\end\{.*?\}", "", text)

    # Replace known LaTeX expressions with natural language
    replacements = {
        r"\\log": " log ",
        r"\\ln": " natural log ",
        r"\\exp": " e to the ",
        r"\\sin": " sin ",
        r"\\cos": " cos ",
        r"\\tan": " tan ",
        r"\\csc": " csc ",
        r"\\sec": " sec ",
        r"\\cot": " cot ",
        r"\\arcsin": " arcsin ",
        r"\\arccos": " arccos ",
        r"\\arctan": " arctan ",
        r"\\min": " min ",
        r"\\max": " max ",
        r"\\gcd": " gcd ",
        r"\\lcm": " lcm ",
        r"\\mod": " mod ",
        r"\\lfloor\s*\{(.*?)\}": r"floor of \1",
        r"\\lceil\s*\{(.*?)\}": r"ceiling of \1",
        r"\\in": " in ",
        r"\\notin": " not in ",
        r"\\subset": " subset ",
        r"\\supset": " superset ",
        r"\\cup": " union ",
        r"\\cap": " intersection ",
        r"\\cdot": ".",
        r"\\dfrac\s*\{(.*?)\}\s*\{(.*?)\}": r"fraction \1 over \2",
        r"\\frac\s*\{(.*?)\}\s*\{(.*?)\}": r"fraction \1 over \2",
        r"\\pmod\s*\{(.*?)\}": r"mod \1",
        r"\\log_\{(.*?)\}\{(.*?)\}": r"log base \1 of \2",
        r"\\log_(\S+)\s*(\S+)": r"log base \1 of \2",
    }

    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text)

    # Convert inline math $...$ to plain text
    text = re.sub(r"\$(.*?)\$", r"\1", text)

    # Strip backslash from remaining LaTeX commands but keep the name
    text = re.sub(r"\\([a-zA-Z]+)", r"\1", text)

    # Remove braces
    text = re.sub(r"[{}]", "", text)

    # Normalize spacing
    text = re.sub(r"\s+", " ", text).strip()

    text = re.sub(r"\^(?:\{([^}]+)\}|(\S))", r" to the power \1\2", text)

    # Final cleanup: remove any remaining backslashes
    text = text.replace("\\", "")

    return text



def get_source_tag(p):
    year = p.get("year")
    num = p.get("problem_number")
    contest = p.get("contest")
    variant = p.get("variant", "")  # May be "", "A", "B", "I", or "II"

    if contest == "AMC8":
        return f"{year} AMC 8 #{num}"
    elif contest == "AMC10":
        return f"{year} AMC 10{variant} #{num}"
    elif contest == "AMC12":
        return f"{year} AMC 12{variant} #{num}"
    elif contest == "AIME":
        if year < 2000:
            return f"{year} AIME #{num}"
        else:
            return f"{year} AIME {variant} #{num}" if variant else f"{year} AIME #{num}"
    return f"{year} Problem #{num}"


def main():
    input_files = [
        "amc8_tagged.json",
        "amc10_tagged.json",
        "amc12_tagged.json",
        "aime_tagged.json",
    ]

    all_problems = []

    for file in input_files:
        path = Path(file)
        if not path.exists():
            print(f"⚠️ Warning: {file} not found, skipping.")
            continue

        with open(path, "r", encoding="utf-8") as f:
            problems = json.load(f)

        for p in problems:
            raw_problem = p.get("latex", "")
            raw_solution = p.get("solution", "")
            p["cleaned_problem"] = clean_latex(raw_problem)
            p["cleaned_solution"] = clean_latex(raw_solution)

            # Assign contest for source tag
            # Infer contest based on file name
            if "amc8" in file.lower():
                p["contest"] = "AMC8"
            elif "amc10" in file.lower():
                p["contest"] = "AMC10"
            elif "amc12" in file.lower():
                p["contest"] = "AMC12"
            elif "aime" in file.lower():
                p["contest"] = "AIME"

            # Add source tag
            p["source"] = get_source_tag(p)
            all_problems.append(p)

    with open("all_problems_cleaned_with_source.json", "w", encoding="utf-8") as f:
        json.dump(all_problems, f, indent=1, ensure_ascii=False)

    print("✅ Saved cleaned problems with source tags to all_problems_cleaned_with_source.json")

if __name__ == "__main__":
    main()
