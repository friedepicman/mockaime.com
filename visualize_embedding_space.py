import json
import torch
import umap
import plotly.express as px
from sentence_transformers import SentenceTransformer

# === Load problems ===
with open("all_problems_cleaned_with_source.json", "r") as f:
    problems = json.load(f)

texts = [p["solution_summary"] for p in problems if "solution_summary" in p]
sources = [p["source"] for p in problems if "solution_summary" in p]
difficulties = [p.get("difficulty", 0) for p in problems if "solution_summary" in p]

# === Load model & compute embeddings ===
model = SentenceTransformer("./mlm_trained_model")
embeddings = model.encode(texts, convert_to_tensor=True, show_progress_bar=True)

# === UMAP to 3D ===
reducer = umap.UMAP(n_components=3, n_neighbors=15, min_dist=0.1, metric="cosine")
embeddings_3d = reducer.fit_transform(embeddings.cpu().numpy())

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
