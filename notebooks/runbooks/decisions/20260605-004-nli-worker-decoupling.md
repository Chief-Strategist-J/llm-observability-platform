# ADR-004 — Model Registry Decoupling for NLI Worker

| Field       | Value                                                             |
|-------------|-------------------------------------------------------------------|
| **ID**      | 004                                                               |
| **Date**    | 2026-06-05                                                        |
| **Status**  | accepted                                                          |
| **Deciders**| LLM Observability Platform Team                                   |
| **Package** | `packages/python/nli-worker`                                      |

---

## Context

The `nli-worker` is a stateless microservice designed for sequence classification scoring using DeBERTa v3. Historically, microservices pre-download and cache model weights at build time (e.g. `cross-encoder/nli-deberta-v3-base`) and bake them directly into the Docker image. However:
1. **Large Docker Image Footprint**: Baking PyTorch (~2.5GB) and the model weights (~370MB) into the CPU image results in a ~3GB image. The GPU version base image (`nvidia/pytorch:2.3.1-cuda12.1`) is already ~8.5GB, pushing the final GPU image size past 10GB.
2. **Hardcoded Model Dependency**: Baking in the model prevents reusing the same inference container with alternative NLI cross-encoder models (e.g., `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli` or `facebook/bart-large-mnli`) without rebuilding and deploying separate images.

To keep deployments lightweight and support dynamic model selection at runtime, we need a mechanism to decouple model weight storage from the container runtime and cache model instances in a registry.

### Driving Forces
- Keep CPU Docker images under 1GB (excluding volume caching).
- Enable hot-swapping or dynamic testing of alternative NLI models at runtime without code changes or container rebuilds.
- Maintain Clean Architecture principles by utilizing port protocols instead of concrete infrastructure adapter imports in the domain layer.
- Guarantee thread safety for GPU CUDA execution under concurrent load.

---

## Decision

We decided to implement a dynamic Model Registry caching system in the `NliScorerAdapter` and update the Dockerfiles to remove baked-in weights.

1. **Dynamic Model Registry**:
   The [NliScorerAdapter](file:///home/btpl-lap-22/live/obs/packages/python/nli-worker/src/infra/adapters/nli_scorer_adapter.py) initializes a memory cache of model and tokenizer instances (`self._models` and `self._tokenizers`). When a request arrives with an optional `model_id`, the adapter checks the cache:
   - If loaded, it performs inference immediately.
   - If not loaded, it downloads the weights dynamically from Hugging Face, caches them in memory, and then runs inference.
2. **Parameterize Endpoints**:
   Updated the REST handler [nli.py](file:///home/btpl-lap-22/live/obs/packages/python/nli-worker/src/api/rest/v1/handlers/nli.py) and domain [service.py](file:///home/btpl-lap-22/live/obs/packages/python/nli-worker/src/core/domain/service.py) to accept a `model_id` parameter in the request body, falling back to the default `NLI_MODEL_ID` environment variable if not specified.
3. **Clean Architecture Isolation**:
   Defined a clear [NliScorerPort](file:///home/btpl-lap-22/live/obs/packages/python/nli-worker/src/core/domain/ports/nli_scorer_port.py) protocol to decouple the domain layer from concrete Hugging Face/PyTorch implementations.
4. **Decoupled Docker Weights**:
   Removed model pre-download scripts from [Dockerfile](file:///home/btpl-lap-22/live/obs/packages/python/nli-worker/build/Dockerfile) and [Dockerfile.gpu](file:///home/btpl-lap-22/live/obs/packages/python/nli-worker/build/Dockerfile.gpu). Users can map a host cache directory into `/root/.cache/huggingface` inside the container for persistent volume storage.

---

## Failure-First System Building (FFSB) Analysis

Applying the failure-first framework:

### Mode 1: First-Request Latency Spike (Cold-Start)
- **Symptom**: The first request targeting a new model experiences severe delays (3–10+ seconds) while downloading weights, causing upstream client timeouts.
- **Prevention**:
  - Implement dynamic lifespan preloading in [app.py](file:///home/btpl-lap-22/live/obs/packages/python/nli-worker/src/api/rest/v1/app.py): eagerly load the default model and tokenizer at container startup to prevent cold-starts on the default hot path.
  - Safeguard startup preloading using `hasattr` checks to support mock configurations in test environments.

### Mode 2: Network Outage (Dynamic Download Failure)
- **Symptom**: Incoming requests for a new model fail with `OSError` or connection errors if the Hugging Face registry is unreachable.
- **Prevention**:
  - Rely on persistent volume mounts (e.g. host mapping `~/.cache/huggingface` to the container) so that once a model is downloaded, it never needs to be fetched over the network again.
  - Return explicit HTTP `503 Service Unavailable` error structures with detailed connection error reports if dynamic downloading fails.

### Mode 3: Memory Exhaustion (OOM due to Registry Bloat)
- **Symptom**: The container is terminated with `OOMKilled` after loading multiple large models.
- **Prevention**:
  - Limit default models to base sizes (e.g., 186M parameters).
  - In production, restrict authorized models via environment variables or set memory limits on the container.

---

## Consequences

### Positive
- **Reduced Image Size**: Extricating model weights reduces the CPU build size substantially (the built image size is only **229 MB**), making deployment fast.
- **Flexibility**: Zero rebuilds required to switch models; simply pass a different `model_id` in the API payload.
- **Strict Separation**: Clean Architecture guidelines are met via the [NliScorerPort](file:///home/btpl-lap-22/live/obs/packages/python/nli-worker/src/core/domain/ports/nli_scorer_port.py) protocol.

### Negative / Trade-offs
- **Network Dependency**: The container requires access to Hugging Face or a mounted model cache on first start.
- **RAM Footprint**: Loading multiple models concurrently consumes more system RAM.

---

## Alternatives Considered

- **Option A: Bake-in weights in Docker image**
  - *Elimination Reason*: Results in massive 10GB+ GPU images and strictly couples the image to a single model.
- **Option B: ONNX Runtime Only**
  - *Elimination Reason*: While extremely lightweight for CPU, ONNX GPU compilation requires separate setups, reducing versatility for GPU-based inference SLOs.
