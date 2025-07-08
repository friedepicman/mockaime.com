import json
import re
from fractions import Fraction
from collections import Counter

def extract_numerical_answer(solution_text):
    if not solution_text:
        return None

    # Helper: Extract from \boxed{...} or \fbox{...} with nested brace support
    def extract_brace_content(text, start_token):
        start = text.find(start_token)
        if start == -1:
            return None
        i = start + len(start_token)
        depth = 1
        result = ''
        while i < len(text):
            char = text[i]
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return result.strip()
            result += char
            i += 1
        return None

    boxed = extract_brace_content(solution_text, r'\boxed{')
    if boxed:
        return boxed

    fbox = extract_brace_content(solution_text, r'\fbox{')
    if fbox:
        return fbox

    # 2. Look for well-formed LaTeX math blocks like $...$
    latex_exprs = re.findall(r"\$([^\$]+)\$", solution_text)

    for expr in reversed(latex_exprs):
        expr = expr.strip()

        if re.fullmatch(r"\\frac\{[^{}]+\}\{[^{}]+\}", expr):
            return expr
        if re.fullmatch(r"\\sqrt\{[^{}]+\}", expr):
            return expr
        if re.fullmatch(r"-?\d*\\sqrt\{\d+\}", expr):
            return expr
        if re.fullmatch(r"-?\d*\\?pi", expr):
            return expr
        if re.fullmatch(r"-?\d+\^\d+", expr):
            return expr
        if re.fullmatch(r"-?\d+(\.\d+)?", expr):
            return expr

        # If equals sign, return RHS
        if '=' in expr:
            rhs = expr.split('=')[-1].strip()
            if rhs:
                return rhs

    # 3. Final fallback: last trailing number
    trailing_number = re.search(r"[^0-9a-zA-Z](\d+)[^0-9a-zA-Z]*$", solution_text)
    if trailing_number:
        return trailing_number.group(1).strip()

    return None

def tag_answer_type(ans_str):
    if not ans_str:
        return "unknown"

    s = ans_str.strip().replace(" ", "")
    s = s.replace(r"\cdot", "*")

    try:
        val = int(s)
        if val > 1000:
            return "positive integer > 1000"
        elif val > 0:
            return "positive integer <= 1000"
        elif val < 0:
            return "negative integer"
        else:
            return "zero"
    except:
        pass

    try:
        frac = Fraction(s)
        return "positive fraction" if frac > 0 else "negative fraction"
    except:
        pass

    sqrt_pattern = re.compile(r"^-?\\?sqrt\{(\d+)\}$")
    if sqrt_pattern.fullmatch(s):
        return "positive square root" if not s.startswith('-') else "negative square root"

    if re.match(r"^-?\d*\\?sqrt\{\d+\}$", s):
        return "positive multiple of square root" if not s.startswith('-') else "negative multiple of square root"

    if re.match(r"^-?\d*\\?pi$", s):
        return "positive multiple of pi" if not s.startswith('-') else "negative multiple of pi"

    if re.match(r"^-?\d+\^\d+$", s):
        return "positive integer power" if not s.startswith('-') else "negative integer power"

    return "other"

# === Main logic ===
input_file = "CMIMC_problems_with_solutions.json"
output_file = "CMIMC_answers.json"

with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

total_problems = len(data)
answers_extracted = 0
failed_to_extract = []
type_counter = Counter()

for idx, problem in enumerate(data):
    solution = problem.get("solution", "e")
    answer = extract_numerical_answer(solution)
    problem["answer"] = answer

    if answer:
        answers_extracted += 1
        answer_type = tag_answer_type(answer)
    else:
        answer_type = "unknown"
        if len(failed_to_extract) < 30:
            failed_to_extract.append({
                "index": idx,
                "text": problem.get("text", "")[:100],
                "solution": (solution or "")[:300]
            })

    problem["answer_type"] = answer_type
    type_counter[answer_type] += 1

# Save to new JSON
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# Report
print(f"✅ Loaded {total_problems} problems.")
print(f"🔍 Extracted answers for {answers_extracted} problems.")
print(f"❌ Couldn't extract answers for {total_problems - answers_extracted} problems.")
print(f"💾 Saved to: {output_file}")
print("\n📊 Answer type breakdown:")
for ans_type, count in type_counter.items():
    print(f"  {ans_type}: {count}")

print("\n🔍 First 5 failures:")
for fail in failed_to_extract[:5]:
    print(f"\n— Problem #{fail['index']}")
    print(f"  Text: {fail['text']}...")
    print(f"  Solution snippet: {fail['solution']}...")

pos_ints_under_1000 = [p for p in data if p.get("answer_type") == "positive integer <= 1000"]
pos_ints_all = [p for p in data if "positive integer" in (p.get("answer_type") or "")]
pos_ints_under_1000_with_diff = [p for p in pos_ints_under_1000 if p.get("difficulty") is not None]

print("\n📈 Extra Stats:")
print(f"  ✅ Positive integers ≤ 1000: {len(pos_ints_under_1000)}")
print(f"  ✅ Total positive integers (incl. >1000): {len(pos_ints_all)}")
print(f"  ✅ Positive integers ≤ 1000 with difficulty: {len(pos_ints_under_1000_with_diff)}")
