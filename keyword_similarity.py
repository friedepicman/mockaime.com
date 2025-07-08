import json
import re

JSON_PATH = "all_problems_cleaned_with_source.json"  # Path to your JSON file

combined_keywords = [
    # Algebra
    "equation", "inequality", "polynomial", "quadratic", "factor", "root", "expression",
    "variable", "function", "linear", "exponent", "log", "system", "identity", "simplify",
    "expand", "coefficient", "term", "binomial", "sequence", "series", "age", "geometric",
    "arithmetic", "binet's", "de moivre", "division", "factor theorem", "vieta", "piecewise",
    "median", "substitution", "substitute", "complex", "root of unity", "AM-GM", "cauchy-schwarz",
    "floor", "ceiling", "greatest integer", "⌊", "range", "interval", "domain", "codomain",
   "inverse", "composition", "polynomial long division", "synthetic division", 

    # Counting
    "count", "combinations", "permutations", "arrangement", "probability", "choose",
    "subset", "factorial", "pigeonhole", "inclusion-exclusion", "PIE", "casework", "complementary",
    "cardinality", "disjoint", "derangement", "stars and bars", "pascal", "hockey stick",
    "vandermonde", "roots of unity filter", "recursion", "bayes", "expected value",
    "linearity", "markov chain", "euler", "generating function", "catalan", "permutation",
    "combination", "distribution", "arrange", "distinct", "order", "ways", "selection",
    "counting", "pattern", 

    # Geometry
    "triangle", "circle", "angle", "side", "perimeter", "area", "volume", "radius",
    "diameter", "polygon", "quadrilateral", "parallel", "perpendicular", "chord",
    "arc", "sector", "coordinate", "line", "segment", "point", "height", "base",
    "similar", "congruent", "rectangle", "square", "trapezoid", "pentagon", "hexagon",
    "circumference", "inscribed", "regular", "cyclic", "pythag", "power of a point",
    "angle bisector", "centroid", "incenter", "circumcenter", "orthocenter", "excenter",
    "euler", "incircle", "circumcircle", "triangle inequality", "ceva", "menelaus",
    "stewart", "radical", "ptolemy", "heron", "brahmagupta", "sine", "cosine", "sin",
    "cos", "tan", "tangent", "law of sines", "law of cosines", "law of tangents",
    "ratio lemma", "slope", "shoelace", "pick", "magnitude", "3 dimensional shapes",
    "sphere", "cube", "cuboid", "cylinder", "cone", "pyramid", "tetrahedron", "prism",
    "polyhedron", "descarte", "routhe",

    # Number Theory
    "prime", "factor", "multiple", "divisible", "modulo", "congruence", "gcd", "lcm",
    "remainder", "integer", "even", "odd", "perfect square", "perfect cube", "divisor",
    "sum of divisors", "product of divisors", "relatively prime", "rpime", "coprime",
    "Euclidean", "Euclidean algorithm", "residue", "mod", "modular inverse", "little theorem",
    "wilson", "Chinese", "CRT", "order", "ord", "primitive root", "diophantine", "legendre",
    "totient", "multiplicative function", "Simon", "SFFT", "Sophie-Germain", "number", "base"
]

def preprocess(text):
    # Lowercase and remove punctuation for matching
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)  # Replace punctuation with space
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_keywords(text, keywords):
    found = set()
    # For multi-word keywords, simple substring search is enough here
    for kw in keywords:
        if kw in text:
            found.add(kw)
    return found

def jaccard_similarity(set1, set2):
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    if union == 0:
        return 0.0
    return intersection / union

def find_similar_by_keywords(user_index, problems, keywords, top_k=3):
    keyword_sets = []

    # Precompute keyword sets for all problems once
    for p in problems:
        text = p.get('cleaned_solution', '')  # or "cleaned_problem" if you prefer
        text = preprocess(text)
        kws = extract_keywords(text, combined_keywords)
        keyword_sets.append(kws)

    if not (0 <= user_index < len(problems)):
        print(f"Index {user_index} is out of bounds.")
        return

    # Keywords in the user-selected problem
    query_set = keyword_sets[user_index]
    print(f"🔑 Number of keywords matched in problem [{user_index}]: {len(query_set)}")

    # Compute similarities using Jaccard similarity
    similarities = []
    for idx, kw_set in enumerate(keyword_sets):
        if idx == user_index:
            continue
        sim = jaccard_similarity(query_set, kw_set)
        similarities.append((sim, idx))

    # Sort descending by similarity score
    similarities.sort(reverse=True, key=lambda x: x[0])

    print(f"\nTop {top_k} problems similar to problem {user_index} — Source: {problems[user_index].get('source','Unknown')}:")

    for sim, idx in similarities[:top_k]:
        matched_count = len(keyword_sets[idx])
        print(f"[{idx}] — Source: {problems[idx].get('source','Unknown')} (Similarity: {sim:.3f}, Keywords matched: {matched_count})")


def main():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        all_problems = json.load(f)
    
    problems = [p for p in all_problems if 'aime' in p.get('source', '').lower()]

    while True:
        user_input = input("Enter problem index (or 'q' to quit): ").strip()
        if user_input.lower() == 'q':
            break
        if not user_input.isdigit():
            print("Please enter a valid integer index.")
            continue
        user_index = int(user_input)
        find_similar_by_keywords(user_index, problems, combined_keywords, top_k=3)

if __name__ == "__main__":
    main()