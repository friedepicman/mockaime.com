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
BATCH_SIZE = 1
MAX_LENGTH = 512
OUTPUT_DIR = "./qwen-problemtype-classification"

# === Load dataset ===
ds = load_from_disk(DATASET_PATH)
print(f"Dataset splits: {list(ds.keys())}")
print(f"Train size: {len(ds['train'])}")

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
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(problem_types),
    id2label=id2label,
    label2id=label2id,
    torch_dtype=torch.float32
)

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
    eval_strategy="steps",     # eval every N steps
    eval_steps=5000, 
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_steps=10,
    report_to="none",
    push_to_hub=False,
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    fp16=False,
    bf16=False,
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
