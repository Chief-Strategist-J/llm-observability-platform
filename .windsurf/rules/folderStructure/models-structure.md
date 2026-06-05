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
│   │       ├── model.yaml                 # Configs: id, task, framework, precision, deployment, metadata
│   │       │                              # Source: Hugging Face (cross-encoder/nli-deberta-v3-base)
│   │       │                              # Use Case: RAG grounding verification, response faithfulness scoring
│   │       └── README.md                  # Accuracy benchmarks and evaluation metrics
│   │
│   ├── unitary/                           # HF Namespace directory
│   │   └── toxic-bert/                    # Toxicity classification model
│   │       ├── model.yaml                 # Configs: id, task, framework, precision, deployment, metadata
│   │       │                              # Source: Hugging Face (unitary/toxic-bert)
│   │       │                              # Use Case: Input/output toxicity classification and Kafka alert publishing
│   │       └── README.md                  # Multi-label category descriptions
│   │
│   ├── gpt2/                              # Standalone model folder (no namespace prefix)
│   │   ├── model.yaml                     # Configs: id, task, framework, precision, deployment, metadata
│   │   │                                  # Source: Hugging Face (gpt2) / local ONNX
│   │   │                                  # Use Case: Fallback token perplexity computation when provider logprobs are missing
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
version: "1.0.0"                         # Semantic version or commit hash pin of model weights
task: "sequence-classification"          # ML Task (sequence-classification, token-classification, causal-lm)
framework: "pytorch"                     # Primary runtime framework (pytorch, onnx, tensorflow)
precision: "fp32"                        # Quantization precision (fp32, fp16, int8)
size_bytes: 370000000                    # Weight size on disk in bytes
parameters: 186000000                    # Active parameter count
sha256: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z..."  # SHA-256 checksum for download verification
max_sequence_length: 512                 # Max tokens model context window accepts
vocab_size: 128100                       # Number of vocabulary tokens
license: "apache-2.0"                    # Model open-source or proprietary license type

source:
  registry: "huggingface"                # Source registry (huggingface, local, custom-s3)
  url: "https://huggingface.co/cross-encoder/nli-deberta-v3-base" # Registry source url

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

---

## Detailed Configuration Parameters

Every `model.yaml` registry file requires these configurations:
- **`id` (string)**: The exact model repository identifier (Hugging Face ID or model path) that the runtime loaders query.
- **`version` (string)**: Pinned semantic version (e.g. `1.0.0`) or git commit SHA of model weights to prevent runtime drifts.
- **`task` (string)**: The machine learning task type. Must be one of `sequence-classification`, `token-classification`, or `causal-lm`.
- **`framework` (string)**: The software execution framework. Must be one of `pytorch`, `onnx`, or `tensorflow`.
- **`precision` (string)**: The numerical data precision. Commonly `fp32`, `fp16`, or `int8`.
- **`size_bytes` (integer)**: The size of model weights in bytes on disk, used for forecasting volume storage allocations.
- **`parameters` (integer)**: Active model parameter count.
- **`sha256` (string)**: The SHA-256 checksum of the main model binary weight file to verify integrity during dynamic download.
- **`max_sequence_length` (integer)**: Context window length supported by the model (e.g. `512` or `1024`).
- **`vocab_size` (integer)**: Total vocabulary size of the model's tokenizer.
- **`license` (string)**: Model licensing details (e.g. `apache-2.0`, `mit`, `openrail`).
- **`source` (object)**:
  - **`registry` (string)**: Target weights registry (e.g. `huggingface`, `onnx-model-zoo`, `custom-s3`).
  - **`url` (string)**: Complete repository URL for downloading model weights.
- **`deployment` (object)**:
  - **`memory_limit_bytes` (integer)**: The minimum container memory size (in bytes) needed to run model loading and inference without triggering OOM-kills.
  - **`hardware_platforms` (list of strings)**: Runtime hardware devices supported (`cpu`, `cuda`, `mps`).
  - **`volume_mounts` (object)**:
    - **`host_path` (string)**: Host system volume path to mount.
    - **`container_path` (string)**: Container destination path to mount for Hugging Face cache persistence.
- **`metadata` (object)**:
  - **`owner` (string)**: Slack owner tag or team handles for package support.
  - **`description` (string)**: Detailed operational context and use cases for the registered model.


