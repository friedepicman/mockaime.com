import pandas as pd
import re
from fractions import Fraction
from collections import Counter
import uuid

def extract_numerical_answer(solution_text):
    if not solution_text or pd.isna(solution_text):
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

    # Look for LaTeX math expressions
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
        if '=' in expr:
            rhs = expr.split('=')[-1].strip()
            if rhs:
                return rhs

    trailing_number = re.search(r"[^0-9a-zA-Z](\d+)[^0-9a-zA-Z]*$", solution_text)
    if trailing_number:
        return trailing_number.group(1).strip()

    return None

def tag_answer_type(ans_str):
    if not ans_str or pd.isna(ans_str):
        return "unknown"

    s = str(ans_str).strip().replace(" ", "")
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

def calculate_aime_answer(answer):
    """Calculate AIME answer (mod 1000) if applicable"""
    if not answer or pd.isna(answer):
        return None
    
    try:
        # Try to extract a number from the answer
        answer_str = str(answer).strip()
        
        # Handle simple integers
        if re.match(r"^-?\d+$", answer_str):
            num = int(answer_str)
            if num >= 0:  # AIME answers are typically non-negative
                return num % 1000
        
        # Handle fractions like \frac{numerator}{denominator}
        frac_match = re.match(r"\\frac\{(\d+)\}\{(\d+)\}", answer_str)
        if frac_match:
            num = int(frac_match.group(1))
            den = int(frac_match.group(2))
            if den != 0:
                result = num // den  # Integer division for AIME-style problems
                return result % 1000
        
        # Handle square roots - approximate for integer results
        sqrt_match = re.match(r"(\d*)\\?sqrt\{(\d+)\}", answer_str)
        if sqrt_match:
            multiplier = int(sqrt_match.group(1)) if sqrt_match.group(1) else 1
            radicand = int(sqrt_match.group(2))
            # Only calculate if it's a perfect square
            sqrt_val = int(radicand ** 0.5)
            if sqrt_val * sqrt_val == radicand:
                result = multiplier * sqrt_val
                return result % 1000
        
    except:
        pass
    
    return None

# === Main logic ===
input_file = "/Users/jasonyuan/Documents/git/math/HMMT_February_problems_with_solutions_and_sources.csv"
output_file = "HMMT_February_processed.csv"

# Read CSV file
try:
    df = pd.read_csv(input_file)
    print(f"✅ Loaded CSV with {len(df)} rows and columns: {list(df.columns)}")
except Exception as e:
    print(f"❌ Error reading CSV: {e}")
    exit(1)

# Handle columns - create or reset them with proper data types
# Generate sequential IDs starting from 9554
df['id'] = [9554 + i for i in range(len(df))]

# Initialize columns with proper data types to avoid pandas warnings
df['answer'] = df['answer'].astype('object') if 'answer' in df.columns else None
df['aime_answer'] = df['aime_answer'].astype('object') if 'aime_answer' in df.columns else None
df['answer_type'] = df['answer_type'].astype('object') if 'answer_type' in df.columns else None

# Reset all answer-related columns to None to start fresh
df['answer'] = None
df['aime_answer'] = None
df['answer_type'] = None

# Process each row
total_problems = len(df)
answers_extracted = 0
failed_to_extract = []
type_counter = Counter()

print(f"🔄 Processing {total_problems} problems...")

for idx, row in df.iterrows():
    solution = row.get('solution', '') if 'solution' in df.columns else ''
    
    # Extract answer from solution
    answer = extract_numerical_answer(solution)
    df.at[idx, 'answer'] = answer
    
    if answer:
        answers_extracted += 1
        answer_type = tag_answer_type(answer)
        aime_answer = calculate_aime_answer(answer)
    else:
        answer_type = "unknown"
        aime_answer = None
        if len(failed_to_extract) < 30:
            failed_to_extract.append({
                "index": idx,
                "title": row.get('title', ''),
                "text": str(row.get('text', ''))[:100],
                "solution": str(solution)[:300]
            })
    
    df.at[idx, 'answer_type'] = answer_type
    df.at[idx, 'aime_answer'] = aime_answer
    type_counter[answer_type] += 1

# Save processed CSV
df.to_csv(output_file, index=False)

# Report
print(f"✅ Processed {total_problems} problems.")
print(f"🔍 Extracted answers for {answers_extracted} problems.")
print(f"❌ Couldn't extract answers for {total_problems - answers_extracted} problems.")
print(f"💾 Saved to: {output_file}")
print("\n📊 Answer type breakdown:")
for ans_type, count in type_counter.most_common():
    print(f"  {ans_type}: {count}")

print("\n🔍 First 5 failures:")
for fail in failed_to_extract[:5]:
    print(f"\n— Problem #{fail['index']}")
    print(f"  Title: {fail['title']}")
    print(f"  Text: {fail['text']}...")
    print(f"  Solution snippet: {fail['solution']}...")

# Extra stats
pos_ints_under_1000 = df[df['answer_type'] == 'positive integer <= 1000']
pos_ints_all = df[df['answer_type'].str.contains('positive integer', na=False)]
pos_ints_with_aime = df[(df['answer_type'] == 'positive integer <= 1000') & (df['aime_answer'].notna())]

print("\n📈 Extra Stats:")
print(f"  ✅ Positive integers ≤ 1000: {len(pos_ints_under_1000)}")
print(f"  ✅ Total positive integers (incl. >1000): {len(pos_ints_all)}")
print(f"  ✅ Positive integers ≤ 1000 with AIME answer: {len(pos_ints_with_aime)}")

# Show sample of extracted data
print("\n📋 Sample extracted data:")
sample_df = df[df['answer'].notna()].head(3)
for idx, row in sample_df.iterrows():
    print(f"  Problem {row['id']}: answer='{row['answer']}', aime_answer={row['aime_answer']}, type='{row['answer_type']}'")

print(f"\n🎯 Ready for upload! Column order: {list(df.columns)}")