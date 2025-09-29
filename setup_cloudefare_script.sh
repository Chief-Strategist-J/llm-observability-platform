#!/usr/bin/env bash
set -euo pipefail

PROJECT="ai-proxy"
[ -d "$PROJECT" ] && rm -rf "$PROJECT"

mkdir -p "$PROJECT/adapters/llm_provider"
mkdir -p "$PROJECT/adapters/stt_provider"
mkdir -p "$PROJECT/adapters/tts_provider"
mkdir -p "$PROJECT/core/domain"
mkdir -p "$PROJECT/core/ports"
mkdir -p "$PROJECT/core/usecases"
mkdir -p "$PROJECT/api"
mkdir -p "$PROJECT/config"

cat > "$PROJECT/requirements.txt" << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.3
httpx==0.25.2
python-multipart==0.0.6
EOF

cat > "$PROJECT/.env.example" << 'EOF'
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_API_TOKEN=your_api_token
OPENAI_API_KEY=your_openai_key
GROK_API_KEY=your_grok_key
ANTHROPIC_API_KEY=your_anthropic_key
HOST=0.0.0.0
PORT=8000
EOF

cat > "$PROJECT/config/providers.yaml" << 'EOF'
llm:
  default: cloudflare
  
  cloudflare:
    enabled: true
    model: "@cf/meta/llama-3.2-1b-instruct"
    max_tokens: 256
    temperature: 0.7
    
  openai:
    enabled: false
    model: "gpt-3.5-turbo"
    max_tokens: 256
    temperature: 0.7
    
  grok:
    enabled: false
    model: "grok-beta"
    max_tokens: 256
    temperature: 0.7
    base_url: "https://api.x.ai/v1"
    
  anthropic:
    enabled: false
    model: "claude-3-haiku-20240307"
    max_tokens: 256
    temperature: 0.7
EOF

cat > "$PROJECT/core/__init__.py" << 'EOF'
EOF

cat > "$PROJECT/core/domain/__init__.py" << 'EOF'
EOF

cat > "$PROJECT/core/domain/models.py" << 'EOF'
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class LLMRequest:
    prompt: str
    provider: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str

@dataclass
class STTRequest:
    audio_data: bytes
    provider: str

@dataclass
class STTResponse:
    text: str
    provider: str

@dataclass
class TTSRequest:
    text: str
    provider: str

@dataclass
class TTSResponse:
    audio_data: bytes
    provider: str
EOF

cat > "$PROJECT/core/ports/__init__.py" << 'EOF'
EOF

cat > "$PROJECT/core/ports/llm_provider.py" << 'EOF'
from abc import ABC, abstractmethod
from core.domain.models import LLMResponse

class LLMProviderPort(ABC):
    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int, temperature: float) -> LLMResponse:
        pass
EOF

cat > "$PROJECT/core/ports/stt_provider.py" << 'EOF'
from abc import ABC, abstractmethod
from core.domain.models import STTResponse

class STTProviderPort(ABC):
    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> STTResponse:
        pass
EOF

cat > "$PROJECT/core/ports/tts_provider.py" << 'EOF'
from abc import ABC, abstractmethod
from core.domain.models import TTSResponse

class TTSProviderPort(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> TTSResponse:
        pass
EOF

cat > "$PROJECT/core/usecases/__init__.py" << 'EOF'
EOF

cat > "$PROJECT/core/usecases/generate_text.py" << 'EOF'
from core.domain.models import LLMRequest, LLMResponse
from core.ports.llm_provider import LLMProviderPort

async def generate_text(
    request: LLMRequest,
    provider: LLMProviderPort,
    default_max_tokens: int,
    default_temperature: float
) -> LLMResponse:
    return await provider.generate(
        prompt=request.prompt,
        max_tokens=request.max_tokens or default_max_tokens,
        temperature=request.temperature or default_temperature
    )
EOF

cat > "$PROJECT/core/usecases/transcribe_audio.py" << 'EOF'
from core.domain.models import STTRequest, STTResponse
from core.ports.stt_provider import STTProviderPort

async def transcribe_audio(
    request: STTRequest,
    provider: STTProviderPort
) -> STTResponse:
    return await provider.transcribe(request.audio_data)
EOF

cat > "$PROJECT/core/usecases/synthesize_speech.py" << 'EOF'
from core.domain.models import TTSRequest, TTSResponse
from core.ports.tts_provider import TTSProviderPort

async def synthesize_speech(
    request: TTSRequest,
    provider: TTSProviderPort
) -> TTSResponse:
    return await provider.synthesize(request.text)
EOF

cat > "$PROJECT/adapters/__init__.py" << 'EOF'
EOF

cat > "$PROJECT/adapters/llm_provider/__init__.py" << 'EOF'
EOF

cat > "$PROJECT/adapters/llm_provider/cloudflare.py" << 'EOF'
import httpx
from core.ports.llm_provider import LLMProviderPort
from core.domain.models import LLMResponse

class CloudflareLLM(LLMProviderPort):
    def __init__(self, account_id: str, api_token: str, model: str):
        self.account_id = account_id
        self.api_token = api_token
        self.model = model
        self.url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    async def generate(self, prompt: str, max_tokens: int, temperature: float) -> LLMResponse:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.url,
                headers=self.headers,
                json={
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["result"]["response"],
                provider="cloudflare",
                model=self.model
            )
EOF

cat > "$PROJECT/adapters/llm_provider/openai.py" << 'EOF'
import httpx
from core.ports.llm_provider import LLMProviderPort
from core.domain.models import LLMResponse

class OpenAILLM(LLMProviderPort):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate(self, prompt: str, max_tokens: int, temperature: float) -> LLMResponse:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                provider="openai",
                model=self.model
            )
EOF

cat > "$PROJECT/adapters/llm_provider/grok.py" << 'EOF'
import httpx
from core.ports.llm_provider import LLMProviderPort
from core.domain.models import LLMResponse

class GrokLLM(LLMProviderPort):
    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.url = f"{base_url}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate(self, prompt: str, max_tokens: int, temperature: float) -> LLMResponse:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["choices"][0]["message"]["content"],
                provider="grok",
                model=self.model
            )
EOF

cat > "$PROJECT/adapters/llm_provider/anthropic.py" << 'EOF'
import httpx
from core.ports.llm_provider import LLMProviderPort
from core.domain.models import LLMResponse

class AnthropicLLM(LLMProviderPort):
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
    
    async def generate(self, prompt: str, max_tokens: int, temperature: float) -> LLMResponse:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            response.raise_for_status()
            data = response.json()
            return LLMResponse(
                text=data["content"][0]["text"],
                provider="anthropic",
                model=self.model
            )
EOF

cat > "$PROJECT/api/__init__.py" << 'EOF'
EOF

cat > "$PROJECT/api/main.py" << 'EOF'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
import os
import yaml
import logging
import sys

from core.domain.models import LLMRequest
from core.usecases.generate_text import generate_text
from adapters.llm_provider.cloudflare import CloudflareLLM
from adapters.llm_provider.openai import OpenAILLM
from adapters.llm_provider.grok import GrokLLM
from adapters.llm_provider.anthropic import AnthropicLLM

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Proxy")

config = {}
llm_providers: Dict = {}

@app.on_event("startup")
async def startup():
    global config, llm_providers
    
    with open("config/providers.yaml") as f:
        config = yaml.safe_load(f)
    
    llm_config = config["llm"]
    
    if llm_config.get("cloudflare", {}).get("enabled"):
        cf_account = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        cf_token = os.getenv("CLOUDFLARE_API_TOKEN")
        if cf_account and cf_token:
            llm_providers["cloudflare"] = CloudflareLLM(
                account_id=cf_account,
                api_token=cf_token,
                model=llm_config["cloudflare"]["model"]
            )
            logger.info("Cloudflare LLM enabled")
    
    if llm_config.get("openai", {}).get("enabled"):
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            llm_providers["openai"] = OpenAILLM(
                api_key=openai_key,
                model=llm_config["openai"]["model"]
            )
            logger.info("OpenAI LLM enabled")
    
    if llm_config.get("grok", {}).get("enabled"):
        grok_key = os.getenv("GROK_API_KEY")
        if grok_key:
            llm_providers["grok"] = GrokLLM(
                api_key=grok_key,
                model=llm_config["grok"]["model"],
                base_url=llm_config["grok"]["base_url"]
            )
            logger.info("Grok LLM enabled")
    
    if llm_config.get("anthropic", {}).get("enabled"):
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            llm_providers["anthropic"] = AnthropicLLM(
                api_key=anthropic_key,
                model=llm_config["anthropic"]["model"]
            )
            logger.info("Anthropic LLM enabled")
    
    if not llm_providers:
        logger.warning("No LLM providers configured")

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "providers": list(llm_providers.keys()),
        "default": config["llm"]["default"]
    }

class GenerateRequest(BaseModel):
    prompt: str
    provider: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None

@app.post("/generate")
async def generate(req: GenerateRequest):
    provider_name = req.provider or config["llm"]["default"]
    
    if provider_name not in llm_providers:
        raise HTTPException(400, f"Provider '{provider_name}' not available")
    
    provider = llm_providers[provider_name]
    provider_config = config["llm"][provider_name]
    
    request = LLMRequest(
        prompt=req.prompt,
        provider=provider_name,
        max_tokens=req.max_tokens,
        temperature=req.temperature
    )
    
    try:
        response = await generate_text(
            request,
            provider,
            provider_config["max_tokens"],
            provider_config["temperature"]
        )
        return {
            "text": response.text,
            "provider": response.provider,
            "model": response.model
        }
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(500, str(e))
EOF

cat > "$PROJECT/Dockerfile" << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

cat > "$PROJECT/docker-compose.yml" << 'EOF'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./config:/app/config:ro
    restart: unless-stopped
EOF

cat > "$PROJECT/start.sh" << 'EOF'
#!/bin/bash
set -e
docker compose down 2>/dev/null || true
docker compose up -d --build
sleep 5
echo "API: http://localhost:8000/docs"
EOF

cat > "$PROJECT/stop.sh" << 'EOF'
#!/bin/bash
docker compose down
EOF

chmod +x "$PROJECT/start.sh" "$PROJECT/stop.sh"

cat > "$PROJECT/.gitignore" << 'EOF'
__pycache__/
*.pyc
.env
EOF

cat > "$PROJECT/README.md" << 'EOF'
# AI Proxy

Unified API for LLM, STT, TTS providers with swappable adapters.

## Setup

```bash
cp .env.example .env
# Add your API keys
./start.sh
```

## Add Provider

1. Create adapter: `adapters/llm_provider/yourprovider.py`
2. Implement `LLMProviderPort`
3. Register in `api/main.py` startup

## Structure

```
core/
  domain/      # Data models
  ports/       # Interfaces
  usecases/    # Business logic
adapters/
  llm_provider/   # LLM implementations
  stt_provider/   # STT implementations
  tts_provider/   # TTS implementations
api/
  main.py      # FastAPI app
```
EOF

echo "Setup complete: cd $PROJECT && ./start.sh"