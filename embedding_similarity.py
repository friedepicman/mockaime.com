import json
import torch
from sentence_transformers import SentenceTransformer, util

# === CONFIGURATION ===
JSON_PATH = "all_problems_cleaned_with_source.json"   # Path to your JSON file
EMBED_FIELD = "cleaned_solution"
TOP_K = 3  # Number of similar problems to return

# === LOAD DATA ===
with open(JSON_PATH, "r", encoding="utf-8") as f:
    problems = json.load(f)

# Extract the relevant text
texts = []
indexed_problems = []

for i, p in enumerate(problems):
    source = p.get("source", "")
    field = p.get(EMBED_FIELD)

    if "aime" in source.lower() and isinstance(field, str) and field.strip():
        texts.append(field.strip())
        indexed_problems.append((i, p))  # Track original index if needed

# === LOAD EMBEDDING MODEL ===
model = SentenceTransformer("all-MiniLM-L6-v2")

# === EMBED ALL PROBLEMS ===
embeddings = model.encode(texts, convert_to_tensor=True)

# === INTERACTIVE SEARCH ===
def find_similar(user_index, k=TOP_K):
    # Check if input index exists in original problems
    if not (0 <= user_index < len(problems)):
        print(f"Index {user_index} is out of bounds.")
        return

    # Find index in the filtered, embedded list
    try:
        embed_index = next(i for i, (orig_idx, _) in enumerate(indexed_problems) if orig_idx == user_index)
    except StopIteration:
        source = problems[user_index].get("source", "Unknown")
        print(f"❌ Problem {user_index} — Source: {source} — was skipped (missing or invalid '{EMBED_FIELD}').")
        return

    # Get embedding similarity scores
    query_embedding = embeddings[embed_index]
    cosine_scores = util.pytorch_cos_sim(query_embedding, embeddings)[0]

    # Get top results (skip self)
    top_results = torch.topk(cosine_scores, len(embeddings))  # get all scores to filter manually

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
            continue  # skip if missing problem_number

        prob_diff = abs(user_prob_num - comp_prob_num)

        # Apply your filtering rules:
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
            break

# === MAIN LOOP ===
if __name__ == "__main__":
    aime_indices = [i for i, p in enumerate(problems) if "aime" in p.get("source", "").lower()]
    if aime_indices:
        print(f"📘 AIME problems range from index {aime_indices[0]} to {aime_indices[-1]} (total: {len(aime_indices)})")
    else:
        print("⚠️ No AIME problems found in the dataset.")
    while True:
        user_input = input("\nEnter an index to find similar problems (or 'q' to quit): ")
        if user_input.lower() == "q":
            break
        try:
            idx = int(user_input)
            find_similar(idx)
        except ValueError:
            print("Please enter a valid integer.")
