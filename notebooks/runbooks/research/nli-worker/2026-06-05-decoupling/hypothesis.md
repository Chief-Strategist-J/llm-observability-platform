# Hypothesis: NLI Scorer Model Decoupling and Warmup Behavior

## 1. Problem Statement
Historically, microservices running machine learning models pre-bake model weights into the container image to simplify deployments. However, for `nli-worker` (using `cross-encoder/nli-deberta-v3-base`), this approach results in:
- Swelled CPU container image sizes (~3GB+) and massive GPU container image sizes (~10GB+), increasing deployment overhead.
- Hardcoded coupling to a single model variant, which prevents swapping or testing alternative NLI models at runtime.

## 2. Hypothesis
We hypothesize that:
1. Decoupling model weights from the Docker image (downloading dynamically at startup or runtime) will reduce the CPU container footprint to under **1.0GB**.
2. Implementing a dynamic, thread-safe in-memory model registry will allow hot-swapping models via API parameters without rebuilding container images.
3. Implementing eager pre-caching during container lifespan startup will eliminate cold-start latencies for default requests, keeping the default scoring pathway within acceptable latency bounds.
4. Per-model locking and double-checked locking in the memory cache will guarantee safe, non-blocking execution under concurrent request loads.

## 3. Experimental Design
- **Experiment 1 (Image Footprint)**: Build container images with and without baked-in model weights, comparing image sizes.
- **Experiment 2 (Cold Start vs. Warm Cache vs. Preloaded)**: Profile the latency of three request scenarios:
  - Scenario A: Cold start (first request triggering download of a non-preloaded model).
  - Scenario B: Warm cache (request targeting a model already cached in memory).
  - Scenario C: Eager startup preload (first request targeting the default model pre-warmed during lifespan startup).
- **Experiment 3 (Concurrency & Thread Safety)**: Load test the service with concurrent threads to verify double-checked locking efficiency and thread lock safety.
