import json
import os
import urllib.request
import urllib.error

def format_debugger_state_with_ai(raw_transcript: str) -> str:
    """Takes the raw debugger dump and uses a lightweight AI model to format it."""
    prompt = """
You are a highly advanced debugger UI formatter. Your job is to take raw debugger output and reformat it exactly into the following ASCII UI layout.
Do NOT output markdown code blocks. Do NOT output any conversational text. Output ONLY the raw terminal text in the exact layout shown below.

TARGET LAYOUT:
╔════════════════════════════════════════════════════════════════════╗
║ BREAKPOINT                                                         ║
╠════════════════════════════════════════════════════════════════════╣
║ Location : [Class.method()]                                        ║
║ File     : [Filename:line]                                         ║
║ Thread   : [Thread Name]                                           ║
║ Time     : [Current Time]                                          ║
╚════════════════════════════════════════════════════════════════════╝

▶ Current Statement
────────────────────────────────────────────────────────────────────
[Line Number] │ [Code Line]

▶ Parameters
────────────────────────────────────────────────────────────────────
[param = value]

▶ Locals
────────────────────────────────────────────────────────────────────
[local = value]

▶ Watches
────────────────────────────────────────────────────────────────────
[Cleanly format complex objects into simple arrays or objects like arr = [1, 2, 3]]

▶ Call Path
────────────────────────────────────────────────────────────────────
[Format as: #1 function(args) File:line]

▶ Source Context
────────────────────────────────────────────────────────────────────
[Cleanly format the source code snippet, keeping the ▶ arrow on the current line. Use │ separator.]

▶ State Changes Since Last Stop
────────────────────────────────────────────────────────────────────
[List any variables that changed. Example: pi: 2 -> 4]

▶ Summary
────────────────────────────────────────────────────────────────────
[Write a 1-2 sentence extremely brief summary of what is conceptually happening in the algorithm at this step. Example: Partition complete. Left side sorted.]

RAW DEBUGGER OUTPUT TO FORMAT:
""" + raw_transcript

    provider = os.environ.get("PYLOW_AI_PROVIDER", "custom").lower()
    
    if provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return raw_transcript + "\n\n[PYLOW] Error: GEMINI_API_KEY not set. Falling back to raw output."
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}]
        }).encode("utf-8")
        
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return raw_transcript + f"\n\n[PYLOW] AI Formatting Failed: {e}"
            
    elif provider == "custom":
        # Load the custom trained model locally via HuggingFace
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            model_path = os.environ.get("PYLOW_CUSTOM_MODEL_PATH", "./pylow-custom-formatter-model")
            if not os.path.exists(model_path):
                return raw_transcript + f"\n\n[PYLOW] Error: Custom trained model not found at {model_path}. Please run train_formatter.py first!"
                
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, device_map="auto")
            
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            outputs = model.generate(**inputs, max_new_tokens=512, temperature=0.1)
            
            response = tokenizer.decode(outputs[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True)
            return response
            
        except Exception as e:
            return raw_transcript + f"\n\n[PYLOW] Custom Model Inference Failed: {e}"
            
    return raw_transcript
