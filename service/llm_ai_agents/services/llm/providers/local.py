import os
import torch
from typing import Any, Dict, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer, Pipeline, pipeline
from services.llm.base.llm import BaseLLM
from dotenv import load_dotenv

load_dotenv()

class LocalLLMProvider(BaseLLM):
    """Local LLM provider using Hugging Face Transformers."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.device = self.model_config.get("device_map", "cpu")
        self.trust_remote_code = self.model_config.get("trust_remote_code", True)
        self.load_in_8bit = self.model_config.get("load_in_8bit", False)
        
        self.hf_token = os.getenv("HF_TOKEN")
        
        self._load_model()

    def _load_model(self):
        """Lazy load the model and tokenizer."""
        if self.model is not None:
            return

        print(f"Loading local model: {self.model_id} on {self.device}...")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id, 
                token=self.hf_token,
                trust_remote_code=self.trust_remote_code
            )
            
            dtype = torch.float32
            if self.device != "cpu" and torch.cuda.is_available():
                if hasattr(torch, 'bfloat16'):
                    dtype = torch.bfloat16
            
            load_kwargs = {
                "device_map": self.device,
                "token": self.hf_token,
                "trust_remote_code": self.trust_remote_code
            }
            
            if not self.load_in_8bit:
                load_kwargs["torch_dtype"] = dtype
            else:
                load_kwargs["load_in_8bit"] = True
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                **load_kwargs
            )
            
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device_map=self.device
            )
            print(f"Model {self.model_id} loaded successfully.")
        except Exception as e:
            print(f"Error loading model {self.model_id}: {str(e)}")
            if "gated" in str(e).lower() or "401" in str(e):
                print("CRITICAL: This model is gated. Please ensure you have accepted the license on Hugging Face and set HF_TOKEN.")
            raise

    def generate(self, prompt: str, **kwargs) -> str:
        if not self.pipeline:
            self._load_model()
            
        params = self.model_config.get("parameters", {})
        temperature = kwargs.get("temperature", params.get("temperature", 0.7))
        top_p = kwargs.get("top_p", params.get("top_p", 0.95))
        
        temperature = max(0.1, min(temperature, 2.0))
        top_p = max(0.1, min(top_p, 1.0))
        
        gen_kwargs = {
            "max_new_tokens": kwargs.get("max_tokens", params.get("max_tokens", 512)),
            "temperature": temperature,
            "top_p": top_p,
            "do_sample": temperature > 0,
            "repetition_penalty": 1.0,
            "pad_token_id": self.tokenizer.eos_token_id if self.tokenizer.eos_token_id is not None else 0,
            "use_cache": True,
        }
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            if hasattr(self.tokenizer, "apply_chat_template"):
                formatted_prompt = self.tokenizer.apply_chat_template(
                    messages, 
                    tokenize=False, 
                    add_generation_prompt=True
                )
            else:
                formatted_prompt = prompt

            outputs = self.pipeline(
                formatted_prompt,
                **gen_kwargs
            )
            
            generated_text = outputs[0]["generated_text"]
            
            if generated_text.startswith(formatted_prompt):
                response = generated_text[len(formatted_prompt):].strip()
            else:
                response = generated_text.strip()
                
            return response
        except Exception as e:
            return f"Error during generation: {str(e)}"

    def stream_generate(self, prompt: str, **kwargs):
        """Stream response from the local model."""
        if not self.model:
            self._load_model()

        from transformers import TextIteratorStreamer
        from threading import Thread

        params = self.model_config.get("parameters", {})
        temperature = kwargs.get("temperature", params.get("temperature", 0.7))
        top_p = kwargs.get("top_p", params.get("top_p", 0.95))
        max_new_tokens = kwargs.get("max_tokens", params.get("max_tokens", 512))

        streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
        
        messages = [{"role": "user", "content": prompt}]
        if hasattr(self.tokenizer, "apply_chat_template"):
            formatted_prompt = self.tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
        else:
            formatted_prompt = prompt
            
        inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.device)
        
        gen_kwargs = {
            **inputs,
            "streamer": streamer,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "do_sample": temperature > 0,
            "pad_token_id": self.tokenizer.eos_token_id if self.tokenizer.eos_token_id is not None else 0,
            "use_cache": True,
        }
        
        thread = Thread(target=self.model.generate, kwargs=gen_kwargs)
        thread.start()
        
        for new_text in streamer:
            yield new_text

    async def generate_async(self, prompt: str, **kwargs) -> str:
        """Wrapper for async generation."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.generate(prompt, **kwargs))

    async def astream_generate(self, prompt: str, **kwargs):
        """Async wrapper for streaming generation."""
        import asyncio
        loop = asyncio.get_event_loop()
        for token in self.stream_generate(prompt, **kwargs):
            yield token
            await asyncio.sleep(0)

    def get_langchain_model(self) -> Any:
        """Return the pipeline wrapped in a LangChain object."""
        if self.pipeline is None:
            self._load_model()
        from langchain_huggingface import HuggingFacePipeline
        return HuggingFacePipeline(pipeline=self.pipeline)
