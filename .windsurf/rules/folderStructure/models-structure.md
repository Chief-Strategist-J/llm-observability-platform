# Model Registry and Caching Directory Structure Rules

This document defines the rules and structure for registering and maintaining model weights, task configurations, and hardware runtime specifications across the LLM Observability Platform.

---

## Core Rules
1. **Zero Weight Baking**: Large model weights must **never** be baked directly into the application container build layers. Images must remain lightweight (< 1.0GB for CPU).
2. **Dynamic Caching**: Container runtimes must download model weights dynamically at startup/runtime or load them from mapped persistent volume cache mounts (e.g., mapping `~/.cache/huggingface` to the container's `/root/.cache/huggingface`).
3. **Registry Declaration**: Every ML model utilized across packages must be documented under the root `models/` directory using the standard namespace layout.
4. **Clean Architecture Isolation**: Core domain services must never import infrastructure machine learning packages (e.g., PyTorch, ONNX Runtime, or Hugging Face Transformers) directly. They must communicate via port protocols.

---

## Registry Folder Structure Layout

```
models/
├── {namespace}/                   ← Hugging Face author namespace (e.g., cross-encoder)
│   └── {model-name}/              ← Model repository name
│       ├── model.yaml             ← Model metadata, tasks, parameters, and constraints
│       └── README.md              ← Model evaluation, baseline benchmarks, and references
│
├── {standalone-model-name}/       ← Standalone model repositories (e.g., gpt2)
│   ├── model.yaml
│   └── README.md
│
└── README.md                      ← Global model registry index
```

---

## Model Specification Schema (`model.yaml`)

Every registered model directory must contain a `model.yaml` matching this specification:

```yaml
id: "cross-encoder/nli-deberta-v3-base"  # Unique Hugging Face repository identifier
task: "sequence-classification"          # ML Task (sequence-classification, token-classification, causal-lm)
framework: "pytorch"                     # Primary runtime framework (pytorch, onnx, tensorflow)
precision: "fp32"                        # Quantization precision (fp32, fp16, int8)
size_bytes: 370000000                     # Weight size on disk in bytes
parameters: 186000000                    # Active parameter count

deployment:
  memory_limit_bytes: 1073741824         # Minimum recommended RAM allocation for execution (1GiB)
  hardware_platforms:                    # Supported platform runtimes
    - "cpu"
    - "cuda"
  volume_mounts:                         # Required persistent directory mapping
    host_path: "~/.cache/huggingface"
    container_path: "/root/.cache/huggingface"

metadata:
  owner: "@quality-team"
  description: "Cross-encoder NLI model for RAG grounding and faithfulness evaluation."
```
