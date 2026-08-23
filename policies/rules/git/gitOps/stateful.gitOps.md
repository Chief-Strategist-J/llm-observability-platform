# Stateful GitOps Rollbacks — Immutable State

*Tracks compiled configurations via Git hashes; performs instant rollback when automated integration tests fail.*

---

## 1. What Is This?

**Stateful GitOps Rollback** is a deployment discipline where:

1. Every deployable configuration is **compiled** from source (Helm/Kustomize/CUE/Jsonnet templates → rendered manifests) into a single, **content-addressed artifact** — identified by a hash (usually the Git commit SHA, sometimes a hash of the compiled output itself).
2. That hash is the **only mutable pointer** in the entire system — the manifests/artifacts it points to are never edited in place, only ever superseded by a new hash.
3. A controller continuously **reconciles** live infrastructure state toward whatever hash is currently declared as "desired" in Git.
4. After every sync, **automated integration tests** gate promotion — if they fail, the system **does not attempt to "fix" the current state**; it instantly re-points the desired-state pointer back to the last known-good hash and lets the same reconciliation loop undo the change.

The core trick: **rollback is not "undo," it's "re-apply a different immutable value."** This is the entire reason it's fast and safe — you are never computing a diff of "how do I get back," you are simply re-declaring "the desired hash is X" and letting the same forward-only reconciliation machinery run again.

**What it is not:**
- Not a backup/restore system (that recovers from *loss*; this recovers from *bad intent that was faithfully deployed*).
- Not a database rollback / transaction rollback (those undo *data* mutations; this undoes *configuration* mutations — and the interaction between the two is the hardest edge case, see §5).
- Not blind "revert the git commit" — a naive `git revert` still needs the *exact same* content-addressable, immutable-artifact discipline underneath it, or the "revert" can silently deploy something different from what was actually running before.

---

## 2. Why? — From First Principles

### 2.1 The core problem this solves

Traditional imperative deployment ("SSH in and run this script," "kubectl edit," "click a button in a console") produces state that is **path-dependent** — the current state of a server depends on the entire history of operations ever run against it, not just on its declared configuration. This means:

- You cannot **reproduce** a given state without replaying its exact operational history.
- You cannot **roll back** without knowing the inverse of every operation ever applied (and many operations, like `apt upgrade`, have no clean inverse).
- Configuration **drifts** invisibly, because nothing continuously compares "what should be running" to "what is running."

### 2.2 The first-principles fix: make state a pure function of a hash

If you define:

```
State = f(CompiledConfig)
CompiledConfig = compile(GitCommitHash)
```

...and `compile()` is **deterministic** (same commit → byte-identical output, always), then the entire operational history collapses to a single fact: **which hash is currently desired.** This is the same principle functional programming uses to make code reproducible (pure functions, immutable values) applied to infrastructure. Two direct consequences fall out for free:

1. **Reproducibility**: state at any point in time is fully described by one hash — you can recreate it anywhere, any time.
2. **Rollback becomes O(1) in *decision* cost**: "go back" is just "declare a different, already-known-good hash" — no inverse operations need to be computed, because the forward reconciliation path *is* the only path, run again with an old value.

### 2.3 Why "instant" is achievable and not just marketing

Rollback latency in this model is bounded by **reconciliation-loop convergence time**, not by "figuring out what to undo." Since the controller's job is always "make live state match hash X," rolling back to hash X-1 costs exactly the same as any other sync — there is no separate "rollback code path" to be slow, buggy, or untested. This is the first-principles reason GitOps rollback can be dramatically faster and safer than imperative rollback: **it eliminates an entire code path (the undo path) by construction**, rather than optimizing it.

---

## 3. Core Architecture — Full Decision Trees

### 3.1 Decision Point 1 — What Triggers a Rollback?

```log
└── Q1: What signal decides "this deployment is bad, revert it"?
    ├── Automated Integration Test Failure
    │   ├── Pre-sync test gate (run tests against compiled artifact before it's ever applied live)
    │   └── Post-sync smoke test (apply, then immediately test against the live result)
    ├── Health-Check / SLO Breach
    │   ├── Liveness/readiness probe failures crossing a threshold
    │   └── Error-rate / latency SLO burn-rate alert (canary analysis metric)
    ├── Manual Trigger
    │   ├── Human declares "rollback" via GitOps CLI/PR (re-point hash manually)
    │   └── Emergency break-glass rollback (bypasses normal PR review for speed)
    └── Policy/Admission Rejection
        ├── OPA/Gatekeeper policy violation detected post-hoc
        └── Security scan finding on the deployed artifact
```

### 3.2 Decision Point 2 — How Is "Last Known-Good" Identified?

```log
└── Q2: Which hash do you roll back TO?
    ├── Last Green Commit (CI-verified)
    │   ├── Tracked via a dedicated "stable" branch/tag that only moves on full green pipeline
    │   └── Risk: "last green" might itself be stale if tests were flaky-passing
    ├── Explicit Release Tag
    │   ├── Human-curated, semantically versioned (v1.4.2)
    │   └── Decouples "what CI approved" from "what ops promoted to prod"
    ├── N-1 Immutable Snapshot (rolling window)
    │   ├── Keep last K compiled-artifact hashes regardless of tagging
    │   └── Enables rollback even if the tagging process itself is broken
    └── Bisection (multi-step rollback)
        ├── If N-1 is also bad, walk back further (git-bisect-style) until tests pass
        └── Requires tests to be deterministic enough for bisection to converge
```

### 3.3 Decision Point 3 — How Is Rollback Executed?

```log
└── Q3: What actually happens, mechanically, to roll back?
    ├── Pull-Based Reconciliation (controller-driven)
    │   ├── Update desired-state pointer (git ref / registry tag) to old hash
    │   ├── Controller's normal reconcile loop detects drift and re-applies old hash
    │   └── No separate "rollback code" — same code path as any sync
    ├── Push-Based Re-Deploy
    │   ├── CI/CD pipeline explicitly re-triggers deploy job with old artifact hash
    │   └── Requires rollback to be a first-class pipeline stage, not an afterthought
    ├── Blue-Green Pointer Swap
    │   ├── Old version ("blue") kept fully running alongside new ("green")
    │   ├── Rollback = flip traffic-routing pointer back to blue
    │   └── Fastest possible rollback (no redeploy at all, just routing change)
    └── Git-Level Revert
        ├── git revert <bad-commit> creates a new commit restoring old manifests
        ├── Preferred when full audit trail of "we reverted X because Y" matters
        └── Requires compile() determinism to guarantee the reverted commit reproduces the exact prior artifact
```

### 3.4 Decision Point 4 — How Is the Immutable Artifact Produced?

```log
└── Q4: How do you go from source to a hash-addressed, immutable config?
    ├── Templating/Compile Step
    │   ├── Helm (values.yaml + charts → rendered manifests)
    │   ├── Kustomize (base + overlays → rendered manifests)
    │   └── CUE/Jsonnet (typed config language → rendered manifests, strongest determinism guarantees)
    ├── Hashing Strategy
    │   ├── Hash the Git commit SHA directly (simplest, but doesn't capture non-Git inputs)
    │   ├── Hash the compiled output (SHA256 over rendered manifest bytes — catches template/engine version drift)
    │   └── Hash the full dependency closure (source + template engine version + values — strongest reproducibility)
    ├── Storage
    │   ├── OCI Registry (store compiled manifests as OCI artifacts, same infra as container images)
    │   ├── Git repo itself (compiled manifests committed to a separate "rendered" branch)
    │   └── Artifact store (S3/GCS with content-addressable keys)
    └── Determinism Guarantee (the load-bearing assumption of the whole pattern)
        ├── Pinned template-engine version
        ├── No wall-clock/random inputs in templates
        └── Reproducible-build verification (rebuild from source, confirm hash matches)
```

### 3.5 Decision Point 5 — How Do Integration Tests Gate Promotion?

```log
└── Q5: Where do automated tests sit relative to the deploy?
    ├── Pre-Sync Gate (test before apply)
    │   ├── Deploy to ephemeral/staging environment first
    │   ├── Run integration suite against staging
    │   └── Only promote hash to prod ref if suite passes
    ├── Post-Sync Canary Analysis
    │   ├── Apply to a small traffic percentage (canary)
    │   ├── Automated analysis (Argo Rollouts-style) compares canary metrics vs baseline
    │   └── Auto-promote on pass / auto-rollback on fail, no human in the loop
    ├── Post-Sync Smoke Test
    │   ├── Apply fully, immediately run a fast synthetic-transaction suite
    │   └── Fastest feedback, but riskiest (full blast radius before any test result)
    └── Shadow/Dark-Launch Validation
        ├── New version receives mirrored (non-authoritative) production traffic
        ├── Compare outputs against current live version without affecting real users
        └── Promote only after shadow comparison passes over a time window
```

### 3.6 Decision Point 6 — Drift Detection & Reconciliation Behavior

```log
└── Q6: What happens when live state diverges from the declared hash without a rollback event?
    ├── Detection
    │   ├── Periodic diff (poll live cluster state vs desired manifest, e.g. every N seconds)
    │   └── Event-driven diff (watch API server events, react immediately)
    ├── Auto-Heal
    │   ├── Silently re-apply desired state, overwriting out-of-band changes
    │   └── Risk: destroys legitimate emergency hotfixes made outside Git
    ├── Alert-Only
    │   ├── Flag drift to humans, do not auto-correct
    │   └── Risk: drift persists and compounds until someone acts
    └── Drift-as-Rollback-Trigger
        └── Treat unexpected drift itself as a signal to re-run the full test gate (§3.5) before deciding to heal or accept
```

---

## 4. Edge Cases

- **Rollback ping-pong**: flaky tests fail intermittently → system rolls back → next sync retries the "bad" hash → passes/fails randomly → repeated oscillation between two hashes, burning deploy budget and confusing on-call.
- **Non-reversible side effects**: config rollback is instant, but if the bad deploy already ran a **database migration**, a schema change, or sent an irreversible external API call (charged a payment, sent an email), rolling back the *config* does not undo the *data* — the two are on fundamentally different timelines (see §5).
- **Non-deterministic compile step**: if `compile()` isn't actually deterministic (embeds a build timestamp, depends on template-engine version drift, or a non-pinned dependency), the same Git hash produces different artifacts on different days — silently breaking the entire "hash = state" assumption.
- **Partial rollback under eventual consistency**: a reconciler managing many resources may roll back some resources faster than others, producing an inconsistent intermediate state (e.g., new API server + old client config) that never existed as a tested combination.
- **Cascading rollback across dependent services**: rolling back Service A's config to be compatible again may break a contract with Service B, which had already been rolled forward to expect A's new behavior — rollback safety is not a single-service property.
- **Rollback storms**: multiple independent test failures across unrelated changes trigger concurrent rollback events that race on the same shared resources (e.g., a shared ConfigMap), producing a worse state than either individual bad deploy.
- **Stale/incomplete test coverage**: automated tests pass (false green) because they don't cover the actual failure mode; the bad state stays live in production long after "instant rollback" should have caught it — the pattern is only as good as its test suite's coverage.
- **Hash-pinned but semantically broken dependency**: pinning a hash guarantees byte-identical *config*, but a pinned base image or library can still have a runtime bug that only appears under production load the test environment never reached.
- **Rollback during active migration window**: rolling back mid-way through a multi-step rollout (e.g., half the fleet already on new schema) can leave the fleet permanently split if the rollback path doesn't also handle in-flight nodes.

---

## 5. The Hardest / Most Difficult Thing

**Distinguishing "the new config caused this failure" from "something unrelated and transient caused this failure," and separately, handling the fact that config state is immutable/reversible but data state is not.**

This has two faces:

1. **Causal attribution under noisy signals** — an integration test failure or SLO breach right after a deploy is *correlated* with the deploy, not *proven* to be caused by it. A downstream dependency outage, a network blip, or a coincidental traffic spike can produce the exact same signal. Rolling back based on correlation alone can (a) mask a real, unrelated production incident behind a false "we fixed it by rolling back" narrative, and (b) discard a genuinely good deploy because of bad luck in timing. This is structurally the same problem as distinguishing "true concurrency" from "causally related" writes in replicated systems (§5 of the Replication article) — you are inferring causality from imperfect, time-ordered signals without a ground-truth oracle.

2. **The immutability boundary is a lie at the data layer** — the entire pattern's power comes from configuration being immutable and hash-addressable. But the moment a deployed change touches **mutable external state** (a database row, a sent webhook, a charged credit card, a message already consumed off a queue), that state has no hash to roll back to. You cannot "re-point a pointer" for data that has already caused real-world side effects. Handling this honestly requires either (a) designing all such side effects to be idempotent and compensable (see Compensating Transaction pattern, §8.16), or (b) explicitly accepting that some deploys are simply **not safely rollback-able** and gating them with stronger pre-deploy checks instead of relying on the rollback safety net.

---

## 6. The Most Complex Part

**The reconciliation control loop's consistency guarantees under concurrent drift, partial application, and dependent-resource ordering.**

A GitOps controller is, structurally, running a never-ending distributed consensus problem: "what is the current desired state, and does live state match it, accounting for the fact that (a) live state can change out-of-band at any moment, (b) applying a full desired-state graph to many resources is not atomic, and (c) resources have dependencies on each other that the flat hash doesn't encode by default."

This is complex for the same underlying reason Raft/Paxos is complex (§6 of the Replication article): you need **safety** (never apply a partially-consistent intermediate state that violates invariants) and **liveness** (eventually converge) simultaneously, under a network and API server that can fail, lag, or partially apply requests mid-sync. The added wrinkle specific to GitOps is **dependency ordering** — a naive reconciler that applies all resources in parallel can, e.g., roll back a Deployment before rolling back the ConfigMap it mounts, producing a crash-loop that a "correct" ordered rollback would have avoided. Encoding and respecting this dependency graph correctly, *especially during rollback*, is the load-bearing hard problem — most production GitOps incidents trace back to this, not to the hashing/immutability mechanics, which are comparatively simple.

---

## 7. Relation to Data and Modern AI

- **Model registry as GitOps for ML**: model artifacts are hash-pinned (checksum or content-addressed storage, e.g. MLflow/DVC), and a "promote model to production" event is structurally identical to promoting a Git hash — rollback is "re-point the serving layer to the previous model hash," instant and code-path-free, exactly as in §2.3.
- **Automated eval-gates as integration tests**: LLM/ML pipelines increasingly gate promotion on automated eval suites (accuracy/safety/regression benchmarks) exactly as this pattern gates on integration tests — a regression in eval score triggers automatic rollback to the last model hash that passed, before any human notices in production.
- **Prompt versioning**: hash-addressed prompt templates (each prompt version content-hashed and stored immutably) let LLM applications instantly roll back a prompt change that causes a spike in refusals, hallucination rate, or user complaints — same mechanics as config rollback, applied to prompt text instead of YAML manifests.
- **Data versioning (DVC, LakeFS, Delta Lake time travel)**: training datasets are content-addressed and immutable, so a training run can be reproduced or rolled back to an exact prior dataset hash — directly analogous to §2.2's "state is a pure function of a hash," applied to training data instead of infra config.
- **Feature flag + canary model rollout**: gradual traffic shifting to a new model version, monitored by automated drift/quality metrics, with auto-rollback on regression — this is Progressive Delivery (§8.7) applied to inference traffic instead of application traffic.
- **The non-reversibility edge case is sharper in AI systems**: a bad model version that has already written outputs into a user-facing system (sent a generated email, taken an autonomous action via an agent) faces the exact §5 problem — the model artifact rolls back cleanly, but the *actions the bad model already took* do not un-happen, making compensating-transaction design disproportionately important for agentic AI systems specifically.

---

## 8. 17 Design Patterns Related to Stateful GitOps Rollbacks

Each pattern below is broken into four parts to build a real mental model rather than a label:
**Definition** (what it is, precisely), **When to Use** (the condition that makes it the right tool), **Who** (which component/role owns and drives it), and **How It Works Internally** (the mechanism, not just the name).

### 8.1 GitOps Reconciliation Loop (Pull-Based Sync)

- **Definition**: A control loop that continuously compares a declared desired state (in Git) against live infrastructure state and drives the live state toward the declared one, without being told to by an external push event.
- **When to Use**: Whenever you want the *system itself*, not a pipeline, to be the source of enforcement — so that drift, crashes, or missed deploys self-correct over time instead of silently persisting.
- **Who**: A long-running controller/operator (e.g., Argo CD, Flux) running inside or adjacent to the target environment, watching a Git repo as its only input.
- **How It Works Internally**: The controller polls (or watches) Git for the current desired hash, fetches the compiled manifest for that hash, diffs it against the live cluster's actual object state via the API server, and applies only the delta. It repeats this forever, on an interval or on webhook/watch events, which is what makes rollback "free" — rolling back is just changing what Git says the desired hash is; the *same* loop then undoes the bad state on its next tick.

### 8.2 Push-Based Continuous Deployment

- **Definition**: A pipeline-driven deployment model where a CI/CD job actively pushes a new artifact to the target environment as a discrete, one-time action, rather than a controller continuously pulling.
- **When to Use**: When deploys are infrequent, tightly coupled to a pipeline's own gating logic (build → test → deploy in one linear job), or when the target environment has no room to run a persistent controller (e.g., a single VM, a serverless function).
- **Who**: The CI/CD pipeline/job runner (GitHub Actions, Jenkins, GitLab CI) acting as the deploy agent.
- **How It Works Internally**: On a trigger (merge, tag, manual click), the pipeline resolves the artifact to deploy, authenticates to the target environment, and issues direct apply/deploy calls. There is no standing process watching for drift afterward — if something changes the live state out-of-band, nothing notices until the next pipeline run, which is the core structural difference from 8.1.

### 8.3 Content-Addressable Configuration (Hash-Pinned Artifacts)

- **Definition**: A storage and identity scheme where a configuration artifact's name/identifier *is* a deterministic hash of its own content, so identical content always produces the identical identifier and any content change produces a new one.
- **When to Use**: Whenever you need to prove "this exact state ran here" with certainty, or need rollback to be a pure reference-swap rather than a recomputation — i.e., any time immutability and reproducibility matter more than human-readable versioning.
- **Who**: The build/compile step of the CI pipeline, and the artifact registry that stores the result.
- **How It Works Internally**: Source templates are rendered with fixed inputs (values, engine version) into byte-exact output; a cryptographic hash (SHA256) is computed over those bytes; the artifact is stored keyed by that hash. Any two builds from identical source+inputs are byte-identical and therefore hash-identical — this is the mechanism that makes "rollback = re-point to old hash" logically sound, because the hash uniquely and permanently identifies one specific state.

### 8.4 Immutable Infrastructure

- **Definition**: An operational model where running infrastructure (servers, containers, VMs) is never modified in place after creation — any change is deployed by creating entirely new instances from a new image/artifact and discarding the old ones.
- **When to Use**: Whenever configuration drift, "it works on this server but not that one," or unreproducible production incidents are a recurring problem — i.e., whenever you need every instance of "version X" to be provably identical.
- **Who**: The infrastructure provisioning layer (Terraform, Packer, Kubernetes ReplicaSets, autoscaling groups) that creates/destroys instances rather than patching them.
- **How It Works Internally**: A new artifact hash triggers provisioning of a whole new instance set from that artifact (fresh VM image, fresh container). Traffic is redirected to the new set once healthy; the old set is torn down (or kept briefly for rollback). Because no instance is ever patched, "what's running" is always fully explained by "which artifact hash it was created from" — no hidden mutation history to account for.

### 8.5 Blue-Green Deployment

- **Definition**: A release strategy that keeps two complete, independent environments ("blue" = currently live, "green" = new version) running simultaneously, and switches all traffic from one to the other atomically.
- **When to Use**: When you need the fastest possible rollback (a routing change, not a redeploy) and can afford to run two full environments' worth of capacity at once, even briefly.
- **Who**: The deployment/release orchestrator and the load balancer / traffic router it controls.
- **How It Works Internally**: The new version is deployed fully into the idle environment while the old one keeps serving all live traffic. After validation, the router's target is flipped from blue to green in one atomic operation. Rollback is simply flipping the router back — no new deployment, no reconciliation wait, just a routing-table change, which is why it's the fastest rollback mechanism in this entire pattern family.

### 8.6 Canary Release with Automated Analysis

- **Definition**: A release strategy that exposes a new version to a small, controlled slice of real production traffic first, and uses automated metric comparison (not human judgment) to decide whether to expand or abort that exposure.
- **When to Use**: When you want real production signal before full rollout, but blue-green's "all or nothing" traffic switch is too risky for the blast radius you're willing to accept.
- **Who**: A progressive-delivery controller (Argo Rollouts, Flagger) plus a metrics backend (Prometheus, Datadog) it queries automatically.
- **How It Works Internally**: A small percentage of traffic (or a small pod count) is routed to the new version alongside the stable baseline. The controller periodically queries success-rate, latency, and error metrics for both versions, computes the delta, and compares it against a configured threshold. If the delta stays within bounds, traffic weight to the canary increases stepwise; if it breaches the threshold, the controller automatically zeroes canary traffic — no human decision required in the loop.

### 8.7 Progressive Delivery (Staged Rollout Gates)

- **Definition**: The umbrella strategy of releasing a change through a sequence of increasing-exposure stages (e.g., 1% → 10% → 50% → 100%), each gated by an automated pass/fail check before advancing to the next.
- **When to Use**: For any change where the cost of a full-blast failure is high enough to justify multiple, automatically-gated checkpoints rather than a single canary check.
- **Who**: The same progressive-delivery controller as 8.6, orchestrating a sequence of canary-style stages rather than a single one.
- **How It Works Internally**: The controller executes a state machine of stages, each with a target traffic weight and a "bake time" (how long to observe before judging). At each stage transition, it re-runs the same kind of automated analysis as 8.6; a failure at *any* stage triggers the same automatic rollback as 8.6, but a pass at every stage eventually promotes the new version to be the new 100%-traffic baseline.

### 8.8 Automated Rollback on Health-Check Failure

- **Definition**: A safety mechanism where a deploy is automatically reverted if post-deploy health signals (liveness probes, readiness checks, error-rate thresholds) fail within a defined observation window, with no human approval required.
- **When to Use**: As a baseline safety net on essentially every automated deploy, especially where the team cannot guarantee a human will be watching immediately after every release.
- **Who**: The deployment controller itself (not a separate system) — it owns both the deploy action and the rollback trigger.
- **How It Works Internally**: Immediately after applying a new state, the controller starts polling health endpoints (or subscribing to alerting signals) on a timer. If health checks fail to turn green within a configured max-wait window, the controller re-applies the previously-recorded "last known good" artifact — using the exact same apply mechanism it used for the forward deploy, just with an older reference.

### 8.9 Declarative Desired-State Management

- **Definition**: A configuration model where you specify *what the end state should look like* (declarative) rather than *what steps to run to get there* (imperative), and let a separate mechanism figure out the steps.
- **When to Use**: Anywhere you want state to be reproducible from a single source of truth and want "what should be running" to be answerable by reading one file, not by reading an operational runbook/history.
- **Who**: The developer/operator authoring the desired-state files, and the reconciliation controller (8.1) that reads and enforces them.
- **How It Works Internally**: A desired-state file (or a pointer to a compiled artifact hash) lives in Git as the single writable source of truth. Nothing else is allowed to be authoritative — any other system that wants to change live state must do so by changing this file, which is what makes drift *detectable*: anything not derivable from this file is, by definition, drift.

### 8.10 Drift Detection & Auto-Heal

- **Definition**: A monitoring mechanism that continuously compares live infrastructure state against declared desired state (8.9) and either corrects (auto-heal) or alerts on any divergence found.
- **When to Use**: In any environment where out-of-band changes are possible (someone runs `kubectl edit`, a manual hotfix, a misbehaving external automation) and you need to know about — or automatically eliminate — the resulting inconsistency.
- **Who**: The same reconciliation controller as 8.1, typically running this as a background pass distinct from its normal sync trigger.
- **How It Works Internally**: On an interval independent of new-commit events, the controller re-fetches live object state and diffs it field-by-field against the expected manifest. If a diff is found and auto-heal is enabled, it re-applies the expected manifest, silently overwriting the drifted fields; if alert-only, it emits a structured diff to an alerting channel and takes no corrective action.

### 8.11 Version-Pinned Dependency Graph (Lockfile Pattern)

- **Definition**: A mechanism that resolves a set of loosely-specified dependency version ranges into one exact, fully-resolved set of versions, recorded in a lockfile so every future install is byte-identical.
- **When to Use**: Whenever a configuration or build depends on external packages/images/modules whose "latest" version could silently change between builds — i.e., whenever reproducibility (8.3, 8.4) needs to extend past your own source code into everything it depends on.
- **Who**: The dependency resolver tool (npm/yarn, pip/poetry, Helm chart dependency lock) run during the build/compile step.
- **How It Works Internally**: Given loose ranges (`^1.2.0`), the resolver picks one exact version per dependency satisfying all constraints, and writes that resolved set (name → exact version, often with a content hash) into a lockfile. Future builds read the lockfile instead of re-resolving ranges, guaranteeing that "the same source" always produces "the same dependency closure" — a prerequisite for §3.4's determinism guarantee to actually hold.

### 8.12 Feature-Flag-Gated Rollout

- **Definition**: A mechanism that decouples *deploying* code from *activating* a behavior, by wrapping the new behavior in a runtime-evaluated flag that can be toggled independently of any deployment.
- **When to Use**: When you want rollback to be instantaneous and independent of the deployment pipeline entirely — flipping a flag is a config change with no build, no artifact, no reconciliation wait.
- **Who**: The application code itself (which checks the flag at runtime) and a feature-flag service/config that operators control directly.
- **How It Works Internally**: At the point a new code path would execute, the application queries a flag-evaluation function with the current user/request context. The function checks a kill switch, an allow-list, and a rollout-percentage bucket (usually a stable hash of user ID modulo 100) to decide true/false. "Rollback" here means flipping the kill switch or rollout percentage to zero — the deployed code is untouched; only its *activation* is reverted.

### 8.13 Snapshot/Checkpoint-Based Rollback (Stateful Stores)

- **Definition**: A mechanism for reverting a *stateful*, mutable data store (unlike immutable config) to a previously captured point-in-time snapshot.
- **When to Use**: Whenever a rollback needs to reach beyond configuration into actual data — e.g., a bad migration corrupted rows, and config-hash rollback alone cannot undo that.
- **Who**: The stateful store itself (database, message queue, key-value store) and whatever backup/checkpoint tooling manages its snapshots.
- **How It Works Internally**: On a schedule or before a risky operation, the store's checkpoint mechanism captures a consistent point-in-time image (e.g., a WAL-based consistent snapshot, an LSM-tree checkpoint). Rollback restores the store's state from that image — which is inherently slower and more disruptive than config rollback, because it usually requires pausing writes and can lose any data written after the snapshot was taken.

### 8.14 Shadow Deployment / Dark Launch

- **Definition**: A validation technique where a new version receives a *mirrored copy* of real production traffic but its responses are never returned to real users — only recorded and compared against the current live version's responses.
- **When to Use**: When you need real production-traffic-shaped validation for a change too risky to expose to any real user yet, even at canary-level (1%) exposure.
- **Who**: A traffic-mirroring proxy/service mesh feature, plus an offline or async comparator process.
- **How It Works Internally**: Incoming requests are duplicated — one copy goes to the live (authoritative) version and is returned to the user as normal; the other copy is sent asynchronously to the shadow version, whose response is discarded from the user's perspective but logged. A comparator later checks how often shadow and live responses agree; only once agreement stays above a threshold over enough samples does the new version proceed toward canary/progressive rollout (8.6/8.7).

### 8.15 Multi-Stage Promotion Pipeline (dev → staging → prod)

- **Definition**: A pipeline structure where a single artifact hash is promoted sequentially through a fixed series of environments, each running its own test suite, and only reaching production after passing every prior stage.
- **When to Use**: Whenever you want increasing confidence and increasing blast-radius risk to be explicitly staged, rather than testing once and deploying everywhere simultaneously.
- **Who**: The CI/CD pipeline orchestrator, coordinating with each environment's test runner in sequence.
- **How It Works Internally**: The exact same artifact hash (never rebuilt between stages — that would break §3.4's determinism guarantee) is deployed to dev, its test suite runs; on pass, the identical hash is deployed to staging, its suite runs; on pass, promoted to prod. A failure at any stage halts promotion at that stage — the hash never reaches the stages after it, and existing production stays on its last-promoted hash.

### 8.16 Compensating Transaction Pattern (for non-reversible side effects)

- **Definition**: A design pattern where, instead of relying on a true "undo" (which may not exist), every risky action is paired at design time with an explicit *compensating action* that semantically counteracts its effect (e.g., "charge card" pairs with "refund card").
- **When to Use**: Anywhere a deploy or workflow step causes an effect outside the system's own immutable-config boundary — a real payment, a sent notification, a message already consumed off a queue — where config-hash rollback (§2.3) has no power.
- **Who**: The application/workflow author, who must explicitly define the compensation logic; there is no generic mechanism that can invent one for you.
- **How It Works Internally**: Every side-effecting action is recorded in a log alongside its paired compensating action at the moment it executes. If a rollback is later triggered, the system walks the log in reverse order and executes each compensation in turn — this is fundamentally different from config rollback because it is an *active, sequential execution of new operations*, not a passive re-pointing of a reference.

### 8.17 Policy-as-Code Admission Gating (pre-sync policy checks)

- **Definition**: A mechanism that evaluates a compiled configuration against a set of machine-readable rules (security, compliance, resource limits) *before* it is ever applied to a live environment, rejecting it outright on violation.
- **When to Use**: Whenever you want to prevent a whole class of bad states from ever reaching production, rather than relying on rollback to clean them up after the fact — i.e., prevention layered in front of the rollback safety net.
- **Who**: A policy engine (Open Policy Agent/Gatekeeper, Kyverno) invoked as an admission webhook or a pre-sync CI step.
- **How It Works Internally**: The compiled manifest (from 8.3) is passed through a rules engine that evaluates a bundle of declarative policies (e.g., "no container may run as root," "all Deployments must set resource limits") against the manifest's contents. Any violation returns a structured rejection before the manifest ever reaches the reconciliation loop (8.1) — this runs *earlier* in the pipeline than every other pattern in this list, since its entire purpose is to stop bad states before they become "current state" at all.

---

## 9. Relationship Between the Patterns (Full Tree)

```log
└── Stateful GitOps Rollback
    ├── Foundation Layer
    │   ├── Declarative Desired-State Management (9)
    │   │   └── enables → GitOps Reconciliation Loop (1)
    │   ├── Content-Addressable Configuration (3)
    │   │   ├── requires → Immutable Infrastructure (4)
    │   │   └── requires → Version-Pinned Dependency Graph (11)
    │   └── Immutable Infrastructure (4)
    │       └── makes-possible → instant rollback via pointer re-declaration
    ├── Delivery Mechanism Layer
    │   ├── GitOps Reconciliation Loop (1)
    │   │   └── alternative-to → Push-Based Continuous Deployment (2)
    │   ├── Blue-Green Deployment (5)
    │   │   └── specialization-of → instant-pointer-swap rollback (fastest form of 1)
    │   ├── Canary Release (6)
    │   │   └── generalized-by → Progressive Delivery (7)
    │   ├── Shadow Deployment (14)
    │   │   └── precedes → Canary Release (6) in cautious pipelines
    │   └── Multi-Stage Promotion Pipeline (15)
    │       └── composes → { 5, 6, 7, 14 } across environments
    ├── Gating Layer
    │   ├── Automated Rollback on Health-Check Failure (8)
    │   │   └── consumes-signal-from → Canary Release (6), Drift Detection (10)
    │   ├── Policy-as-Code Admission Gating (17)
    │   │   └── runs-before → artifact ever reaches (1)
    │   └── Feature-Flag-Gated Rollout (12)
    │       └── decouples → deploy event from user-visible activation
    ├── Consistency/Repair Layer
    │   ├── Drift Detection & Auto-Heal (10)
    │   │   └── backstops → (1) between scheduled syncs
    │   └── Snapshot/Checkpoint-Based Rollback (13)
    │       └── extends → (4)'s immutability guarantee to stateful data stores
    └── Non-Reversibility Boundary
        └── Compensating Transaction Pattern (16)
            └── required-when → rollback crosses from config (immutable) into data (mutable)
```

---

## 10. Per-Pattern Pseudocode (Python-style, no comments, separated by topic)

### 10.1 GitOps Reconciliation Loop (Pull-Based Sync)

```python
def reconcile_loop(controller_state, git_source, live_cluster):
    desired_hash = git_source.get_desired_hash()
    live_hash = live_cluster.get_applied_hash()
    if desired_hash == live_hash:
        return NoOpResult(live_hash)
    manifest = git_source.fetch_compiled_manifest(desired_hash)
    live_cluster.apply(manifest)
    live_cluster.set_applied_hash(desired_hash)
    controller_state.last_reconciled_hash = desired_hash
    return SyncResult(desired_hash)


def watch_and_reconcile(controller_state, git_source, live_cluster, poll_interval):
    while True:
        reconcile_loop(controller_state, git_source, live_cluster)
        sleep(poll_interval)
```

### 10.2 Push-Based Continuous Deployment

```python
def push_deploy(pipeline_state, artifact_hash, target_cluster):
    manifest = pipeline_state.artifact_store.fetch(artifact_hash)
    target_cluster.apply(manifest)
    target_cluster.set_applied_hash(artifact_hash)
    pipeline_state.deploy_history.append(artifact_hash)
    return artifact_hash


def push_rollback(pipeline_state, target_cluster):
    if len(pipeline_state.deploy_history) < 2:
        raise NoPriorDeployment()
    previous_hash = pipeline_state.deploy_history[-2]
    return push_deploy(pipeline_state, previous_hash, target_cluster)
```

### 10.3 Content-Addressable Configuration

```python
def compile_config(source_files, template_engine, values):
    rendered = template_engine.render(source_files, values)
    content_hash = sha256(rendered.encode_bytes())
    return CompiledArtifact(hash=content_hash, manifest=rendered)


def store_artifact(artifact_registry, artifact):
    if artifact_registry.exists(artifact.hash):
        return artifact.hash
    artifact_registry.put(artifact.hash, artifact.manifest)
    return artifact.hash


def verify_reproducibility(source_files, template_engine, values, expected_hash):
    rebuilt = compile_config(source_files, template_engine, values)
    return rebuilt.hash == expected_hash
```

### 10.4 Immutable Infrastructure

```python
def deploy_immutable(fleet_state, new_artifact_hash, provisioner):
    new_instances = provisioner.create_instances(new_artifact_hash)
    fleet_state.instances_by_hash[new_artifact_hash] = new_instances
    return new_instances


def cutover_traffic(load_balancer, old_hash, new_hash, fleet_state):
    load_balancer.set_active_pool(fleet_state.instances_by_hash[new_hash])
    return new_hash


def decommission_old(fleet_state, provisioner, old_hash, grace_period):
    sleep(grace_period)
    provisioner.terminate_instances(fleet_state.instances_by_hash[old_hash])
    del fleet_state.instances_by_hash[old_hash]
```

### 10.5 Blue-Green Deployment

```python
def blue_green_deploy(bg_state, new_manifest_hash, provisioner):
    bg_state.green = provisioner.create_environment(new_manifest_hash)
    return bg_state.green


def blue_green_promote(bg_state, load_balancer):
    load_balancer.route_all_traffic(bg_state.green)
    bg_state.blue, bg_state.green = bg_state.green, bg_state.blue
    return bg_state.blue


def blue_green_rollback(bg_state, load_balancer):
    load_balancer.route_all_traffic(bg_state.blue)
    return bg_state.blue
```

### 10.6 Canary Release with Automated Analysis

```python
def start_canary(rollout_state, new_hash, initial_weight):
    rollout_state.canary_hash = new_hash
    rollout_state.canary_weight = initial_weight
    return rollout_state


def analyze_canary(metrics_client, baseline_hash, canary_hash, thresholds):
    baseline_metrics = metrics_client.query(baseline_hash)
    canary_metrics = metrics_client.query(canary_hash)
    for metric_name, max_delta in thresholds.items():
        delta = canary_metrics[metric_name] - baseline_metrics[metric_name]
        if delta > max_delta:
            return AnalysisResult(passed=False, failing_metric=metric_name)
    return AnalysisResult(passed=True, failing_metric=None)


def step_canary(rollout_state, metrics_client, thresholds, step_weight, max_weight):
    result = analyze_canary(metrics_client, rollout_state.baseline_hash, rollout_state.canary_hash, thresholds)
    if not result.passed:
        return abort_canary(rollout_state)
    rollout_state.canary_weight = min(rollout_state.canary_weight + step_weight, max_weight)
    return rollout_state


def abort_canary(rollout_state):
    rollout_state.canary_weight = 0
    rollout_state.canary_hash = None
    return rollout_state
```

### 10.7 Progressive Delivery (Staged Rollout Gates)

```python
def run_progressive_stages(rollout_state, stages, metrics_client, thresholds):
    for stage in stages:
        rollout_state.canary_weight = stage.traffic_weight
        sleep(stage.bake_time)
        result = analyze_canary(metrics_client, rollout_state.baseline_hash, rollout_state.canary_hash, thresholds)
        if not result.passed:
            return abort_canary(rollout_state)
    rollout_state.baseline_hash = rollout_state.canary_hash
    return rollout_state
```

### 10.8 Automated Rollback on Health-Check Failure

```python
def health_gated_deploy(controller_state, target_cluster, new_hash, health_checker, max_wait):
    old_hash = target_cluster.get_applied_hash()
    target_cluster.apply(controller_state.artifact_store.fetch(new_hash))
    target_cluster.set_applied_hash(new_hash)
    elapsed = 0
    while elapsed < max_wait:
        if health_checker.is_healthy(target_cluster):
            return DeployResult(success=True, active_hash=new_hash)
        sleep(health_checker.interval)
        elapsed += health_checker.interval
    target_cluster.apply(controller_state.artifact_store.fetch(old_hash))
    target_cluster.set_applied_hash(old_hash)
    return DeployResult(success=False, active_hash=old_hash)
```

### 10.9 Declarative Desired-State Management

```python
def set_desired_state(git_repo, environment, new_hash, author):
    commit = git_repo.commit_change(path=environment.desired_state_path, content=new_hash, author=author)
    return commit


def get_desired_state(git_repo, environment):
    return git_repo.read_file(environment.desired_state_path)


def diff_desired_vs_live(git_repo, environment, live_cluster):
    desired = get_desired_state(git_repo, environment)
    live = live_cluster.get_applied_hash()
    return desired != live, desired, live
```

### 10.10 Drift Detection & Auto-Heal

```python
def detect_drift(live_cluster, expected_manifest):
    live_manifest = live_cluster.get_live_manifest()
    diffs = compute_manifest_diff(expected_manifest, live_manifest)
    return diffs


def handle_drift(live_cluster, expected_manifest, mode):
    diffs = detect_drift(live_cluster, expected_manifest)
    if not diffs:
        return NoDriftResult()
    if mode == "auto_heal":
        live_cluster.apply(expected_manifest)
        return HealResult(diffs)
    if mode == "alert_only":
        alert_on_call(diffs)
        return AlertResult(diffs)
    raise UnknownDriftMode(mode)
```

### 10.11 Version-Pinned Dependency Graph (Lockfile Pattern)

```python
def resolve_lockfile(dependency_manifest, resolver):
    resolved = {}
    for name, version_range in dependency_manifest.items():
        resolved[name] = resolver.resolve_exact_version(name, version_range)
    return LockFile(entries=resolved, hash=sha256(str(resolved).encode_bytes()))


def verify_lockfile(lockfile, installed_versions):
    for name, pinned_version in lockfile.entries.items():
        if installed_versions.get(name) != pinned_version:
            return False
    return True
```

### 10.12 Feature-Flag-Gated Rollout

```python
def evaluate_flag(flag_state, user_context):
    if flag_state.kill_switch:
        return False
    if user_context.user_id in flag_state.allow_list:
        return True
    return hash_bucket(user_context.user_id) < flag_state.rollout_percentage


def rollback_flag(flag_state):
    flag_state.kill_switch = True
    flag_state.rollout_percentage = 0
    return flag_state
```

### 10.13 Snapshot/Checkpoint-Based Rollback (Stateful Stores)

```python
def create_snapshot(stateful_store, snapshot_registry, label):
    snapshot_id = stateful_store.checkpoint()
    snapshot_registry.register(label, snapshot_id)
    return snapshot_id


def rollback_to_snapshot(stateful_store, snapshot_registry, label):
    snapshot_id = snapshot_registry.lookup(label)
    stateful_store.restore(snapshot_id)
    return snapshot_id
```

### 10.14 Shadow Deployment / Dark Launch

```python
def shadow_dispatch(request, primary_service, shadow_service, comparator):
    primary_response = primary_service.handle(request)
    shadow_response = shadow_service.handle_async(request)
    comparator.record(request, primary_response, shadow_response)
    return primary_response


def evaluate_shadow_window(comparator, window_size, match_threshold):
    samples = comparator.recent_samples(window_size)
    matches = sum(1 for s in samples if s.primary_response == s.shadow_response)
    return (matches / len(samples)) >= match_threshold
```

### 10.15 Multi-Stage Promotion Pipeline

```python
def promote_through_stages(artifact_hash, stages, test_runner):
    current_stage_index = 0
    while current_stage_index < len(stages):
        stage = stages[current_stage_index]
        stage.environment.deploy(artifact_hash)
        result = test_runner.run_suite(stage.test_suite, stage.environment)
        if not result.passed:
            return PromotionResult(success=False, failed_at=stage.name, hash=artifact_hash)
        current_stage_index += 1
    return PromotionResult(success=True, failed_at=None, hash=artifact_hash)
```

### 10.16 Compensating Transaction Pattern

```python
def execute_with_compensation(action, compensation, side_effect_log):
    result = action.execute()
    side_effect_log.append(SideEffectRecord(action=action, compensation=compensation, result=result))
    return result


def rollback_side_effects(side_effect_log):
    for record in reversed(side_effect_log):
        record.compensation.execute(record.result)
    side_effect_log.clear()
```

### 10.17 Policy-as-Code Admission Gating

```python
def evaluate_policy(policy_engine, compiled_manifest, policy_bundle):
    violations = policy_engine.evaluate(compiled_manifest, policy_bundle)
    return PolicyResult(passed=len(violations) == 0, violations=violations)


def gated_sync(reconciler_state, policy_engine, policy_bundle, compiled_manifest, live_cluster):
    result = evaluate_policy(policy_engine, compiled_manifest, policy_bundle)
    if not result.passed:
        raise PolicyRejected(result.violations)
    live_cluster.apply(compiled_manifest)
    return SyncResult(success=True)
```

---

## 11. Flow of Execution (End-to-End List)

1. Developer commits config source change to Git
2. CI compiles source into an immutable manifest via `compile_config` (10.3)
3. Compiled artifact's content hash computed and stored in a registry (10.3)
4. Policy-as-code admission check runs against the compiled artifact before it's ever synced (10.17)
5. GitOps controller's reconcile loop detects new desired hash vs live hash (10.1 / 10.9)
6. Deployment mechanism applies the new hash — pull-based sync, push deploy, blue-green swap, or canary start (10.1, 10.2, 10.5, 10.6)
7. Progressive rollout stages execute with bake time and metric analysis at each step (10.7)
8. Automated integration tests / canary analysis run against the new state (10.6, 10.8)
9. **On pass**: baseline hash advances to the new hash; promotion continues through remaining pipeline stages (10.15)
10. **On fail**: controller re-declares desired hash back to last known-good — same reconcile loop runs again in reverse (10.1, 10.8)
11. If the bad deploy already produced non-reversible side effects, compensating transactions run to undo real-world effects config rollback cannot touch (10.16)
12. Drift detection continues running in the background between deploys, catching any out-of-band changes (10.10)
13. Stateful/data-layer components roll back via snapshot restore if they were affected, since they don't share the config layer's immutability (10.13)

---

## 12. References

- Weaveworks / OpenGitOps — *GitOps Principles*, opengitops.dev
- Humble, J. & Farley, D. — *Continuous Delivery*, Addison-Wesley, 2010
- Burns, B. et al. — *Kubernetes: Up and Running* (control loop / reconciliation pattern), O'Reilly
- Fowler, M. — *ImmutableServer*, martinfowler.com, 2012
- Argo Project — *Argo Rollouts: Progressive Delivery Controller*, argoproj.github.io
- Chacon, S. & Straub, B. — *Pro Git* (content-addressable object model), 2014
- Open Policy Agent — *Policy-as-Code for Kubernetes Admission Control*, openpolicyagent.org
- Newman, S. — *Building Microservices* (Ch. on deployment strategies: blue-green, canary), O'Reilly, 2021
- Google SRE Workbook — *Canarying Releases*, sre.google

---

*Stateful GitOps Rollback works by eliminating the "undo" code path entirely — rollback is just another forward reconciliation to a different, already-known-good, content-addressed value. Its entire safety model rests on one assumption that must be actively defended: that "config" stays immutable and hash-pure while "data" does not — and the moment a deploy's effects cross that line, this pattern needs a compensating-transaction partner, not a rollback.*