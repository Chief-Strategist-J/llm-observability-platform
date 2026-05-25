# AI Service

This service acts as an AI Orchestrator that integrates with Cloudflare's AI Gateway/Workers API. It implements stateful, persistent chat sessions with a high-performance in-memory memory repository, semantic context retrieval via cosine similarity, and OpenTelemetry instrumentation.

---

## Architecture Flow

The following hierarchical structure illustrates the HTTP request routing, Dependency Injection layout, Port/Adapter boundary, and external integration points of the AI Orchestrator:

```
└── HTTP Client (Frontend / API consumer)
    └── [POST /api/v1/chat or /chat/persistent]
        └── HTTP Router (src/api/rest/v1/router.go)
            └── Route Matching & Middleware Injection
                └── AI Handlers (src/api/rest/v1/handlers/ai_handlers.go)
                    ├── Dependency Injection Container (src/shared/di/providers.go)
                    │   └── Resolves and injects the Orchestrator Service
                    │
                    └── AI Orchestrator Service (src/features/ai_orchestrator/service.go)
                        ├── Port: CloudflareClient (src/features/ai_orchestrator/ports.go)
                        │   └── Adapter: CloudflareAdapter (src/infra/adapters/cloudflare_adapter.go)
                        │       └── REST Calls -> External Cloudflare AI Gateway/Workers API
                        │
                        ├── Port: MemoryRepository (src/features/ai_orchestrator/ports.go)
                        │   └── Adapter: MemoryRepository (src/infra/adapters/memory_repo.go)
                        │       └── Thread-safe In-Memory Vector DB (Cosine Similarity retrieval)
                        │
                        ├── Port: VectorRepositoryPort (src/features/ai_orchestrator/ports.go)
                        │   └── Adapter: QdrantRepository (src/infra/adapters/qdrant_repo.go)
                        │       └── Qdrant REST API Vector Store (Semantic memory & point upserts)
                        │
                        ├── Port: ResponseCachePort (src/features/ai_orchestrator/ports.go)
                        │   └── Adapter: MemoryResponseCache (src/infra/adapters/memory_cache.go)
                        │       └── High-performance In-Memory Standard Caching (exact match)
                        │
                        └── Port: SemanticCachePort (src/features/ai_orchestrator/ports.go)
                            └── Adapter: QdrantSemanticCache (src/infra/adapters/qdrant_cache.go)
                                └── Vector-based Semantic Caching (Qdrant similarity search)
```

---

## Decision Tree (Chat Flow Execution)

This hierarchical decision tree outlines the conditional execution paths for stateless vs. stateful chat requests:

```
└── Incoming Chat Request
    ├── Route: /api/v1/chat (Stateless Flow)
    │   ├── [Step 1] Parse payload (messages list)
    │   ├── [Step 2] Lookup in standard cache via hash key of prompt history
    │   │   ├── Hit -> Return cached response (cached: true, cache_type: "standard")
    │   │   └── Miss -> Proceed to step 3
    │   ├── [Step 3] Query semantic cache (threshold: 0.92) using user message embedding
    │   │   ├── Hit -> Store in standard cache, return cached response (cached: true, cache_type: "semantic")
    │   │   └── Miss -> Proceed to step 4
    │   ├── [Step 4] Send messages directly to Cloudflare LLM
    │   └── [Step 5] Store response in standard and semantic cache, return response (cached: false)
    │
    └── Route: /api/v1/chat/persistent (Stateful Flow)
        ├── [Step 1] Parse payload (user_id, message text)
        ├── [Step 2] Generate embedding vector for user message via Cloudflare AI
        ├── [Step 3] Fetch user memory history from In-Memory Memory Repository / Qdrant Vector Store
        ├── [Decision] Does user have past conversational memory?
        │   ├── YES (Retrieve Context)
        │   │   ├── [Sub-Step] Query Memory Repository / Qdrant via cosine similarity with user_id filter
        │   │   ├── [Sub-Step] Filter and sort memories where similarity >= threshold (default: 0.7)
        │   │   ├── [Sub-Step] Select top K context-rich memories (default: 5)
        │   │   └── [Sub-Step] Prepend retrieved context to the prompt as system instructions
        │   └── NO (Skip Context Retrieval)
        │       └── [Sub-Step] Proceed with empty conversational history context
        │
        ├── [Step 4] Lookup full compiled prompt in standard cache via hash key
        │   ├── Hit -> Return cached response (cached: true, cache_type: "standard")
        │   └── Miss -> Proceed to step 5
        │
        ├── [Step 5] Query semantic cache (threshold: 0.92) using user message embedding
        │   ├── Hit -> Store in standard cache, return cached response (cached: true, cache_type: "semantic")
        │   └── Miss -> Proceed to step 6
        │
        ├── [Step 6] Send complete prompt (context + current message) to Cloudflare LLM
        ├── [Step 7] Receive LLM AI response text
        ├── [Step 8] Generate embedding vector for assistant response text via Cloudflare AI
        ├── [Step 9] Store response in standard cache and semantic cache
        ├── [Step 10] Atomically store both User and Assistant turns in Memory Repository and Qdrant
        └── [Step 11] Return AI response + semantic context metadata to the client (cached: false)
```

---

## Folder Structure

```
.
├── Dockerfile
├── docker-compose.yaml
├── go.mod
├── go.sum
├── test_api.sh
├── test_cloudflare_real.sh
├── contracts/
│   ├── changelog.md
│   └── openapi/
│       └── v1.yaml
├── scripts/
│   └── deploy_docker.sh
└── src/
    ├── main.go
    ├── api/
    │   └── rest/
    │       └── v1/
    │           ├── router.go
    │           └── handlers/
    │               └── ai_handlers.go
    ├── features/
    │   └── ai_orchestrator/
    │       ├── index.go
    │       ├── ports.go
    │       ├── service.go
    │       └── types.go
    ├── infra/
    │   └── adapters/
    │       ├── cloudflare_adapter.go
    │       ├── memory_repo.go
    │       └── qdrant_repo.go
    └── shared/
        ├── di/
        │   └── providers.go
        └── tracing/
            └── otel.go
```

**Key components:** Multi-stage `Dockerfile`, OpenAPI `contracts`, automated `deploy_docker.sh` release script, Hexagonal Domain layer `ai_orchestrator`, and Cloudflare API + In-Memory Vector / Qdrant `adapters`.

---

## Build and Deploy

### Environment Variables

The service is configured using the following environment variables:

| Variable | Description | Default Value |
| :--- | :--- | :--- |
| `PORT` | The port the HTTP server binds to | `8080` |
| `CF_ACCOUNT_ID` | Cloudflare Account ID | `local-account` (Triggers mock mode if default) |
| `CF_API_TOKEN` | Cloudflare AI Workers Token (`cfut_...`) | `local-token` (Triggers mock mode if default) |
| `CF_ACCESS_JWT_ASSERTION` | Cloudflare Access API Token (`cfat_...`) | Optional / None |
| `CF_EMBEDDING_MODEL` | The default text embedding model ID | `@cf/baai/bge-small-en-v1.5` |
| `AI_DEFAULT_MODEL` | The default chat/LLM model ID | `@cf/meta/llama-3.1-8b-instruct` |
| `QDRANT_URL` | Qdrant REST API endpoint URL | Optional / None |
| `QDRANT_API_KEY` | Optional API Key for Qdrant | Optional / None |
| `QDRANT_COLLECTION` | Qdrant Collection name for storing vectors | `chat_messages` |
| `QDRANT_SEMANTIC_CACHE_COLLECTION` | Qdrant Collection name for storing semantic cache vectors | `semantic_cache` |
| `QDRANT_VECTOR_SIZE` | Dimensions of the vector embedding | `384` |
| `QDRANT_DISTANCE` | Distance metric algorithm for Qdrant collection | `Cosine` |

### Running Locally (Bare Metal)

Ensure you have Go 1.21+ installed.

```bash
export PORT=8080
export CF_ACCOUNT_ID="your-cloudflare-account-id"
export CF_API_TOKEN="your-cloudflare-api-token"
export CF_ACCESS_JWT_ASSERTION="your-cloudflare-access-jwt-assertion"

go run src/main.go
```

### Docker Build (Local)

To build a highly optimized, multi-stage production Docker image:

```bash
docker build -t chiefj/ai-service:latest .
```

* **Image Size:** 13.3 MB (13,349,712 bytes)
* **Base Image:** Alpine 3.19 (minimal runtime footprint)

### Docker Deploy (Registry Push & Release)

A deployment script is provided at `scripts/deploy_docker.sh` that automates building, tagging, logging in, and pushing the image as the first stable release (`v1.0.0`), `stable`, and `latest`:

```bash
./scripts/deploy_docker.sh
```

### Docker Deploy (Container Run)

To run the built Docker container locally mapping port `8080`:

```bash
docker run -d \
  --name ai-service-test \
  -p 8080:8080 \
  -e CF_ACCOUNT_ID="your-cloudflare-account-id" \
  -e CF_API_TOKEN="your-cloudflare-api-token" \
  -e CF_ACCESS_JWT_ASSERTION="your-cloudflare-access-jwt-assertion" \
  chiefj/ai-service:latest
```


---

## Performance, Capacity, and Telemetry Statistics

### 1. Memory Capacity Profile (RAM)

The in-memory session memory repository stores active chat session records under a high-performance concurrent map (`sync.RWMutex`). Each record holds the conversational text history alongside the 384-dimensional float32 embedding vector (`@cf/baai/bge-small-en-v1.5`).

* **Memory footprint per message turn**: ~4 to 8 KB (includes Go structure padding, user request message, assistant response, and embedding vectors).
* **Automatic Eviction Policy**: An active cleanup loop checks every minute and evicts any session that has been inactive for more than `15 minutes` (`15 * time.Minute` TTL).

Based on server RAM allocations:

| Allocated RAM | Approx. Active Sessions | Approx. Total Messages Stored |
| :--- | :--- | :--- |
| `100 MB` | ~10,000 | ~25,000 |
| `500 MB` | ~50,000 | ~125,000 |
| `1 GB` | ~100,000 | ~250,000 |
| `4 GB` | ~400,000 | ~1,000,000 |

### 2. Microsecond-Level Performance Latency

| Operation | Latency | Complexity | Detail |
| :--- | :--- | :--- | :--- |
| **In-Memory Session Lookup** | `< 1 µs` | O(1) | Read-locked hash map retrieval |
| **Cosine Similarity Search** | `< 1 ms` | O(N) | Blazing-fast float32 array calculations |
| **Embedding Generation** | `50 - 150 ms` | Network-Bound | REST Call to Cloudflare Workers AI |
| **LLM Chat Inference** | `300 - 800 ms` | Network-Bound | REST Call to Cloudflare Workers AI Llama-3 |

### 3. Native OpenTelemetry (OTel) Instrumentation

The service has deep native tracing capabilities built with OpenTelemetry (`go.opentelemetry.io/otel`). The `InitTracer` provider formats and exports service traces to standard out or compatible collectors.

#### Telemetry Trace Attributes Captured:

* **API Request Context**: `http.method`, `http.route`, `api.version` (v1)
* **Domain Feature Name**: `feature.name` (set to `ai_orchestrator`)
* **AI Model Engine Execution**: `ai.model` and `ai.embedding_model`
* **Session Tracking**: `user.id`
* **Errors and Failures**: Captured using `span.RecordError(err)` and marked with `codes.Error` status code for automatic alerting inside modern observability dashboards.

---

## CURLs and Responses

### 1. List Available Models

Retrieves the catalog of AI models from Cloudflare.

#### Request

```bash
curl -s -f http://localhost:8080/api/v1/models
```

#### Response

```json
[
  {
    "id": "31097538-a3ff-4e6e-bb56-ad0e1f428b61",
    "name": "@cf/meta/llama-3-8b-instruct-awq",
    "description": "Quantized (int4) generative text model with 8 billion parameters from Meta.",
    "provider": ""
  },
  {
    "id": "053d5ac0-861b-4d3b-8501-e58d00417ef8",
    "name": "@cf/google/gemma-3-12b-it",
    "description": "Gemma 3 models are well-suited for a variety of text generation and image understanding tasks...",
    "provider": ""
  },
  {
    "id": "01bc2fb0-4bca-4598-b985-d2584a3f46c0",
    "name": "@cf/baai/bge-large-en-v1.5",
    "description": "BAAI general embedding (Large) model that transforms any given text into a 1024-dimensional vector",
    "provider": ""
  }
]
```

### 2. Standard Chat Inference

Executes a stateless chat completion against a designated LLM model.

#### Request

```bash
curl -s -f -X POST http://localhost:8080/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "@cf/meta/llama-3-8b-instruct",
    "messages": [
      {"role": "user", "content": "Explain Hexagonal Architecture in Go in one sentence."}
    ]
  }'
```

#### Response

```json
{
  "response": "In Go, Hexagonal Architecture, also known as Ports and Adapters Architecture, is a design pattern where the application's business logic is encapsulated in a \"domain layer\" and interacts with external dependencies through \"ports\" and \"adapters\", allowing for loose coupling and testability.",
  "cached": false,
  "cache_type": "none"
}
```

### 3. Stateful/Persistent Chat (Turn 1: Store Context)

Initiates a session, generates a text embedding of the input, saves it in concurrent-safe memory, and processes the response.

#### Request

```bash
curl -s -f -X POST http://localhost:8080/api/v1/chat/persistent \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "live_user_123",
    "message": "Hello Cloudflare! My favorite programming language is Go.",
    "model": "@cf/meta/llama-3-8b-instruct",
    "embedding_model": "@cf/baai/bge-small-en-v1.5"
  }'
```

#### Response

```json
{
  "response": "Hello there! I'm thrilled to hear that your favorite programming language is Go! As a cloud-based service, Cloudflare is heavily invested in the Go programming language. In fact, our entire web server is written in Go, and it's been a fantastic choice for us.\n\nWe've found that Go's concurrency features, performance, and simplicity make it an ideal language for building scalable and reliable systems. Our Go-based server has allowed us to handle massive traffic spikes and provide fast and secure connections to our customers.\n\nWhat do you love most about Go? Is it the concurrency model, the simplicity of the language, or something else entirely?",
  "history": [
    {
      "role": "user",
      "content": "Hello Cloudflare! My favorite programming language is Go."
    },
    {
      "role": "assistant",
      "content": "Hello there! I'm thrilled to hear that your favorite programming language is Go! As a cloud-based service, Cloudflare is heavily invested in the Go programming language..."
    }
  ],
  "cached": false,
  "cache_type": "none"
}
```

### 4. Stateful/Persistent Chat (Turn 2: Semantic Memory Retrieval)

Queries the chat session. The orchestrator embeds the query, searches the memory repository via cosine similarity, retrieves the relevant context, appends history, and passes it to the LLM.

#### Request

```bash
curl -s -f -X POST http://localhost:8080/api/v1/chat/persistent \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "live_user_123",
    "message": "What is my favorite programming language?",
    "model": "@cf/meta/llama-3-8b-instruct",
    "embedding_model": "@cf/baai/bge-small-en-v1.5"
  }'
```

#### Response

```json
{
  "response": "You told me earlier that your favorite programming language is Go!",
  "history": [
    {
      "role": "user",
      "content": "Hello Cloudflare! My favorite programming language is Go."
    },
    {
      "role": "assistant",
      "content": "Hello there!..."
    },
    {
      "role": "user",
      "content": "What is my favorite programming language?"
    },
    {
      "role": "assistant",
      "content": "You told me earlier that your favorite programming language is Go!"
    }
  ],
  "cached": false,
  "cache_type": "none"
}
```
