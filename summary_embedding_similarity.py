import json
import torch
from sentence_transformers import SentenceTransformer, util

# === CONFIGURATION ===
JSON_PATH = "all_problems_cleaned_with_source.json"   # Path to your JSON file
EMBED_FIELD = "solution_summary"
TOP_K = 3  # Number of similar problems to return

# === LOAD DATA ===
with open(JSON_PATH, "r", encoding="utf-8") as f:
    problems = json.load(f)

# Extract the relevant text
texts = []
indexed_problems = []

for i, p in enumerate(problems):
    field = p.get(EMBED_FIELD)
    if isinstance(field, str) and field.strip():
        texts.append(field.strip())
        indexed_problems.append((i, p))  # Track original index if needed

print(f"✅ Loaded {len(indexed_problems)} problems with valid '{EMBED_FIELD}' fields.")

# === LOAD EMBEDDING MODEL ===
model = SentenceTransformer("all-MiniLM-L6-v2")

# === EMBED ALL PROBLEMS ===
print("🔄 Embedding all solution summaries...")
embeddings = model.encode(texts, convert_to_tensor=True)
print("✅ Embedding complete.")

# === INTERACTIVE SEARCH ===
def find_similar(user_index, k=TOP_K):
    if not (0 <= user_index < len(problems)):
        print(f"Index {user_index} is out of bounds.")
        return

    try:
        embed_index = next(i for i, (orig_idx, _) in enumerate(indexed_problems) if orig_idx == user_index)
    except StopIteration:
        source = problems[user_index].get("source", "Unknown")
        print(f"❌ Problem {user_index} — Source: {source} — was skipped (missing or invalid '{EMBED_FIELD}').")
        return

    try:
        user_difficulty = float(problems[user_index].get("difficulty"))
    except (TypeError, ValueError):
        print("⚠️ User problem missing or invalid 'difficulty' field.")
        return

    query_embedding = embeddings[embed_index]
    cosine_scores = util.pytorch_cos_sim(query_embedding, embeddings)[0]
    top_results = torch.topk(cosine_scores, len(embeddings))

    print(f"\n🔍 Problem [{user_index}] — Source: {problems[user_index].get('source', 'Unknown')}")

    print("\n📊 Most similar problems:\n")

    count = 0
    for score, idx in zip(top_results.values, top_results.indices):
        idx = idx.item()
        orig_idx = indexed_problems[idx][0]
        if orig_idx == user_index:
            continue

        try:
            comp_difficulty = float(problems[orig_idx].get("difficulty"))
        except (TypeError, ValueError):
            continue

        diff = abs(user_difficulty - comp_difficulty)

        # Apply filtering rules based on difficulty difference
        if score > 0.7:
            allowed = True
        elif score > 0.65:
            allowed = diff <= 2.5
        elif score > 0.6:
            allowed = diff <= 2.0
        else:
            allowed = diff <= 1.5

        if not allowed:
            continue

        source = problems[orig_idx].get("source", "Unknown")
        summary = problems[orig_idx].get(EMBED_FIELD, "")[:80].replace("\n", " ")
        print(f"[{orig_idx}] — {source} (Score: {score:.4f}, Difficulty diff: {diff:.1f}) — \"{summary}...\"")

        count += 1
        if count >= k:
            break

# === MAIN LOOP ===
if __name__ == "__main__":
    while True:
        user_input = input("\nEnter an index to find similar problems (or 'q' to quit): ")
        if user_input.lower() == "q":
            break
        try:
            idx = int(user_input)
            find_similar(idx)
        except ValueError:
            print("Please enter a valid integer.")
