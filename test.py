import re

def clean_latex(text):
    if not text:
        return ""

    # Decode HTML entities like &lt;math&gt;
    text = text.replace("&lt;", "<").replace("&gt;", ">")

    # Remove <math>...</math> blocks with LaTeX (but KEEP numbers inside if pure digits)
    def remove_math_tags(match):
        inner = match.group(0)
        # Extract number if it's something like <math>42</math>
        digits = re.search(r"<math>(\d+)</math>", inner)
        return digits.group(1) if digits else ""

    text = re.sub(r"<math.*?>.*?</math>", remove_math_tags, text, flags=re.DOTALL | re.IGNORECASE)

    # Remove LaTeX environments
    text = re.sub(r"\\begin\{.*?\}.*?\\end\{.*?\}", "", text, flags=re.DOTALL)

    replacements = {
        r"\\cdot": " times ",
        r"\\times": " times ",
        r"\\div": " divided by ",
        r"\\frac": " fraction ",
        r"\\sqrt": " square root ",
        r"\\leq": " ≤ ",
        r"\\geq": " ≥ ",
        r"\\neq": " ≠ ",
        r"\\approx": " ≈ ",
        r"\\angle": " angle ",
        r"\\pi": " pi ",
        r"\\infty": " infinity ",
        r"\\ldots": " ... ",
        r"\\dots": " ... ",
        r"\\%": " percent ",
        r"\\\$": " dollar ",
        r"\\qquad": " ",
        r"\\mathrm": "",
        r"\\\(": "",
        r"\\\)": "",
        r"\\\[": "",
        r"\\\]": "",
        r"\\\\": " ",
    }

    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text)

    # Remove inline LaTeX math
    text = re.sub(r"\$(.*?)\$", r"\1", text)

    # Remove \text{}
    text = re.sub(r"\\text\{(.*?)\}", r"\1", text)

    # Remove remaining LaTeX commands
    text = re.sub(r"\\[a-zA-Z]+\s*", "", text)

    # Remove braces
    text = re.sub(r"[\{\}]", "", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


# Your sample input
sample = (
    "Aunt Anna is <math>42</math> years old. Caitlin is <math>5</math> years younger than Brianna, "
    "and Brianna is half as old as Aunt Anna. How old is Caitlin?\n\n"
    "<math>\\mathrm{(A)}\\ 15\\qquad\\mathrm{(B)}\\ 16\\qquad\\mathrm{(C)}\\ 17\\qquad\\mathrm{(D)}\\ 21\\qquad\\mathrm{(E)}\\ 37</math>"
)

# Test it
cleaned = clean_latex(sample)
print("🧹 Cleaned Text:\n")
print(cleaned)
