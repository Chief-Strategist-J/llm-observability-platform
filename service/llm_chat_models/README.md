# AI Agents Platform

Modular, durable, and extensible platform for running AI agents with persistent state, event-driven workflows, and robust failure handling.

## System Architecture

```ascii
                                         ┌─────────────────┐
                                         │  Admin / API    │
                                         │  (Dashboard)    │
                                         └────────┬────────┘
                                                  │ HTTP / SSE
                                                  ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  AI AGENTS SERVICE                                                              │
│                                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐                   │
│  │   GATEWAY    │◄────►│    LOGIC     │◄────►│ PERSISTENCE  │                   │
│  │ (FastAPI)    │      │ (News/Agent) │      │ (Mongo/PG)   │                   │
│  └──────┬───────┘      └──────┬───────┘      └──────┬───────┘                   │
│         │                     │                     │                           │
│         ▼                     ▼                     ▼                           │
│  ┌──────────────┐      ┌──────────────┐      ┌────────────┐     ┌────────────┐  │
│  │ Auth & Rate  │      │   Workflow   │◄────►│  MongoDB   │◄───►│  Postgres  │  │
│  │ Limit (PG)   │      │    Engine    │      │ (Workflow) │     │ (Auth/Rate)│  │
│  └──────────────┘      └──────┬───────┘      └────────────┘     └────────────┘  │
│                               │                                                 │
│                               ▼                                                 │
│                        ┌──────────────┐                                         │
│                        │ Model Mngr   │                                         │
│                        │ (Ollama)     │                                         │
│                        └──────┬───────┘                                         │
│                               │                                                 │
│                               ▼                                                 │
│                        ┌──────────────┐                                         │
│                        │   Ollama     │                                         │
│                        │   Service    │                                         │
│                        └──────────────┘                                         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## System Loop & Sequence

### 1. Agent Execution Flow

```ascii
Client             Gateway            AgentRegistry        ChatAgent           ModelManager          Ollama
  │                   │                     │                  │                    │                   │
  │ POST /chat/stream │                     │                  │                    │                   │
  ├──────────────────►│                     │                  │                    │                   │
  │                   │ Get Agent Class     │                  │                    │                   │
  │                   ├────────────────────►│                  │                    │                   │
  │                   │◄────────────────────┤                  │                    │                   │
  │                   │                     │                  │                    │                   │
  │                   │ Instantiate         │                  │                    │                   │
  │                   ├───────────────────────────────────────►│                    │                   │
  │                   │                                        │                    │                   │
  │                   │ generate_stream(input)                 │                    │                   │
  │                   ├───────────────────────────────────────►│                    │                   │
  │                   │                                        │ generate_stream()  │                   │
  │                   │                                        ├───────────────────►│                   │
  │                   │                                        │                    │ POST /generate    │
  │                   │                                        │                    ├──────────────────►│
  │                   │                                        │                    │                   │
  │                   │                                        │                    │ Stream Tokens     │
  │                   │                                        │◄───────────────────┼───────────────────┤
  │                   │                                        │                    │                   │
  │ Tablet SSE        │Yield Chunk                             │Yield Chunk         │                   │
  │◄──────────────────┼────────────────────────────────────────┼────────────────────┘                   │
  │                   │                                        │                                        │
  │...                │...                                     │...                                     │
  │                   │                                        │                                        │
  │ [DONE]            │                                        │                                        │
  │◄──────────────────┘                                        │                                        │
  ▼                                                            ▼                                        ▼
```

### 2. Durable Workflow Flow

```ascii
WorkflowEngine         Step (Durable)        MongoStore         EventBus (Mongo)
      │                      │                   │                    │
      │ run(workflow_fn)     │                   │                    │
      ├─────────────────────►│                   │                    │
      │                      │                   │                    │
      │                      │ Save Status       │                    │
      │◄─────────────────────┼──────────────────►│                    │
      │                      │                   │                    │
      │                      │ step.do("task")   │                    │
      │                      ├──────────────────►│ Check if done      │
      │                      │                   │                    │
      │                      │◄──────────────────┤ Return result/None │
      │                      │                   │                    │
      │                      │ [If not done]     │                    │
      │                      │ Execute Task...   │                    │
      │                      │                   │                    │
      │                      │ Save Result       │                    │
      │                      ├──────────────────►│                    │
      │                      │                   │                    │
      │                      │ wait_for_event()  │                    │
      │                      ├───────────────────────────────────────►│
      │                      │                   │                    │ Poll Mongo
      │                      │                   │                    ├─────┐
      │                      │                   │                    │◄────┘
      │                      │                   │                    │
      │                      │                   │                    │ [Event Found]
      │                      │◄───────────────────────────────────────┤
      │                      │                   │                    │
      │ Finish Workflow      │                   │                    │
      ├─────────────────────►│                   │                    │
      │ Save Complete        │                   │                    │
      ├──────────────────────┼──────────────────►│                    │
      ▼                      ▼                   ▼                    ▼
```

## Decision Tree: "Can I run this Agent?"

```ascii
Start
  │
  ▼
Is Authentication Enabled? (AUTH_ENABLED=true)
  │
  ├─ YES ──► Is API Key Valid?
  │            │
  │            ├─ NO ──► Return 401 Unauthorized
  │            │
  │            └─ YES ──► Check Rate Limit
  │                         │
  │                         ├─ EXCEEDED ──► Return 429 Too Many Requests
  │                         │
  │                         └─ OK ──► Continue
  │
  └─ NO ──► Continue
         │
         ▼
Does Agent Type Exist? (AgentRegistry)
  │
  ├─ NO ──► Return 501 Not Implemented
  │
  └─ YES ──► Instantiate Agent
              │
              ▼
Is Ollama Available? (Circuit Breaker)
  │
  ├─ NO (Open) ──► Return 503 Service Unavailable (Retry-After)
  │
  └─ YES (Closed) ──► Execute Logic
```

## Features

1.  **Durable Workflows**: Workflows survive restarts using MongoDB for state.
2.  **Event-Driven**: Agents communicating via persistent EventBus.
3.  **Resilience**:
    *   **Circuit Breaker**: Protects downstream Ollama service.
    *   **Rate Limiting**: Per-client limits via Postgres.
    *   **Graceful Shutdown**: Drains active workflows before exiting.
4.  **Security**: API Key authentication with Postgres storage.
5.  **Streaming**: Real-time SSE support for chat agents.

## Configuration

*   **MongoDB**: `MONGO_URI`, `MONGO_DB_NAME`
*   **Postgres**: `POSTGRES_DSN`
*   **Ollama**: `OLLAMA_HOST`
*   **Auth**: `AUTH_ENABLED` (default: true)
*   **Limits**: `RATE_LIMIT_MAX_REQUESTS` (default: 100/min)

## Running

```bash
# Start infrastructure
docker-compose up -d

# Run service
python run.py
```
