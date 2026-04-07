import os
import yaml
import argparse
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--prompt", type=str, default="Hello")
    args = parser.parse_args()

    config = load_config(args.config)['model']
    model_id = config['id']

    bnb_config = None
    if config.get('quantization') == "4bit":
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map=config.get('device_map', 'auto'),
        trust_remote_code=config.get('trust_remote_code', True)
    )

    inputs = tokenizer(args.prompt, return_tensors="pt").to(model.device)
    
    outputs = model.generate(
        **inputs,
        max_new_tokens=config['parameters'].get('max_tokens', 512),
        temperature=config['parameters'].get('temperature', 0.7),
        top_p=config['parameters'].get('top_p', 0.95),
        do_sample=True
    )
    
    print(tokenizer.decode(outputs[0], skip_special_tokens=True))

if __name__ == "__main__":
    main()
