import json
import torch
from transformers import BertForMaskedLM, BertTokenizerFast
from torch.nn.functional import normalize
from sentence_transformers import util  # for pytorch_cos_sim
from tqdm import tqdm  # Make sure to import tqdm at the top
# === CONFIGURATION ===
JSON_PATH = "all_problems_with_masked_summary.json"
EMBED_FIELD = "solution_summary"
TOP_K = 3
MAX_LENGTH = 256
TOP_TOKENS_MAIN = 5
TOP_TOKENS_SIMILAR = 3

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# === LOAD DATA ===
with open(JSON_PATH, "r", encoding="utf-8") as f:
    problems = json.load(f)

# === LOAD MODEL AND TOKENIZER ===
tokenizer = BertTokenizerFast.from_pretrained("./mlm_trained_model")
model = BertForMaskedLM.from_pretrained("./mlm_trained_model")
model = model.to(device)
model.eval()

def get_embedding_and_tokens(text):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding="max_length",
        truncation=True,
        max_length=MAX_LENGTH,
        return_special_tokens_mask=True,
    )
    input_ids = inputs["input_ids"].to(device)
    attention_mask = inputs["attention_mask"].to(device)
    special_tokens_mask = inputs["special_tokens_mask"].to(device)

    with torch.no_grad():
        outputs = model.bert(input_ids=input_ids, attention_mask=attention_mask)
        last_hidden_state = outputs.last_hidden_state

    mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    sum_embeddings = torch.sum(last_hidden_state * mask_expanded, 1)
    sum_mask = torch.clamp(mask_expanded.sum(1), min=1e-9)
    embedding = sum_embeddings / sum_mask

    embedding = normalize(embedding, p=2, dim=1)
    token_embeddings = normalize(last_hidden_state.squeeze(0), p=2, dim=1)

    return embedding.squeeze(0), token_embeddings, input_ids.squeeze(0), special_tokens_mask.squeeze(0)


# === Prepare problems with embeddings ===
indexed_problems = []
all_embeddings = []
all_token_embeds = []
all_input_ids = []
all_special_masks = []

print("🔎 Checking existing embeddings in problems...")

for i, p in enumerate(problems):
    summary = p.get(EMBED_FIELD)
    embedding_exists = "embedding" in p and isinstance(p["embedding"], list) and len(p["embedding"]) > 0

    if isinstance(summary, str) and summary.strip():
        indexed_problems.append((i, p))
        if embedding_exists:
            # Use saved embedding tensor
            all_embeddings.append(torch.tensor(p["embedding"]))
            # We do not have token_embeds etc. saved, so we will recompute those below if needed
            all_token_embeds.append(None)
            all_input_ids.append(None)
            all_special_masks.append(None)
        else:
            all_embeddings.append(None)  # placeholder for later
            all_token_embeds.append(None)
            all_input_ids.append(None)
            all_special_masks.append(None)
    else:
        # Problem missing valid summary, skip
        pass

# === Compute embeddings only for problems missing embeddings ===
def compute_and_fill_embeddings():
    print("🔄 Computing embeddings for problems missing them...")
    for idx, (orig_i, prob) in enumerate(tqdm(indexed_problems, desc="Embedding problems")):
        if all_embeddings[idx] is None:
            text = prob[EMBED_FIELD]
            emb, token_embeds, input_ids, special_mask = get_embedding_and_tokens(text)
            all_embeddings[idx] = emb
            all_token_embeds[idx] = token_embeds
            all_input_ids[idx] = input_ids
            all_special_masks[idx] = special_mask

            # Save embedding back into problems JSON (as list)
            problems[orig_i]["embedding"] = emb.tolist()
        else:
            # For problems that already have embeddings, recompute token info
            text = prob[EMBED_FIELD]
            _, token_embeds, input_ids, special_mask = get_embedding_and_tokens(text)
            all_token_embeds[idx] = token_embeds
            all_input_ids[idx] = input_ids
            all_special_masks[idx] = special_mask

    print("💾 Saving updated embeddings to JSON file...")
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(problems, f, indent=2)


# Check if any embeddings are missing and compute if needed
if any(e is None for e in all_embeddings):
    compute_and_fill_embeddings()
else:
    # All embeddings exist, but recompute token-level info for all problems
    print("✅ All embeddings found. Recomputing token embeddings and masks...")
    for idx, (orig_i, prob) in enumerate(indexed_problems):
        text = prob[EMBED_FIELD]
        _, token_embeds, input_ids, special_mask = get_embedding_and_tokens(text)
        all_token_embeds[idx] = token_embeds
        all_input_ids[idx] = input_ids
        all_special_masks[idx] = special_mask

embeddings = torch.stack(all_embeddings)


# === Function to get top tokens by cosine similarity ===
def top_tokens(embedding, token_embeddings, input_ids, special_tokens_mask, top_n=5):
    cos_sim = torch.matmul(token_embeddings, embedding)
    valid_mask = special_tokens_mask == 0
    valid_cos_sim = cos_sim[valid_mask]
    valid_input_ids = input_ids[valid_mask]

    top_vals, top_idxs = torch.topk(valid_cos_sim, min(top_n, len(valid_cos_sim)))
    top_tokens = [tokenizer.decode([valid_input_ids[i]]) for i in top_idxs]
    top_scores = top_vals.tolist()

    return list(zip(top_tokens, top_scores))


# === Interactive search function ===
def find_similar(user_index, k=TOP_K):
    if not (0 <= user_index < len(problems)):
        print(f"Index {user_index} is out of bounds.")
        return

    try:
        embed_index = next(i for i, (orig_idx, _) in enumerate(indexed_problems) if orig_idx == user_index)
    except StopIteration:
        source = problems[user_index].get("source", "Unknown")
        print(f"❌ Problem {user_index} — Source: {source} — missing or invalid '{EMBED_FIELD}'.")
        return

    main_embedding = embeddings[embed_index]
    main_token_embeds = all_token_embeds[embed_index]
    main_input_ids = all_input_ids[embed_index]
    main_special_mask = all_special_masks[embed_index]

    print(f"\n🔍 Problem [{user_index}] — Source: {problems[user_index].get('source', 'Unknown')}")
    print(f"Top {TOP_TOKENS_MAIN} impactful tokens in this problem's summary embedding:")
    for token, score in top_tokens(main_embedding, main_token_embeds, main_input_ids, main_special_mask, TOP_TOKENS_MAIN):
        print(f"  {token} (cosine similarity: {score:.4f})")

    cosine_scores = util.pytorch_cos_sim(main_embedding, embeddings)[0]
    top_results = torch.topk(cosine_scores, len(embeddings))

    print("\n📊 Most similar problems:\n")

    count = 0
    for score, idx in zip(top_results.values, top_results.indices):
        idx = idx.item()
        orig_idx = indexed_problems[idx][0]
        if orig_idx == user_index:
            continue

        source = problems[orig_idx].get("source", "Unknown")
        summary = problems[orig_idx].get(EMBED_FIELD, "")[:80].replace("\n", " ")
        print(f"[{orig_idx}] — {source} (Score: {score:.4f}) — \"{summary}...\"")

        sim_token_embeds = all_token_embeds[idx]
        sim_input_ids = all_input_ids[idx]
        sim_special_mask = all_special_masks[idx]

        print(f"  Top {TOP_TOKENS_SIMILAR} impactful tokens:")
        for token, score in top_tokens(embeddings[idx], sim_token_embeds, sim_input_ids, sim_special_mask, TOP_TOKENS_SIMILAR):
            print(f"    {token} (cosine similarity: {score:.4f})")

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
