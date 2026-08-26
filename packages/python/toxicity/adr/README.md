# Toxicity Service — Architecture Decision Records

This directory contains the full decision history for `packages/python/toxicity`.

| ADR | Title | Status | Date |
|---|---|---|---|
| [0001](./0001-onnx-cpu-inference-and-dual-pass-long-text-strategy.md) | ONNX Runtime CPU Inference with Dual-Pass Long-Text Strategy | Accepted | 2026-05-29 |
| [0002](./0002-kafka-publisher-for-flagged-toxicity-events.md) | Kafka Publisher for Flagged Toxicity Events | Accepted | 2026-06-02 |
| [0003](./0003-consolidation-of-toxicity-and-toxicity-worker.md) | Consolidation of `toxicity` and `toxicity-worker` into a Single Package | Accepted | 2026-08-26 |

---

## ADR Policy

Follow the **failure-first** format defined in [`policies/rules/runbook/adr.md`](../../../../policies/rules/runbook/adr.md).

Every ADR must answer:
1. What failure modes does the current approach have?
2. What options were considered and why were they rejected?
3. What new failure modes does the chosen option create?
4. Under what conditions should this decision be revisited?
