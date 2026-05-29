# Features

Explore the core features of the observability stack.

- [PII & Injection Scanning](PII-and-Injection-Scanning.md) — Protect user data and scan for prompt exploits.
- [Deterministic Sampling](Deterministic-Sampling.md) — 1% modulo gate to control overhead.
- [MiniLM Embeddings](MiniLM-Embeddings.md) — Async 384-dimensional vector embeddings of prompt texts.
- [Prometheus Metrics & Grafana](Prometheus-Metrics-and-Grafana.md) — Prebuilt dashboards for monitoring latency, TTFT, cost, and error rates.
- [Temporal EWMA Cost Anomaly Detection](Temporal-EWMA-Cost-Anomaly-Detection.md) — Decoupled EWMA baseline computing & cost anomaly detection worker.
- [Alert Engine](Alert-Engine.md) — Kafka consumer worker routing budget alerts and cost anomalies to Postgres, Slack, and PagerDuty.
- [Budget Provisioner](Budget-Provisioner.md) — Internal API managing token bucket rate limits and user budget configurations.
- [Toxicity Scorer](Toxicity-Scorer.md) — Multi-label toxic-bert ONNX classifier for response text.
- [Faithfulness Scorer](Faithfulness-Scorer.md) — Hallucination detection in RAG pipelines using DeBERTa-v3 NLI entailment.
- [Semantic Coherence Scorer](Semantic-Coherence-Scorer.md) — Cosine similarity check between prompt and response embeddings.


