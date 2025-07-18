import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from datasets import load_from_disk, ClassLabel
from sklearn.metrics import accuracy_score
from tqdm import tqdm

# === Config ===
DATASET_PATH = "numinamath_1.5_split_10pct"
MODEL_NAME = "Qwen/Qwen1.5-0.5B"

# === Quick test mode (comment out for full training) ===
QUICK_TEST = True  # Set to False for full training

# === GPU-specific settings ===
# For NVIDIA GPUs, your dad should modify these:
if torch.cuda.is_available():
    BATCH_SIZE = 16  # Can probably go higher on modern GPUs
    MAX_LENGTH = 512  # Full length for better accuracy
    USE_FP16 = True  # Enable mixed precision for speed
    print("🚀 CUDA detected - using GPU-optimized settings")
else:
    BATCH_SIZE = 2  # Small for Mac testing
    MAX_LENGTH = 256  # Shorter for faster testing
    USE_FP16 = False  # Mac compatibility
    print("🍎 Using CPU/MPS settings")

OUTPUT_DIR = "./qwen-problemtype-classification"

# === Load dataset ===
ds = load_from_disk(DATASET_PATH)
print(f"Dataset splits: {list(ds.keys())}")
print(f"Train size: {len(ds['train'])}")
print(f"Validation size: {len(ds['validation'])}")
print(f"Test size: {len(ds['test'])}")

# Quick test mode - use smaller subset
if QUICK_TEST:
    print("🚀 QUICK TEST MODE - Using smaller dataset")
    
    # Use smaller subsets but don't exceed actual dataset sizes
    train_size = min(1000, len(ds['train']))
    val_size = min(200, len(ds['validation']))
    test_size = min(200, len(ds['test']))
    
    ds['train'] = ds['train'].select(range(train_size))
    ds['validation'] = ds['validation'].select(range(val_size))
    ds['test'] = ds['test'].select(range(test_size))
    
    print(f"Reduced train size: {len(ds['train'])}")
    print(f"Reduced validation size: {len(ds['validation'])}")
    print(f"Reduced test size: {len(ds['test'])}")

# Print problem types of first 10 problems in train split
print("\nFirst 10 problem types in train split:")
for i in range(10):
    print(f"{i+1}: {ds['train'][i]['problem_type']}")

# === Define labels ===
problem_types = [
    "Algebra", "Geometry", "Number Theory", "Combinatorics",
    "Calculus", "Inequalities", "Logic and Puzzles", "Other"
]
label2id = {label: i for i, label in enumerate(problem_types)}
id2label = {i: label for label, i in label2id.items()}

# === Convert labels to integers ===
def convert_labels(example):
    example["labels"] = label2id.get(example["problem_type"], label2id["Other"])
    return example

for split in ds.keys():
    print(ds["train"].column_names)
    ds[split] = ds[split].map(convert_labels)

# === Error if too many "Other" labels ===
num_other = sum(1 for x in ds["train"]["labels"] if x == label2id["Other"])
total = len(ds["train"])
if num_other > total // 2:
    raise ValueError(f"🚨 More than 50% of training examples are labeled 'Other' ({num_other}/{total}). Check problem_type formatting.")

# === Load tokenizer and model ===
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

# FIX: Add padding token if it doesn't exist
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.pad_token_id = tokenizer.eos_token_id
    print(f"Added padding token: {tokenizer.pad_token} (ID: {tokenizer.pad_token_id})")

# Debug: Print tokenizer info
print(f"Tokenizer pad_token: {tokenizer.pad_token}")
print(f"Tokenizer pad_token_id: {tokenizer.pad_token_id}")
print(f"Tokenizer eos_token: {tokenizer.eos_token}")
print(f"Tokenizer eos_token_id: {tokenizer.eos_token_id}")

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(problem_types),
    id2label=id2label,
    label2id=label2id,
    torch_dtype=torch.float32,
    pad_token_id=tokenizer.pad_token_id  # Explicitly set pad_token_id
)

# FIX: Resize token embeddings if we added a new token
model.resize_token_embeddings(len(tokenizer))

# FIX: Explicitly set the model's pad_token_id
model.config.pad_token_id = tokenizer.pad_token_id
print(f"Model pad_token_id set to: {model.config.pad_token_id}")

# Device setup
device = (
    torch.device("mps")
    if torch.backends.mps.is_available()
    else torch.device("cuda" if torch.cuda.is_available() else "cpu")
)
model.to(device)
print("Using device:", device)

# === Tokenize input ===
def tokenize_function(example):
    text = example["problem"]
    tokens = tokenizer(
        text,
        truncation=True,
        max_length=MAX_LENGTH,
        padding="max_length"
    )
    tokens["labels"] = example["labels"]
    return tokens

tokenized_datasets = {}
for split in ds.keys():
    print(f"Tokenizing {split} split...")
    tokenized_datasets[split] = ds[split].map(
        tokenize_function,
        batched=False,
        remove_columns=ds[split].column_names,
    )

# === Training arguments ===
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    eval_strategy="steps",
    eval_steps=500 if QUICK_TEST else 5000,  # More frequent eval in test mode
    save_strategy="steps",
    save_steps=500 if QUICK_TEST else 5000,
    learning_rate=2e-5,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    num_train_epochs=1 if QUICK_TEST else 3,  # Just 1 epoch for testing
    weight_decay=0.01,
    logging_steps=10,
    report_to="none",
    push_to_hub=False,
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    fp16=USE_FP16,  # Enable mixed precision on GPU
    bf16=False,
    dataloader_pin_memory=False,
)

# === Compute metrics ===
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = torch.argmax(torch.tensor(logits), dim=-1).numpy()
    acc = accuracy_score(labels, predictions)
    return {"accuracy": acc}

# === Trainer ===
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets.get("validation"),
    compute_metrics=compute_metrics,
)

# === Train ===
print("Starting training with batch size =", BATCH_SIZE)
trainer.train()

# === Evaluate on test set ===
print("🔍 Final evaluation on test set...")
metrics = trainer.evaluate(tokenized_datasets["test"])
print("Test set metrics:", metrics)