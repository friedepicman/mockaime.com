#!/usr/bin/env python3
"""
TensorFlow alternative to PyTorch training
Sometimes TensorFlow GPU setup is easier than PyTorch
"""

import tensorflow as tf
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
from datasets import load_from_disk
import numpy as np
from sklearn.metrics import accuracy_score
import os

# Check GPU
print("TensorFlow version:", tf.__version__)
gpus = tf.config.list_physical_devices('GPU')
print(f"GPUs available: {len(gpus)}")

# Enable GPU memory growth
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print("✅ GPU memory growth enabled")
    except RuntimeError as e:
        print(f"GPU setup error: {e}")
        
# Set mixed precision for faster training
tf.keras.mixed_precision.set_global_policy('mixed_float16')
print("✅ Mixed precision enabled")

# === Config ===
DATASET_PATH = "numinamath_1.5_split_10pct"
MODEL_NAME = "Qwen/Qwen1.5-0.5B"
BATCH_SIZE = 16
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
    ds[split] = ds[split].map(convert_labels)

# === Load tokenizer and model ===
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Use TensorFlow model instead of PyTorch
model = TFAutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(problem_types),
    id2label=id2label,
    label2id=label2id,
    from_tf=True  # Use TensorFlow weights
)

# === Tokenize data ===
def tokenize_function(examples):
    return tokenizer(
        examples["problem"],
        truncation=True,
        max_length=MAX_LENGTH,
        padding="max_length",
        return_tensors="tf"
    )

# Tokenize datasets
tokenized_train = ds["train"].map(tokenize_function, batched=True)
tokenized_val = ds["validation"].map(tokenize_function, batched=True)

# Convert to TensorFlow datasets
def make_tf_dataset(dataset):
    features = {
        "input_ids": np.array(dataset["input_ids"]),
        "attention_mask": np.array(dataset["attention_mask"]),
    }
    labels = np.array(dataset["labels"])
    
    tf_dataset = tf.data.Dataset.from_tensor_slices((features, labels))
    tf_dataset = tf_dataset.batch(BATCH_SIZE)
    tf_dataset = tf_dataset.prefetch(tf.data.AUTOTUNE)
    return tf_dataset

train_dataset = make_tf_dataset(tokenized_train)
val_dataset = make_tf_dataset(tokenized_val)

# === Compile model ===
optimizer = tf.keras.optimizers.Adam(learning_rate=2e-5)
model.compile(
    optimizer=optimizer,
    loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=['accuracy']
)

# === Train ===
print("Starting training...")
with tf.device('/GPU:0' if tf.config.list_physical_devices('GPU') else '/CPU:0'):
    history = model.fit(
        train_dataset,
        validation_data=val_dataset,
        epochs=3,
        verbose=1
    )

# === Save model ===
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

print("Training completed!")
print(f"Model saved to: {OUTPUT_DIR}")