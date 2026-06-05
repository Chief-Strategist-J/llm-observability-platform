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

Below is the detailed directory map of the model registry, shepherding rules, and consumer packages:

```text
.
├── .windsurf/
│   └── rules/
│       └── folderStructure/
│           └── models-structure.md        # Registry specifications and locking rules
│
├── models/                                # Centralized Model Registry
│   ├── cross-encoder/                     # HF Namespace directory
│   │   └── nli-deberta-v3-base/           # Model folder
│   │       ├── model.yaml                 # NLI weights metadata and deployment parameters
│   │       └── README.md                  # Accuracy benchmarks and evaluation metrics
│   │
│   ├── unitary/                           # HF Namespace directory
│   │   └── toxic-bert/                    # Toxicity classification model
│   │       ├── model.yaml                 # ONNX CPU-only deployment metadata
│   │       └── README.md                  # Multi-label category descriptions
│   │
│   ├── gpt2/                              # Standalone model folder (no namespace prefix)
│   │   ├── model.yaml                     # Fallback perplexity specifications
│   │   └── README.md                      # Logprob causal LM benchmarks
│   │
│   └── README.md                          # Master index of registered platform models
│
└── packages/
    └── python/
        ├── nli-worker/                    # Consumer package for NLI scoring
        │   ├── build/
        │   │   ├── Dockerfile             # Decoupled build (Zero Weight Baking)
        │   │   └── Dockerfile.gpu         # Decoupled build (Zero Weight Baking)
        │   └── src/
        │       ├── core/domain/ports/
        │       │   └── nli_scorer_port.py # Clean Architecture port (no ML dependencies)
        │       └── infra/adapters/
        │           └── nli_scorer_adapter.py # Implements cache loader and thread safety
        │
        ├── perplexity/                    # Consumer package for Perplexity metrics
        │   └── src/infra/adapters/
        │       └── scorers/
        │           └── gpt2_scorer_adapter.py # Loads fallback ONNX models dynamically
        │
        └── toxicity/                      # Consumer package for Toxicity auditing
            └── src/infra/adapters/
                └── scorers/
                    └── toxicity_scorer_adapter.py # Loads ONNX classification weights
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
