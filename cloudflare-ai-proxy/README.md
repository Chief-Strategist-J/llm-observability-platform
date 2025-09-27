# Cloudflare AI Proxy

A fast, minimal FastAPI microservice that provides a clean REST API for Cloudflare Workers AI.

## Features

- 🚀 **Fast**: Optimized for low latency with async HTTP client
- 💰 **Cost-effective**: Uses Cloudflare's cheap AI models
- 🔧 **Hot-swappable**: Change models without rebuilding containers
- 🐳 **Docker ready**: Production-ready containerization
- 📊 **Monitoring**: Health checks and request timing
- 🛡️ **Secure**: Non-root containers with proper error handling

## Quick Start

1. **Setup environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Cloudflare credentials
   ```

2. **Run with Docker**:
   ```bash
   docker-compose up -d
   ```

3. **Test the API**:
   ```bash
   # Health check
   curl http://localhost:8080/health

   # Generate text
   curl -X POST http://localhost:8080/v1/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello, how are you?"}'
   ```

## API Endpoints

- `GET /` - Service info
- `GET /health` - Health check with Cloudflare API status
- `POST /v1/generate` - Generate text

## Configuration

Edit `configs/model.yaml` to change models without rebuilding:

```yaml
model_id: "@cf/meta/llama-3.2-1b-instruct"
inference:
  max_tokens: 256
  temperature: 0.7
  top_p: 0.95
```

## Development

```bash
# Local development
make dev

# Development with Docker (hot reload)
make up-dev
```

## Available Models

- `@cf/meta/llama-3.2-1b-instruct` (default - fastest, cheapest)
- `@cf/meta/llama-3.1-8b-instruct`
- `@cf/mistral/mistral-7b-instruct-v0.1`
- `@cf/microsoft/phi-2`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CF_ACCOUNT_ID` | Cloudflare Account ID | ✅ |
| `CF_API_TOKEN` | Cloudflare API Token | ✅ |
| `MODEL_ID` | Override model from config | ❌ |
| `HOST` | Server host | ❌ |
| `PORT` | Server port | ❌ |

## Pricing

Cloudflare Workers AI pricing (as of 2024):
- Free tier: 10,000 requests/day
- Pay-as-you-go: ~$0.001-0.01 per request (model dependent)

## License

MIT License
