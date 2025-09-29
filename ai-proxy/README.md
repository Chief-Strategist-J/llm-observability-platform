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
