# AI Service

This service acts as an AI Orchestrator that integrates with Cloudflare's AI Gateway/Workers API. It implements stateful, persistent chat sessions with a high-performance in-memory memory repository, semantic context retrieval via cosine similarity, and OpenTelemetry instrumentation.

---

## Architecture Flow

The following diagram illustrates the HTTP request routing, Dependency Injection layout, Port/Adapter boundary, and external integration points of the AI Orchestrator:

```
                               +---------------------------------------------+
                               |                 HTTP Client                 |
                               +---------------------------------------------+
                                      |                               ^
                   POST /chat/persistent                              | Response JSON
                                      v                               |
+------------------------------------------------------------------------------------+
|  AI SERVICE                                                                        |
|                                                                                    |
|  +--------------------+             +------------------+             +----------+  |
|  |    HTTP Router     |------------>|   AI Handlers    |------------>| Provider |  |
|  |     (Router)       |             |   (Controller)   |             |   (DI)   |  |
|  +--------------------+             +------------------+             +----------+  |
|                                              |                                     |
|                                              v                                     |
|                                 +-------------------------+                        |
|                                 |     AI Orchestrator     |                        |
|                                 |        (Service)        |                        |
|                                 +-------------------------+                        |
|                                    /                     \                         |
|                      1. Cosine Similarity           2. Chat Inference & Embedding  |
|                                 /                           \                      |
|                                v                             v                     |
|                   +-------------------------+   +-------------------------+        |
|                   |       Memory Repo       |   |   Cloudflare Adapter    |        |
|                   |     (In-Memory DB)      |   |    (HTTP Rest Client)   |        |
|                   +-------------------------+   +-------------------------+        |
+------------------------------------------------------------------------------------+
                                                               |
                                                       HTTP / HTTPS API
                                                               v
                                                      +------------------+
                                                      |  Cloudflare AI   |
                                                      |  Gateway/Workers |
                                                      +------------------+
```

---

## Decision Tree (Chat Flow Execution)

This decision flowchart outlines the execution path of stateless vs. stateful chat requests:

```
                       [ Incoming Chat Request ]
                                   |
                          Is Route Persistent?
                         /                    \
                       No                     Yes
                       /                        \
           +----------------------+       +------------------------------------+
           | Stateless Chat Flow  |       |        Stateful Chat Flow          |
           +----------------------+       +------------------------------------+
                      |                                      |
                      |                         Extract user_id & message
                      |                                      |
                      |                         Generate embedding for message
                      |                                      |
                      v                         Query Memory Repo for user_id
           Send prompt to Cloudflare            (Fetch historical context)
                      |                                      |
                      |                         Retrieve top K similar memories
                      |                         (Cosine Similarity Threshold)
                      v                                      |
              Return AI response                 Inject memories as context
                      |                         into prompt message history
                      |                                      |
                      v                         Send prompt + history to Cloudflare
                 [ End Chat ]                                |
                                                Receive LLM AI response
                                                             |
                                                Generate embedding for response
                                                             |
                                                Store both User & Assistant
                                                turns in Memory Repo
                                                             |
                                                             v
                                                     Return AI response
                                                             |
                                                             v
                                                        [ End Chat ]
```

---

## Folder Structure

```
.
├── Dockerfile                  # Multi-stage Docker build configuration
├── docker-compose.yaml         # Local container orchestration
├── go.mod                      # Go module dependencies
├── go.sum                      # Go dependency verification checksums
├── test_api.sh                 # Local integration test script using mock adapters
├── test_cloudflare_real.sh     # Live integration test script using real Cloudflare credentials
├── contracts/
│   ├── changelog.md            # API contract version history
│   └── openapi/
│       └── v1.yaml             # OpenAPI v1 contract specification
├── scripts/
│   └── deploy_docker.sh        # Docker deployment script (build, tag, registry push)
└── src/
    ├── main.go                 # App entrypoint (initializes tracing, HTTP server, DI container)
    ├── api/
    │   └── rest/
    │       └── v1/
    │           ├── router.go   # HTTP request routing definitions
    │           └── handlers/
    │               └── ai_handlers.go # HTTP controllers/request handlers
    ├── features/
    │   └── ai_orchestrator/    # Domain layer (Hexagonal Architecture)
    │       ├── index.go        # Feature initialization
    │       ├── ports.go        # Port interface definitions (Service, Client, Repo)
    │       ├── service.go      # Core Orchestrator implementation (coordinate LLM, Embedding, Memory retrieval)
    │       └── types.go        # Domain entity models (ModelInfo, ChatMessage, MemoryItem)
    ├── infra/
    │   └── adapters/           # Infrastructure adapter implementations
    │       ├── cloudflare_adapter.go # HTTP client communicating with Cloudflare AI
    │       └── memory_repo.go  # Concurrent-safe storage and cosine similarity retriever
    └── shared/
        ├── di/
        │   └── providers.go    # Wire-up of application dependencies (Dependency Injection)
        └── tracing/
            └── otel.go         # OpenTelemetry tracer provider setup
```

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
  "response": "In Go, Hexagonal Architecture, also known as Ports and Adapters Architecture, is a design pattern where the application's business logic is encapsulated in a \"domain layer\" and interacts with external dependencies through \"ports\" and \"adapters\", allowing for loose coupling and testability."
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
  ]
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
  ]
}
```
