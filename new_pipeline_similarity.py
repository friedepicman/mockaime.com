import json
import torch
import time
from openai import OpenAI
from sentence_transformers import SentenceTransformer, util

# === CONFIGURATION ===
JSON_PATH = "all_problems_cleaned_with_source.json"
EMBED_FIELD = "solution_summary"  # We'll generate this from cleaned_solution
TOP_K = 3
MODEL_NAME = "all-MiniLM-L6-v2"
OPENAI_API_KEY = "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"

# === INITIALIZE MODELS ===
client = OpenAI(api_key=OPENAI_API_KEY)
embedder = SentenceTransformer(MODEL_NAME)

# === LOAD DATA ===
with open(JSON_PATH, "r", encoding="utf-8") as f:
    problems = json.load(f)

# === STEP 1: Summarize solutions (if not already present) ===
def gpt_summarize(problem, solution):
    prompt = f"Summarize the mathematical ideas and techniques used in solving this problem:\n\nProblem: {problem}\n\nSolution: {solution}\n\nSummary:"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content.strip()

updated = False
for i, p in enumerate(problems):
    source = p.get("source", "")
    if "aime" in source.lower():
        if not p.get("solution_summary"):
            problem = p.get("problem", "").strip()
            sol = p.get("cleaned_solution", "").strip()
            if problem and sol:
                try:
                    summary = gpt_summarize(problem, sol)
                    problems[i]["solution_summary"] = summary
                    print(f"[{i}] Summary added.")
                    updated = True
                    time.sleep(1)  # Avoid rate limiting
                except Exception as e:
                    print(f"[{i}] Error: {e}")

if updated:
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(problems, f, indent=2)

# === STEP 2: Embed summaries ===
texts = []
indexed_problems = []

for i, p in enumerate(problems):
    source = p.get("source", "")
    field = p.get(EMBED_FIELD)
    if "aime" in source.lower() and isinstance(field, str) and field.strip():
        texts.append(field.strip())
        indexed_problems.append((i, p))

embeddings = embedder.encode(texts, convert_to_tensor=True)

# === STEP 3: Find Similar ===
def find_similar(user_index, k=TOP_K):
    if not (0 <= user_index < len(problems)):
        print(f"Index {user_index} is out of bounds.")
        return

    try:
        embed_index = next(i for i, (orig_idx, _) in enumerate(indexed_problems) if orig_idx == user_index)
    except StopIteration:
        print(f"❌ Problem {user_index} missing a valid summary.")
        return

    query_embedding = embeddings[embed_index]
    cosine_scores = util.pytorch_cos_sim(query_embedding, embeddings)[0]
    top_results = torch.topk(cosine_scores, len(embeddings))

    print(f"\n🔍 Problem [{user_index}] — Source: {problems[user_index].get('source', 'Unknown')}")
    print("\n📊 Most similar problems:\n")

    count = 0
    user_prob_num = problems[user_index].get("problem_number")
    if user_prob_num is None:
        print("⚠️ User problem missing 'problem_number', cannot filter by difficulty proximity.")
        return

    for score, idx in zip(top_results.values, top_results.indices):
        idx = idx.item()
        orig_idx = indexed_problems[idx][0]
        if orig_idx == user_index:
            continue

        comp_prob_num = problems[orig_idx].get("problem_number")
        if comp_prob_num is None:
            continue

        prob_diff = abs(user_prob_num - comp_prob_num)

        if score > 0.6:
            allowed = True
        elif score > 0.55:
            allowed = prob_diff <= 6
        elif score > 0.5:
            allowed = prob_diff <= 4
        else:
            allowed = prob_diff <= 3

        if not allowed:
            continue

        source = problems[orig_idx].get("source", "Unknown")
        print(f"[{orig_idx}] — Source: {source} (Score: {score:.4f})")
        count += 1
        if count >= k:
            break

# === MAIN LOOP ===
if __name__ == "__main__":
    aime_indices = [i for i, p in enumerate(problems) if "aime" in p.get("source", "").lower()]
    if aime_indices:
        print(f"📘 AIME problems range from index {aime_indices[0]} to {aime_indices[-1]} (total: {len(aime_indices)})")
    else:
        print("⚠️ No AIME problems found.")
    while True:
        user_input = input("\nEnter an index to find similar problems (or 'q' to quit): ")
        if user_input.lower() == "q":
            break
        try:
            idx = int(user_input)
            find_similar(idx)
        except ValueError:
            print("Please enter a valid integer.")
