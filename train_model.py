import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
)
from datasets import load_from_disk
from tqdm import tqdm
import re

# === Config ===
DATASET_PATH = "numinamath_integer_split_10pct"  # Your local dataset path
MODEL_NAME = "Qwen/Qwen1.5-0.5B"
BATCH_SIZE = 8
MAX_LENGTH = 512
OUTPUT_DIR = "./qwen-numinamath-test"

# === Load dataset ===
ds = load_from_disk(DATASET_PATH)
print(f"Dataset splits: {list(ds.keys())}")
print(f"Train size: {len(ds['train'])}")

# === Load tokenizer and model ===
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
torch_dtype = torch.float32
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME, torch_dtype=torch_dtype
)

# Device setup
device = (
    torch.device("mps")
    if torch.backends.mps.is_available()
    else torch.device("cuda" if torch.cuda.is_available() else "cpu")
)
model.to(device)
print("Using device:", device)

# === Tokenization function ===
def tokenize_function(example):
    full_text = example["problem"] + "\n" + example["solution"]
    tokens = tokenizer(
        full_text,
        truncation=True,
        max_length=MAX_LENGTH,
        padding="max_length",
    )
    # Mask padding tokens in labels
    tokens["labels"] = [
        (tok if tok != tokenizer.pad_token_id else -100)
        for tok in tokens["input_ids"]
    ]
    return tokens

# Tokenize datasets
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
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    num_train_epochs=1,
    weight_decay=0.01,
    logging_steps=10,
    report_to="none",
    push_to_hub=False,
    load_best_model_at_end=True,
    fp16=False,  # No mixed precision on MPS
    bf16=False,
)

# === Trainer ===
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets.get("validation"),
)

# === Train ===
print("Starting training with batch size =", BATCH_SIZE)
trainer.train()

# === Evaluation: exact integer match ===
def extract_first_integer(text):
    """Extract the first integer (including negative) from text, or None if none found."""
    match = re.search(r"[-]?\d+", text)
    return int(match.group()) if match else None

def evaluate_model_accuracy(model, tokenizer, dataset, max_new_tokens=32):
    model.eval()
    correct = 0
    total = 0

    for example in tqdm(dataset, desc="Evaluating"):
        prompt = example["problem"] + "\n"
        expected = example["answer"]

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
            )

        decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
        generated_text = decoded[len(prompt):].strip()

        predicted = extract_first_integer(generated_text)
        try:
            gold = int(expected)
            if predicted == gold:
                correct += 1
        except:
            pass
        total += 1

    accuracy = correct / total if total > 0 else 0.0
    print(f"\n✅ Exact Integer Match Accuracy: {accuracy:.4f} ({correct}/{total})")
    return accuracy

print("🔍 Running exact integer match evaluation on test set...")
evaluate_model_accuracy(model, tokenizer, ds["test"])
