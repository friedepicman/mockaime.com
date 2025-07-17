import torch
from transformers import AutoTokenizer, AutoModel
from datasets import load_from_disk
from tqdm import tqdm
from torch.cuda.amp import autocast

# === CONFIGURATION ===
DATASET_PATH = "numina_splits"  # folder where your dataset is saved
OUTPUT_PATH = "numinamath_with_embeddings"  # folder to save dataset with embeddings
TEXT_FIELD = "solution"  # field to embed
BATCH_SIZE = 64  # increased batch size for better GPU utilization
MAX_LENGTH = 256

# === LOAD DATASET ===
ds = load_from_disk(DATASET_PATH)

# === LOAD MODEL & TOKENIZER ===
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained("./mlm_trained_model")
model = AutoModel.from_pretrained("./mlm_trained_model")
model = model.to(device)
model.eval()

def embed_texts(texts):
    all_embeddings = []
    for i in tqdm(range(0, len(texts), BATCH_SIZE)):
        batch_texts = texts[i:i+BATCH_SIZE]
        inputs = tokenizer(batch_texts, padding=True, truncation=True, max_length=MAX_LENGTH, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            # Use autocast for mixed precision inference on GPU
            with autocast(enabled=device.type == 'cuda'):
                outputs = model(**inputs)
                last_hidden_state = outputs.last_hidden_state  # (batch_size, seq_len, hidden_size)
                cls_embeddings = last_hidden_state[:, 0, :]    # CLS token embedding
                cls_embeddings = torch.nn.functional.normalize(cls_embeddings, p=2, dim=1)
                all_embeddings.append(cls_embeddings.cpu())
    return torch.cat(all_embeddings, dim=0).tolist()

# === PROCESS EACH SPLIT ===
for split in ds.keys():
    print(f"Processing split: {split}")
    dataset = ds[split]
    texts = dataset[TEXT_FIELD]
    embeddings = embed_texts(texts)
    ds[split] = dataset.add_column("embedding", embeddings)

# === SAVE UPDATED DATASET ===
ds.save_to_disk(OUTPUT_PATH)
print(f"✅ Saved dataset with embeddings to: {OUTPUT_PATH}")
