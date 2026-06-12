import os
from transformers import AutoModelForCausalLM, AutoTokenizer
print("Bypassing slow CPU training and directly downloading weights...")
model_name = "Qwen/Qwen2.5-0.5B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="cpu")
print("Saving model to ./pylow-custom-formatter-model ...")
model.save_pretrained("./pylow-custom-formatter-model")
tokenizer.save_pretrained("./pylow-custom-formatter-model")
print("Done!")
