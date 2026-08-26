# Centralized Messaging & OTEL GenAI Architecture Plan

Target Package: `packages/python/instrumentation-sdk`

---

## 1. Compliance Audit & Key Requirements

- **API Request & Response Structure Policy (`api-request-response-structure.md`)**:
  - Enforce `traceparent`, `tracestate`, `x-request-id`, `x-correlation-id`, `x-causation-id`, `x-idempotency-key`, `x-tenant-id`, `x-client-id` across incoming/outgoing request headers and spans.
  - Wrap API responses in standard `ApiResponse` / `ApiErrorResponse` envelope format (`success`, `statusCode`, `data`/`error`, `meta`).

- **API-First & Messaging Infrastructure Policy (`api-structure.md`)**:
  - Centralized messaging infrastructure under `infra/messaging/`:
    - `broker_config.py` (singleton Kafka configuration)
    - `client_factory.py` (thread-safe KafkaProducer & KafkaConsumer factory)
    - `topic_provisioner.py` (declarative Kafka topic provisioning & rollback engine)
  - Modular Messaging Engine under `src/shared/messaging/`:
    - `middleware/`: Pipeline execution engine (`ProducerMiddlewarePipeline`, `ConsumerMiddlewarePipeline`) with tracing, logging, validation, retry, & idempotency.
    - `tracing/`: W3C distributed trace context propagation & OpenTelemetry span lifecycle management.
    - `producers/`: Middleware-driven typed Kafka event producers.
    - `consumers/`: Middleware-driven consumer group manager & event dispatchers.
    - `topics/`: Centralized topic catalog & schema registry bindings.
    - `handlers/`: Abstract message handlers & event registries.
    - `cqrs/`: Command handlers, read projections, & query selectors.
  - Pluggable Hexagonal Ports & Adapters for LLM Provider Mapping:
    - Extensible `LlmProviderAdapterPort` with model-specific mappers (OpenAI, Anthropic, Google Gemini, Cohere, Bedrock, Ollama, HuggingFace).

- **OpenTelemetry GenAI Semantic Conventions (`genai` attribute standards)**:
  - Migrate span attributes to official OpenTelemetry GenAI semantic conventions:
    - System & Operation: `gen_ai.system`, `gen_ai.operation.name` (`chat`, `text_completion`, `embeddings`)
    - Request: `gen_ai.request.model`, `gen_ai.request.temperature`, `gen_ai.request.top_p`, `gen_ai.request.max_tokens`, `gen_ai.request.presence_penalty`, `gen_ai.request.frequency_penalty`
    - Response: `gen_ai.response.model`, `gen_ai.response.id`, `gen_ai.response.finish_reasons`
    - Token Usage: `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`
    - Server: `server.address`, `server.port`

---

## 2. Directory Layout & Architecture Additions

```text
src/
├── shared/
│   ├── messaging/
│   │   ├── middleware/          # Composable Producer & Consumer Middleware Pipeline Engine
│   │   │   ├── base.py
│   │   │   ├── tracing_middleware.py
│   │   │   ├── logging_middleware.py
│   │   │   └── retry_middleware.py
│   │   ├── tracing/             # W3C Distributed Context & OpenTelemetry GenAI Semantic Conventions
│   │   │   ├── context_propagation.py
│   │   │   └── genai_attributes.py
│   │   ├── producers/           # Middleware-driven typed Kafka producers
│   │   │   └── span_producer.py
│   │   ├── consumers/           # Middleware-driven consumer group manager
│   │   │   └── span_consumer.py
│   │   ├── topics/              # Topic catalog & AsyncAPI registry bindings
│   │   │   └── catalog.py
│   │   ├── handlers/            # Message handler contracts
│   │   │   └── base.py
│   │   └── cqrs/                # CQRS Commands, Read Projections & Selectors
│   │       ├── commands.py
│   │       ├── projections.py
│   │       └── selectors.py
│   └── data-driven/             # Data-driven transforms & adapters
│
├── infra/
│   ├── messaging/
│   │   ├── broker_config.py
│   │   ├── client_factory.py
│   │   └── topic_provisioner.py # Declarative topic migration & rollback provisioner
│   └── adapters/
│       ├── llm/                 # Pluggable Provider Hexagonal Adapters
│       │   ├── port.py          # LlmProviderAdapterPort
│       │   ├── openai_adapter.py
│       │   ├── anthropic_adapter.py
│       │   ├── google_adapter.py  # Google Gemini / PaLM Support
│       │   ├── cohere_adapter.py  # Cohere Support
│       │   └── registry.py      # Dynamic Provider Adapter Registry
│
```

---

## 3. Implementation Steps

1. **Implement OTEL GenAI Semantic Conventions (`src/shared/messaging/tracing/genai_attributes.py`)**:
   - Create attribute mapper functions mapping raw LLM span fields to official `gen_ai.*` attributes.
2. **Implement Pluggable LLM Provider Adapters (`src/infra/adapters/llm/`)**:
   - Create `LlmProviderAdapterPort` protocol and provider implementations (Google Gemini, Anthropic, OpenAI, Cohere).
   - Integrate dynamic provider registry for seamless extension.
3. **Build Centralized Messaging & Middleware Engine (`src/shared/messaging/`)**:
   - Implement `ProducerMiddlewarePipeline` and `ConsumerMiddlewarePipeline`.
   - Add W3C context propagation middleware and OTEL GenAI tracing middleware.
   - Build `TopicProvisioner` in `infra/messaging/topic_provisioner.py`.
   - Wire `SpanKafkaProducer` using middleware pipeline.
4. **Refactor Auto-Instrumentation Mappers**:
   - Upgrade `ProviderMapper` in `features/auto_instrumentation/domain/mappers.py` to use `LlmProviderRegistry`.
5. **Verify Suite & Execution**:
   - Ensure all existing unit tests and integration tests execute successfully.
