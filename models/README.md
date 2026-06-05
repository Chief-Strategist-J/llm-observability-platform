# Platform Model Registry

This directory serves as the centralized Model Registry index for the LLM Observability Platform. Every model used for inference, metrics calculation, and safety auditing is documented here to maintain architectural consistency.

---

## Active Models Index

| Model Identifier | Primary Task | Framework | Precision | Size | Description |
|------------------|--------------|-----------|-----------|------|-------------|
| [nli-deberta-v3-base](file:///home/btpl-lap-22/live/obs/models/cross-encoder/nli-deberta-v3-base/model.yaml) | sequence-classification | PyTorch | FP32 | ~370 MB | Used in NLI worker microservice for RAG grounding and faithfulness checks. |
| [toxic-bert](file:///home/btpl-lap-22/live/obs/models/unitary/toxic-bert/model.yaml) | sequence-classification | ONNX | FP32 | ~410 MB | Used in toxicity scorer microservice for classification. |
| [gpt2](file:///home/btpl-lap-22/live/obs/models/gpt2/model.yaml) | causal-lm | ONNX | FP32 | ~498 MB | Used in perplexity microservice for fallback scoring. |

---

## Caching and Decoupling Rules

All models declared in this registry must adhere to the rules defined in [.windsurf/rules/folderStructure/models-structure.md](file:///home/btpl-lap-22/live/obs/.windsurf/rules/folderStructure/models-structure.md). In summary:
- Large model weight binaries must never be committed to Git.
- Application container builds must not bake weights into image layers.
- Containers must utilize persistent host cache volume mounts (e.g. `~/.cache/huggingface`) to reuse downloaded model weights across restarts.
