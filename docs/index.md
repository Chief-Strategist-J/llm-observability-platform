# LLM Observability SDK — Wiki Home

> Python SDK for capturing, enriching, and analyzing LLM call telemetry with zero-to-minimal code changes.

## Wiki Pages

| Page | What it covers |
|---|---|
| [Installation & Quick Start](Installation-and-Quick-Start) | Install, first span, verify it works |
| [Auto-Instrumentation](Auto-Instrumentation) | Zero-code patching for OpenAI, Anthropic, LiteLLM, LangChain |
| [Manual Spans — Decorator](Manual-Spans-Decorator) | `@llm_observe` decorator usage |
| [Manual Spans — Context Manager](Manual-Spans-Context-Manager) | `llm_span` / `llm_span_with_tokens` context managers |
| [Streaming Observability](Streaming-Observability) | TTFT tracking, `wrap_stream`, `wrap_async_stream` |
| [PII & Injection Scanning](PII-and-Injection-Scanning) | Aho-Corasick redaction, scan API |
| [Deterministic Sampling](Deterministic-Sampling) | SHA-256 modulo-100 gate |
| [MiniLM Embeddings](MiniLM-Embeddings) | Async 384-dim prompt embeddings |
| [Prometheus Metrics & Grafana](Prometheus-Metrics-and-Grafana) | Cost, latency, TTFT dashboards |
| [REST Management API](REST-Management-API) | Full endpoint reference |
| [Docker & CLI Deployment](Docker-and-CLI-Deployment) | `llm-observe` CLI, all-in-one container |
| [Config Files Reference](Config-Files-Reference) | Model prices, PII patterns, infra configs |

## Current Version

`1.7.2` — see [Changelog](https://github.com/your-org/your-repo/blob/main/packages/python/instrumentation-sdk/contracts/changelog.md)
