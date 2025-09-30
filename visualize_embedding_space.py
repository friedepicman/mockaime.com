import json
import torch
import umap
import plotly.express as px
from transformers import BertTokenizer, BertModel

# === Load problems ===
with open("all_problems_cleaned_with_source.json", "r") as f:
    problems = json.load(f)

texts = [p["solution_summary"] for p in problems if "solution_summary" in p]
sources = [p["source"] for p in problems if "solution_summary" in p]
difficulties = [p.get("difficulty", 0) for p in problems if "solution_summary" in p]

# === Load HuggingFace-style BERT model ===
model_path = "/Users/jasonyuan/Documents/git/math/mlm_trained_model"
tokenizer = BertTokenizer.from_pretrained(model_path)
model = BertModel.from_pretrained(model_path)
model.eval()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# === Compute embeddings using [CLS] token ===
def encode_texts(texts, tokenizer, model, batch_size=32):
    embeddings = []
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            inputs = tokenizer(batch, padding=True, truncation=True, return_tensors="pt", max_length=512)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            outputs = model(**inputs)
            cls_embeddings = outputs.last_hidden_state[:, 0, :]  # CLS token
            embeddings.append(cls_embeddings.cpu())
    return torch.cat(embeddings, dim=0)

embeddings = encode_texts(texts, tokenizer, model)

# === UMAP to 3D ===
reducer = umap.UMAP(n_components=3, n_neighbors=15, min_dist=0.1, metric="cosine")
embeddings_3d = reducer.fit_transform(embeddings.numpy())

# === Create Plotly scatter plot ===
fig = px.scatter_3d(
    x=embeddings_3d[:, 0],
    y=embeddings_3d[:, 1],
    z=embeddings_3d[:, 2],
    color=difficulties,
    hover_name=sources,
    title="3D Embedding Space of Solution Summaries",
    labels={"color": "Difficulty"},
    opacity=0.7,
)

fig.update_traces(marker=dict(size=4))
fig.show()
