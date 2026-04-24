"""Canonical Cloudflare Workers AI catalog presets (virtual, no yaml files required)."""

CLOUDFLARE_MODELS = [
    ("aisingapore/gemma-sea-lion-v4-27b-it", "@cf/aisingapore/gemma-sea-lion-v4-27b-it", "Cloudflare Workers AI - SEA-LION v4 27B IT"),
    ("deepseek/deepseek-r1-distill-qwen-32b", "@cf/deepseek/deepseek-r1-distill-qwen-32b", "Cloudflare Workers AI - DeepSeek R1 Distill Qwen 32B"),
    ("google/gemma-3-12b-it", "@cf/google/gemma-3-12b-it", "Cloudflare Workers AI - Google Gemma 3 12B IT"),
    ("google/gemma-4-26b-a4b-it", "@cf/google/gemma-4-26b-a4b-it", "Cloudflare Workers AI - Google Gemma 4 26B A4B IT"),
    ("ibm/granite-4.0-h-micro", "@cf/ibm/granite-4.0-h-micro", "Cloudflare Workers AI - IBM Granite 4.0 H Micro"),
    ("meta/llama-3.1-70b-instruct", "@cf/meta/llama-3.1-70b-instruct", "Cloudflare Workers AI - Meta Llama 3.1 70B Instruct"),
    ("meta/llama-3.1-8b-instruct", "@cf/meta/llama-3.1-8b-instruct", "Cloudflare Workers AI - Meta Llama 3.1 8B Instruct"),
    ("meta/llama-3.1-8b-instruct-fp8", "@cf/meta/llama-3.1-8b-instruct-fp8", "Cloudflare Workers AI - Meta Llama 3.1 8B Instruct FP8"),
    ("meta/llama-3.2-11b-vision-instruct", "@cf/meta/llama-3.2-11b-vision-instruct", "Cloudflare Workers AI - Meta Llama 3.2 11B Vision Instruct"),
    ("meta/llama-3.2-1b-instruct", "@cf/meta/llama-3.2-1b-instruct", "Cloudflare Workers AI - Meta Llama 3.2 1B Instruct"),
    ("meta/llama-3.2-3b-instruct", "@cf/meta/llama-3.2-3b-instruct", "Cloudflare Workers AI - Meta Llama 3.2 3B Instruct"),
    ("meta/llama-3.3-70b-instruct-fp8-fast", "@cf/meta/llama-3.3-70b-instruct-fp8-fast", "Cloudflare Workers AI - Meta Llama 3.3 70B Instruct FP8 Fast"),
    ("meta/llama-4-scout-17b-16e-instruct", "@cf/meta/llama-4-scout-17b-16e-instruct", "Cloudflare Workers AI - Meta Llama 4 Scout 17B 16E Instruct"),
    ("meta/llama-guard-3-8b", "@cf/meta/llama-guard-3-8b", "Cloudflare Workers AI - Meta Llama Guard 3 8B"),
    ("meta/meta-llama-3-8b-instruct", "@cf/meta/meta-llama-3-8b-instruct", "Cloudflare Workers AI - Meta Llama 3 8B Instruct"),
    ("mistralai/mistral-small-3.1-24b-instruct", "@cf/mistralai/mistral-small-3.1-24b-instruct", "Cloudflare Workers AI - Mistral Small 3.1 24B Instruct"),
    ("moonshot-ai/kimi-k2.5", "@cf/moonshot-ai/kimi-k2.5", "Cloudflare Workers AI - Moonshot AI Kimi K2.5"),
    ("moonshot-ai/kimi-k2.6", "@cf/moonshot-ai/kimi-k2.6", "Cloudflare Workers AI - Moonshot AI Kimi K2.6"),
    ("nvidia/nemotron-3-120b-a12b", "@cf/nvidia/nemotron-3-120b-a12b", "Cloudflare Workers AI - NVIDIA Nemotron 3 120B A12B"),
    ("openai/gpt-oss-120b", "@cf/openai/gpt-oss-120b", "Cloudflare Workers AI - OpenAI gpt-oss-120b"),
    ("openai/gpt-oss-20b", "@cf/openai/gpt-oss-20b", "Cloudflare Workers AI - OpenAI gpt-oss-20b"),
    ("qwen/qwen2.5-coder-32b-instruct", "@cf/qwen/qwen2.5-coder-32b-instruct", "Cloudflare Workers AI - Qwen2.5 Coder 32B Instruct"),
    ("qwen/qwen3-30b-a3b-fp8", "@cf/qwen/qwen3-30b-a3b-fp8", "Cloudflare Workers AI - Qwen3 30B A3B FP8"),
    ("qwen/qwq-32b", "@cf/qwen/qwq-32b", "Cloudflare Workers AI - Qwen QwQ 32B"),
    ("zhipu-ai/glm-4.7-flash", "@cf/zhipu-ai/glm-4.7-flash", "Cloudflare Workers AI - Zhipu AI GLM 4.7 Flash"),
]


def build_cloudflare_virtual_records():
    records = []
    for slug, model_id, name in CLOUDFLARE_MODELS:
        key = f"catalog/cloudflare/{slug}"
        config = {
            "model": {
                "id": model_id,
                "name": name,
                "provider": "cloudflare",
                "parameters": {"temperature": 0.7, "max_tokens": 1024},
            }
        }
        records.append(
            {
                "key": key,
                "source": "cloudflare_catalog",
                "provider": "cloudflare",
                "id": model_id,
                "name": name,
                "config": config,
            }
        )
    return records
