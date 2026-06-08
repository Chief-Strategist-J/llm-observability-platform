# Hypothesis: NLI Worker Decoupling — Formal Experimental Design
**Research Date**: 2026-06-05  
**Research Series**: `nli-worker` / Model Registry Decoupling  
**ADR Reference**: [ADR-004 — Model Registry Decoupling for NLI Worker](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/decisions/20260605-004-nli-worker-decoupling.md)  
**Status**: Pre-experiment (hypotheses sealed before data collection)

---

## 1. Research Context and Motivation

The `nli-worker` microservice runs cross-encoder NLI inference using `cross-encoder/nli-deberta-v3-base` (DeBERTa-v3-base, 184M parameters, ~370MB weights). The prior design baked model weights into the container image at build time. This research tests whether a dynamic model registry — where weights are downloaded at startup and cached in an in-memory dict under a threading lock — can meet deployment footprint targets, eliminate cold-start latency on the default path, guarantee concurrent thread safety, and satisfy latency SLOs under long-text dual-pass inference.

Five independent experiments are defined. Each has sealed null and alternative hypotheses, a declared significance level, a power target, and a minimum detectable effect (MDE). All hypotheses were locked before data collection began.

---

## 2. Statistical Framework

### 2.1 Global Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Significance level α | 0.05 | Standard threshold; FP risk of 5% is acceptable for infrastructure experiments |
| Desired statistical power (1 − β) | 0.80 | 80% probability of detecting a true effect at the specified MDE |
| Multiple comparisons correction | None (experiments are independent) | Each experiment addresses a distinct failure mode with non-overlapping metrics |
| Confidence intervals | 95% (two-sided) unless stated | Matches α = 0.05 |

### 2.2 Sample Size Formula (Means Comparison)

For two-sample t-tests with equal allocation:

$$n = \frac{2(z_{1-\alpha/2} + z_{1-\beta})^2 \sigma^2}{\delta^2}$$

Where:
- $z_{1-\alpha/2} = 1.96$ (two-sided, α = 0.05)
- $z_{1-\beta} = 0.842$ (power = 0.80)
- $\sigma$ = estimated population standard deviation
- $\delta$ = minimum detectable effect (MDE)

The combined multiplier $(1.96 + 0.842)^2 = 7.85$ is used throughout.

### 2.3 Sample Size Formula (Proportion Tests)

For binary outcomes (e.g., race condition observed: yes/no):

$$n = \frac{(z_{1-\alpha/2} + z_{1-\beta})^2 [p_0(1-p_0) + p_1(1-p_1)]}{(p_1 - p_0)^2}$$

### 2.4 Expected Measurement Distributions

| Measurement | Assumed Distribution | Justification |
|-------------|---------------------|---------------|
| Container image size (MB) | Deterministic (constant) | Build output is byte-reproducible; no sampling variance |
| Inference latency (ms) | Log-normal | Latency is right-skewed by GC pauses, tokenisation variance, and OS scheduling jitter; confirmed in toxicity-worker characterisation |
| Cold-start download time (ms) | Log-normal | Network I/O latency has a multiplicative error model; P99 can be 10–100× P50 |
| Concurrent thread error count | Binomial(n, p) | Each request either triggers a race condition or it does not; 0/1 outcome |
| Circuit breaker trip time (s) | Normal (approximately) | Controlled deterministic failure injection; variance arises only from OS timer resolution (~1ms jitter) |
| Bloom filter false positive rate | Beta(α_fp, β_fp) | Bayesian posterior over the FP rate; prior Beta(1,1) is non-informative |

> [!NOTE]
> For log-normal measurements, hypothesis tests are conducted on the log-transformed values (i.e., paired or two-sample t-test on `ln(latency_ms)`). Point estimates are reported as geometric means. Cohen's d is computed on log-transformed data.

---

## 3. Algorithm Reference Map

The following table maps each experiment to the specific algorithms from ADR-004 and related design records that the experiment directly validates.

| Algorithm ID | Description | Experiments Validated |
|-------------|-------------|----------------------|
| **ALG-01** | Dynamic model registry: check-before-download with `if m_id not in self._models` gate | EXP-01, EXP-03 |
| **ALG-02** | Global `threading.Lock()` protecting the entire download-and-cache path | EXP-03 |
| **ALG-03** | Per-inference re-acquisition of `self._lock` wrapping `model(**encoding)` forward pass | EXP-03 |
| **ALG-04** | Docker image build without `RUN python download_model.py` step (CPU Dockerfile) | EXP-01 |
| **ALG-05** | Docker image build without baked weights (GPU Dockerfile.gpu) | EXP-01 |
| **ALG-06** | Lifespan startup hook: `_get_model_and_tokenizer(default_model_id)` called at ASGI startup | EXP-02 |
| **ALG-07** | `hasattr` guard for mock injection in test environments during lifespan preload | EXP-02 |
| **ALG-08** | Volume mount passthrough: `/root/.cache/huggingface` → host `~/.cache/huggingface` | EXP-02 |
| **ALG-09** | `AutoModelForSequenceClassification.from_pretrained(m_id).to(device).eval()` load sequence | EXP-02, EXP-04 |
| **ALG-10** | Temperature-scaled softmax: `logits / T` before `torch.softmax(dim=-1)` | EXP-04 |
| **ALG-11** | Token-level chunking via `split_context_by_tokens(max_tokens=400)` for long-text dual-pass | EXP-04 |
| **ALG-12** | `id2label` → label-to-index mapping to resolve DeBERTa NLI logit order (0=contradiction, 1=entailment, 2=neutral) | EXP-04 |
| **ALG-13** | Batch iteration: `range(0, len(pairs), batch_size)` with `bs = batch_size or self._batch_size` | EXP-04 |
| **ALG-14** | HTTP circuit breaker: 3 failures in 10 s window → OPEN state | EXP-05 |
| **ALG-15** | Half-open probe: single test request every 30 s while circuit is OPEN | EXP-05 |
| **ALG-16** | Bloom filter for span deduplication at 1M spans capacity, target FP rate ≤ 0.1% | EXP-05 |
| **ALG-17** | `NliScorerPort` protocol (Clean Architecture) — domain layer never imports concrete HuggingFace classes | EXP-01, EXP-02, EXP-03 |

---

## 4. Experiment Definitions

---

### EXP-01 — Container Image Footprint Reduction

#### 4.1.1 Research Question
Does removing baked-in model weights from the Dockerfile reduce the CPU image size below 1.0 GB?

#### 4.1.2 Formal Hypotheses

$$H_0^{(1)}: \mu_{\text{decoupled,CPU}} \geq 1{,}024 \text{ MB}$$
$$H_1^{(1)}: \mu_{\text{decoupled,CPU}} < 1{,}024 \text{ MB} \quad \text{(one-sided, left-tail)}$$

$$H_0^{(1b)}: \mu_{\text{decoupled,GPU}} \geq \mu_{\text{baked,GPU}} \quad \text{(GPU: no reduction)}$$
$$H_1^{(1b)}: \mu_{\text{decoupled,GPU}} < \mu_{\text{baked,GPU}} \quad \text{(GPU: measurable reduction)}$$

#### 4.1.3 Linked Algorithms
**ALG-04** (CPU Dockerfile weight removal), **ALG-05** (GPU Dockerfile weight removal), **ALG-17** (Clean Architecture port isolation allowing weight-free builds).

#### 4.1.4 Measurement and Expected Distribution
- **Primary metric**: Image size in MB (output of `docker image inspect --format '{{.Size}}'`)
- **Distribution**: Deterministic (build outputs are byte-reproducible under identical base images and dependency lock files)
- **Variance source**: None — this is a point measurement, not a stochastic process. The "test" is a single deterministic comparison against the 1 GB threshold

#### 4.1.5 Sample Size
Docker image builds are deterministic given fixed inputs (pinned base image SHA, locked `requirements.txt`). A minimum of **n = 3 independent builds** per configuration is used to detect any non-determinism in layer caching. If CV > 0.1%, the build environment is investigated before proceeding.

#### 4.1.6 Confounding Variables and Controls

| Confound | Control |
|----------|---------|
| Base image layer caching producing stale layers | Use `--no-cache` flag for all measurement builds |
| Different base image digests across CPU vs GPU | Pin base images by SHA256 digest in Dockerfiles |
| Development dependencies included in production image | Verify only `requirements-prod.txt` is installed; dev packages are excluded |
| Multi-stage build residue | Confirm `COPY --from=builder` excludes model cache directories |

#### 4.1.7 Minimum Detectable Effect
The constraint is a hard threshold at 1,024 MB. Any decoupled image ≥ 1,024 MB constitutes a hypothesis rejection of H₁ and a requirement to revisit the Dockerfile.

#### 4.1.8 Success Criteria
- CPU decoupled image size: **< 1,024 MB** (constraint)
- GPU decoupled image size: **statistically significantly smaller** than GPU baked image
- Build reproducibility: **CV < 0.1%** across 3 builds

---

### EXP-02 — Cold-Start Elimination via Lifespan Preloading

#### 4.2.1 Research Question
Does ASGI lifespan startup preloading of `cross-encoder/nli-deberta-v3-base` reduce the P95 latency of the first HTTP request to be statistically indistinguishable from a warm-cache hit?

#### 4.2.2 Formal Hypotheses

$$H_0^{(2)}: \mu_{\ln L_{\text{preloaded}}} \geq \mu_{\ln L_{\text{cold}}}$$
$$H_1^{(2)}: \mu_{\ln L_{\text{preloaded}}} < \mu_{\ln L_{\text{cold}}} \quad \text{(one-sided)}$$

And, critically, an equivalence test:

$$H_0^{(2b)}: |\mu_{\ln L_{\text{preloaded}}} - \mu_{\ln L_{\text{warm}}}| > \epsilon$$
$$H_1^{(2b)}: |\mu_{\ln L_{\text{preloaded}}} - \mu_{\ln L_{\text{warm}}}| \leq \epsilon \quad \text{(TOST equivalence, } \epsilon = \ln(1.10)\text{)}$$

The equivalence bound ε = ln(1.10) corresponds to ≤ 10% geometric mean difference — i.e., preloaded first-request latency must be within ±10% of warm-cache latency to claim equivalence.

#### 4.2.3 Linked Algorithms
**ALG-06** (lifespan startup hook), **ALG-07** (hasattr mock guard), **ALG-08** (volume mount for persistent cache), **ALG-09** (model load sequence).

#### 4.2.4 Measurement and Expected Distribution
- **Primary metric**: End-to-end HTTP request latency measured at the `POST /v1/nli/score` handler level (wall-clock, including serialisation/deserialisation)
- **Distribution**: Log-normal — $\ln(L) \sim \mathcal{N}(\mu_L, \sigma_L^2)$
- **Three measurement groups**:
  - Group A (Cold): Container started WITHOUT lifespan preload, first request triggers dynamic download
  - Group B (Warm): Container with preload; ≥ 2nd request; model already in `self._models` dict
  - Group C (Preloaded): Container WITH lifespan preload; first request only

#### 4.2.5 Sample Size Calculation

For the cold vs. preloaded comparison (log-scale):
- Estimated $\sigma_{\ln L} = 0.15$ (log-scale SD, equivalent to ~15% CV in latency)
- MDE: $\delta = \ln(7200) - \ln(30) = \ln(240) \approx 5.48$ (difference between 7,200ms cold and 30ms warm, in log-scale)
- Given the enormous effect size (cold start is ~277× longer), the required n is trivially small:

$$n = \frac{2 \times 7.85 \times 0.15^2}{5.48^2} \approx 0.006 \rightarrow n_{\text{min}} = 30 \text{ (practical floor)}$$

For the preloaded vs. warm equivalence test (TOST):
- $\sigma_{\ln L} = 0.10$ (warm-cache variance is tighter; CV ≈ 10%)
- $\epsilon = \ln(1.10) = 0.0953$

$$n_{\text{TOST}} = \frac{2 \times 7.85 \times 0.10^2}{0.0953^2} \approx 17 \rightarrow n_{\text{min}} = 30$$

**Final sample sizes**: n = 30 per group (Groups A, B, C), totalling 90 measurements.

#### 4.2.6 Confounding Variables and Controls

| Confound | Control |
|----------|---------|
| Network speed variance during cold download | Throttle network to 100 Mbps using `tc qdisc` during cold-start tests; report download bandwidth alongside latency |
| OS page cache effects (kernel caching model files) | Drop page cache with `sync; echo 3 > /proc/sys/vm/drop_caches` before each cold-start trial |
| PyTorch just-in-time compilation warming up | Discard first 5 warm-cache measurements; use measurements 6–35 for Group B |
| Container resource limits | Fix: 2 vCPU, 4 GB RAM; no memory swap |
| Tokeniser serialisation overhead | Use identical 3 premise-hypothesis pairs across all groups |

#### 4.2.7 Success Criteria
- $p < 0.05$ for cold vs. preloaded one-sided test: **mandatory**
- TOST p < 0.05 for preloaded vs. warm equivalence: **mandatory** (required to claim "cold-start eliminated")
- Geometric mean of preloaded first-request latency: **≤ 30ms** (matches warm cache)

---

### EXP-03 — Thread-Safe Concurrent Model Access

#### 4.3.1 Research Question
Does the double-checked locking pattern in `_get_model_and_tokenizer` (ALG-01 + ALG-02) guarantee zero race conditions under 16 concurrent threads, where 8 threads target the cached default model and 8 threads simultaneously trigger downloads of two distinct uncached models?

#### 4.3.2 Formal Hypotheses

$$H_0^{(3)}: p_{\text{race}} > 0 \quad \text{(at least one race condition occurs in } N_{\text{trials}} \text{ concurrent runs)}$$
$$H_1^{(3)}: p_{\text{race}} = 0 \quad \text{(zero race conditions; locking is provably correct)}$$

Secondary hypothesis (cached-path lock contention overhead):

$$H_0^{(3b)}: \mu_{L_{\text{cached,concurrent}}} > \mu_{L_{\text{cached,serial}}} + \delta_{\text{lock}} \quad (\delta_{\text{lock}} = 5\text{ms})$$
$$H_1^{(3b)}: \mu_{L_{\text{cached,concurrent}}} \leq \mu_{L_{\text{cached,serial}}} + \delta_{\text{lock}}$$

The secondary test asserts that threads hitting the already-cached model do not incur > 5ms of contention overhead relative to serial baseline, because cached-path threads enter the lock, check the dict (O(1)), and exit immediately.

#### 4.3.3 Linked Algorithms
**ALG-01** (check-before-download gate), **ALG-02** (global `threading.Lock()`), **ALG-03** (per-inference lock re-acquisition for GPU thread safety).

> [!IMPORTANT]
> The current implementation uses a **single global lock** rather than per-model locks. This means that while Model-A is downloading, ALL threads — including those requesting the already-cached default model — must wait for the lock to be released. EXP-03 must measure whether this single-lock design causes measurable contention on the cached path. If it does, ALG-02 may need to be revised to a per-model `defaultdict(Lock)` pattern.

#### 4.3.4 Measurement and Expected Distribution
- **Race condition metric**: Count of `RuntimeError` exceptions, corrupted tensor shapes, or duplicate model instantiation events across $N = 1{,}000$ concurrent trial runs
- **Distribution of race count**: $\text{Binomial}(N, p_{\text{race}})$ under $H_0$
- **Lock contention overhead**: Measured as $L_{\text{concurrent}} - L_{\text{serial}}$ in ms; expected distribution is approximately Normal by CLT (large sample)

#### 4.3.5 Sample Size Calculation

For the proportion test (race conditions):
- $p_0 = 0$ (null: race occurs with probability 0 under correct locking)
- $p_{\text{MDE}} = 0.001$ (we want to detect a 0.1% race rate with 80% power)
- Using the one-proportion exact binomial, the required n to observe 0 failures with 95% confidence that the true rate ≤ 0.1%:

$$n \geq \frac{\ln(0.05)}{\ln(1 - 0.001)} = \frac{-2.996}{-0.001} \approx 2{,}996$$

**Final n**: 3,000 concurrent trial bursts (each burst = 16 threads × 1 request).

For the contention overhead test:
- $\sigma = 2\text{ms}$ (estimated SD of cached-path latency)
- MDE: $\delta_{\text{lock}} = 5\text{ms}$

$$n = \frac{2 \times 7.85 \times 4}{25} \approx 2.5 \rightarrow n_{\text{min}} = 30 \text{ per arm}$$

**Combined**: 3,000 bursts covers both sub-hypotheses.

#### 4.3.6 Confounding Variables and Controls

| Confound | Control |
|----------|---------|
| GIL (Python Global Interpreter Lock) masking true races | Test under both `threading.Thread` AND async `asyncio` coroutines; supplement with `multiprocessing` where GIL is removed |
| Test-environment mock bypassing real download path | Tests run against a local Hugging Face mirror serving real model files, not mocks |
| Non-deterministic thread scheduling hiding races | Use `threading.Barrier` to synchronise all 16 threads to fire simultaneously |
| GPU memory fragmentation (CUDA context races) | Run on CPU only for race condition tests; GPU thread safety is tested separately under ALG-03 |

#### 4.3.7 Success Criteria
- **Zero** `RuntimeError`, `AssertionError`, or model corruption events across all 3,000 bursts: **mandatory**
- Cached-path contention overhead: **< 5ms** geometric mean delta vs. serial baseline: **mandatory**
- P95 latency for cached-path threads during concurrent download: **< 50ms**: **informational** (no download should block cached threads beyond this threshold)

---

### EXP-04 — Throughput Degradation Under Dual-Pass Long-Text Inference

#### 4.4.1 Research Question
For premise-hypothesis pairs whose premises exceed 510 tokens, does the dual-pass chunked inference strategy (ALG-11) cause P95 latency to breach 200ms on a 1 vCPU deployment? And what is the empirical token distribution across real NLI scoring workloads?

#### 4.4.2 Formal Hypotheses

$$H_0^{(4)}: P95(L_{\text{dual-pass,1vCPU}}) \leq 200\text{ms}$$
$$H_1^{(4)}: P95(L_{\text{dual-pass,1vCPU}}) > 200\text{ms} \quad \text{(latency SLO breach under dual-pass)}$$

Secondary hypothesis (token distribution):

$$H_0^{(4b)}: \Pr(\text{tokens} > 510) \leq 0.25 \quad \text{(at most 25% of requests trigger dual-pass)}$$
$$H_1^{(4b)}: \Pr(\text{tokens} > 510) > 0.25$$

#### 4.4.3 Linked Algorithms
**ALG-10** (temperature-scaled softmax), **ALG-11** (token-level chunking, `max_tokens=400`), **ALG-12** (DeBERTa NLI logit label mapping), **ALG-13** (batch iteration loop).

#### 4.4.4 Measurement and Expected Distribution
- **Primary metric**: P95 latency of `score_pairs()` for 800-token premise pairs (log-normal)
- **Secondary metric**: Empirical CDF of premise token lengths from production-representative workload traces
- **Token count distribution**: Expected to follow a heavy-tailed distribution (Pareto or log-normal) based on analogy to NLP workload studies; the 510-token threshold represents the DeBERTa `max_length` boundary

For the P95 latency test:
- **Distribution**: Log-normal — inference time is multiplicatively composed of tokenisation ($O(N)$), two forward passes ($2 \times T_{\text{inf}}$), and overhead
- **Point estimate**: Geometric mean reported alongside arithmetic P95 (since we care about the tail, not the mean)

#### 4.4.5 Sample Size Calculation

For P95 estimation, we require the 95th percentile to be estimated with a 95% CI whose half-width ≤ 10ms:
- Using the order statistic approach for the 95th percentile with sample size n, the CI half-width on a percentile estimate converges as $O(1/\sqrt{n})$
- Empirically, for latency distributions with CV ≈ 0.3, achieving ±10ms CI on P95 requires approximately **n = 500** samples

For the token distribution proportion test:
- $p_0 = 0.25$, $p_1 = 0.33$ (MDE = 0.08)
- $\sigma_p^2 = p_0(1-p_0) + p_1(1-p_1) = 0.1875 + 0.2211 = 0.4086$

$$n = \frac{7.85 \times 0.4086}{0.08^2} \approx 503$$

**Final sample sizes**: n = 500 latency measurements (for P95 CI) + n = 1,000 production request traces (for token distribution CDF).

#### 4.4.6 Confounding Variables and Controls

| Confound | Control |
|----------|---------|
| Other processes consuming CPU cycles | Pin benchmark process to isolated cores using `taskset -c 0`; run in Docker with `--cpuset-cpus=0` |
| Batch size variation affecting throughput | Fix `NLI_BATCH_SIZE=8` via environment variable for all measurements |
| Temperature scaling affecting inference path (not compute) | Confirm: temperature only scales logits post-inference; measure wall-clock to include full path |
| PyTorch thread parallelism from `OMP_NUM_THREADS` | Fix `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1` for 1-vCPU isolation |
| Tokenisation variance for borderline 510-token inputs | Test at 400, 510, 512, 600, 800 tokens to characterise boundary behaviour |

#### 4.4.7 Success Criteria
- **P95 dual-pass latency on 1 vCPU**: Measured and reported (H₀ tests whether it is ≤ 200ms; we expect H₁ to hold — breach is expected)
- **Token distribution > 510 tokens**: Measured empirical proportion reported and tested against 25% threshold
- **Geometric mean single-pass latency (≤ 510 tokens)**: **≤ 50ms** on 1 vCPU (informational SLO target)

---

### EXP-05 — Circuit Breaker State Transition Correctness

#### 4.5.1 Research Question
When the NLI worker becomes unavailable, does the HTTP circuit breaker (ALG-14) correctly transition from CLOSED → OPEN within the specified 10-second failure window, and does it return to CLOSED via the half-open probe (ALG-15) within 30 seconds of worker recovery?

#### 4.5.2 Formal Hypotheses

For the CLOSED → OPEN transition:

$$H_0^{(5a)}: \mu_{T_{\text{open}}} > 30\text{s} \quad \text{(circuit does NOT isolate within 30s)}$$
$$H_1^{(5a)}: \mu_{T_{\text{open}}} \leq 30\text{s} \quad \text{(circuit opens within 30s of the 3rd failure)}$$

For the OPEN → CLOSED recovery:

$$H_0^{(5b)}: \mu_{T_{\text{recover}}} > 60\text{s} \quad \text{(recovery does NOT occur within 60s)}$$
$$H_1^{(5b)}: \mu_{T_{\text{recover}}} \leq 60\text{s} \quad \text{(half-open probe recovers within 60s)}$$

Bloom filter false positive rate:

$$H_0^{(5c)}: p_{\text{FP}} > 0.001 \quad \text{(FP rate exceeds 0.1\% at 1M spans)}$$
$$H_1^{(5c)}: p_{\text{FP}} \leq 0.001 \quad \text{(FP rate} \leq 0.1\%\text{)}$$

#### 4.5.3 Linked Algorithms
**ALG-14** (3-failure/10s window circuit breaker), **ALG-15** (30s half-open probe), **ALG-16** (Bloom filter for span deduplication).

#### 4.5.4 Measurement and Expected Distribution
- **Circuit trip time** $T_{\text{open}}$: Time from first failure to circuit OPEN state (in seconds). Distribution: approximately Normal (controlled failure injection has low timing jitter, ~±1ms from OS clock resolution)
- **Recovery time** $T_{\text{recover}}$: Time from worker restart to circuit CLOSED (bounded above by 30s probe interval + 1 RTT). Distribution: approximately Uniform over [0, 30] seconds (worker may be restarted at any phase of the probe cycle), mean ≈ 15s
- **Bloom filter FP rate**: Proportion of non-inserted keys that test positive. Distribution: Beta(α, β) — Bayesian posterior with $\alpha = \text{FP count} + 1$, $\beta = \text{non-inserted queries} - \text{FP count} + 1$

#### 4.5.5 Sample Size Calculation

For circuit trip time (one-sample t-test against μ₀ = 30s):
- $\sigma = 0.5\text{s}$ (estimated SD from OS timer resolution + HTTP timeout jitter)
- MDE: $\delta = 20\text{s}$ (we expect actual trip time ~10s; want to detect 20s difference from 30s threshold)

$$n = \frac{7.85 \times 0.25}{400} \approx 0.005 \rightarrow n_{\text{min}} = 30$$

For recovery time (one-sample t-test against μ₀ = 60s):
- $\sigma = 5\text{s}$ (variance in probe timing cycle)
- MDE: $\delta = 45\text{s}$ (expected recovery ~15s mean; detect 45s difference from 60s threshold)

$$n = \frac{7.85 \times 25}{2025} \approx 0.097 \rightarrow n_{\text{min}} = 30$$

For Bloom filter FP rate (exact binomial test):
- Query 1,000,000 non-inserted keys; test whether observed FP count is consistent with $p \leq 0.001$
- At $p = 0.001$: expected FP count ≈ 1,000 (large sample, use Normal approximation)
- Power: with n = 1,000,000 queries, power to detect $p = 0.0008$ vs $p_0 = 0.001$ is effectively 1.0

**Final sample sizes**: 30 circuit trip tests + 30 recovery tests + 1,000,000 Bloom filter queries.

#### 4.5.6 Confounding Variables and Controls

| Confound | Control |
|----------|---------|
| HTTP timeout settings masking circuit breaker timing | Set worker timeout to 100ms to ensure failures are fast; distinguish timeout from connection refusal |
| Clock drift between scorer and worker containers | Use monotonic `time.perf_counter()` on the scorer process; do not rely on wall-clock across containers |
| Probe request itself failing due to network partition | Use controlled `docker stop` / `docker start` for deterministic failure injection (not network partition) |
| Bloom filter implementation differences (MurmurHash3 vs xxHash) | Pin Bloom filter library version; document seed and hash function in test fixture |
| Worker warmup time masking recovery time | Account for ASGI lifespan startup time (verified in EXP-02) separately from circuit recovery time |

#### 4.5.7 Success Criteria
- Circuit trip time: **$P95(T_{\text{open}}) \leq 30\text{s}$** — i.e., 95% of failure injection scenarios trip the circuit within 30 seconds
- Expected actual mean trip time: **≤ 10.5s** (3 failures × ~3.4s/failure interval under 10s window)
- Recovery time: **$P95(T_{\text{recover}}) \leq 45\text{s}$** (30s probe + 15s buffer for worker startup)
- Bloom filter FP rate at 1M spans: **≤ 0.10%** (≤ 1,000 false positives)

---

## 5. Confounding Variables: Cross-Experiment Controls

The following confounders apply globally across all five experiments and are controlled identically.

| Global Confound | Control Mechanism |
|-----------------|-------------------|
| Python garbage collection pauses | Disable GC during measurement windows with `gc.disable()`; re-enable after |
| OS thermal throttling | Monitor CPU frequency with `cpupower frequency-info`; discard measurements if clock drops > 5% |
| Docker daemon overhead | All experiments run inside containers on identical host hardware (AMD Ryzen 7, 32 GB RAM); no host processes pinned to measured cores |
| Hugging Face model download CDN variance | For experiments requiring model loads, use a locally hosted `huggingface_hub` mirror with fixed RTT ≤ 5ms |
| PyTorch version non-determinism | Pin `torch==2.3.1+cpu`; set `torch.use_deterministic_algorithms(True)` |
| Temperature parameter affecting score distributions | Fix `temperature=1.5` across all inference measurements (matches production default) |

---

## 6. Experiment Execution Order

Experiments are executed in dependency order to prevent model cache state from one experiment contaminating another:

```
EXP-01 (image build)        ─── no runtime deps
EXP-02 (cold-start)         ─── requires fresh container with empty HF cache
EXP-03 (concurrency)        ─── requires EXP-02 to confirm preload works first
EXP-04 (dual-pass latency)  ─── requires EXP-03 to confirm thread safety
EXP-05 (circuit breaker)    ─── requires EXP-02 (preload) and EXP-04 (latency characterisation)
```

Between each experiment, containers are **fully destroyed and recreated** (`docker rm -f`), and the HF cache directory is wiped (`rm -rf ~/.cache/huggingface/hub/models--cross-encoder*`) to eliminate warm-cache carry-over.

---

## 7. Pre-Registration Attestation

| Field | Value |
|-------|-------|
| Hypotheses sealed | 2026-06-05T09:00:00+05:30 |
| Data collection start | 2026-06-05T10:30:00+05:30 |
| Analysis performed by | Platform Engineering — NLI Squad |
| Blinding | Not applied (infrastructure measurements; blinding not applicable) |
| Pre-registration method | Git commit of this file before any experiment data was collected |
| ADR that motivated experiments | [ADR-004](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/decisions/20260605-004-nli-worker-decoupling.md) |
| Related prior work | Toxicity worker decoupling ([ADR-0001](file:///home/btpl-lap-22/live/obs/docs/adr/0001-toxicity-worker-decoupling.md)), Perplexity dual-path ([ADR-002](file:///home/btpl-lap-22/live/obs/notebooks/runbooks/decisions/20260603-002-perplexity-dual-path-scoring.md)) |

---

*Document owner: Platform Engineering — NLI Squad | Research series: 2026-06-05-decoupling*
