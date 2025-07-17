import json
from datasets import Dataset
from transformers import (
    BertTokenizerFast,
    BertForMaskedLM,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)
import torch

# Load data
with open("all_problems_with_masked_summary.json", "r") as f:
    data = json.load(f)

# Filter for items that contain [MASK] in the masked_summary
filtered = [item for item in data if "masked_summary" in item and "[MASK]" in item["masked_summary"]]


print(f"✅ Using {len(filtered)} training examples with [MASK] tokens.")

# Create Hugging Face Dataset
dataset = Dataset.from_list([{"text": item["masked_summary"]} for item in filtered])

# Load tokenizer and model
tokenizer = BertTokenizerFast.from_pretrained("bert-base-uncased")
model = BertForMaskedLM.from_pretrained("bert-base-uncased")

# Tokenization function
def tokenize(example):
    return tokenizer(
        example["text"],
        padding="max_length",
        truncation=True,
        max_length=256,
        return_special_tokens_mask=True,
    )

tokenized_dataset = dataset.map(tokenize, batched=True)
tokenized_dataset.set_format(type="torch", columns=["input_ids", "attention_mask", "special_tokens_mask"])

# MLM-specific data collator
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=True,
    mlm_probability=0.15
)

# Training arguments
training_args = TrainingArguments(
    output_dir="./mlm_output",
    overwrite_output_dir=True,
    num_train_epochs=4,
    per_device_train_batch_size=8,
    save_steps=500,
    save_total_limit=2,
    logging_steps=100,
    logging_dir="./logs",
    report_to="none"
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator
)

# Train the model
print("🚀 Starting training...")
trainer.train()

# Save final model
model.save_pretrained("./mlm_trained_model")
tokenizer.save_pretrained("./mlm_trained_model")
print("✅ Model saved to ./mlm_trained_model")
