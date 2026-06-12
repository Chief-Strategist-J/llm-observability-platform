"""
Fine-tuning script for Qwen2.5-0.5B using HuggingFace Transformers and LoRA.
This script requires a dataset of raw JDB output mapped to your perfect UI boxes.
"""

import os
import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

def train_model():
    model_name = "Qwen/Qwen2.5-0.5B-Instruct"
    dataset_path = "dataset.jsonl" # YOU MUST CREATE THIS FILE WITH 500+ EXAMPLES!

    if not os.path.exists(dataset_path):
        print("ERROR: You must manually create 'dataset.jsonl' first!")
        print("Format each line as: {\"input\": \"RAW JDB OUTPUT\", \"output\": \"YOUR ASCII BOXES\"}")
        return

    print("Loading 400MB Model and Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        torch_dtype=torch.float16
    )

    # Configure LoRA to make training fast and lightweight
    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    model = get_peft_model(model, lora_config)

    print("Loading your custom dataset...")
    dataset = load_dataset("json", data_files=dataset_path, split="train")

    def format_prompts(example):
        return {
            "text": f"Instruction: Format this debug log:\n{example['input']}\n\nOutput:\n{example['output']}"
        }
    
    dataset = dataset.map(format_prompts)

    from trl import SFTConfig

    training_args = SFTConfig(
        output_dir="./pylow-custom-formatter-model",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        logging_steps=1,
        max_steps=1,
        fp16=True,
        dataset_text_field="text",
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        args=training_args,
    )

    print("Starting Training...")
    trainer.train()
    
    print("Saving your custom formatted model!")
    trainer.model.save_pretrained("./pylow-custom-formatter-model")
    tokenizer.save_pretrained("./pylow-custom-formatter-model")

if __name__ == "__main__":
    train_model()
