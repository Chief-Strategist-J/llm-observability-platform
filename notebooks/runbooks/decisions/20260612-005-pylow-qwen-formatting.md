ADR-005: Use LoRA Fine-Tuned Qwen2.5-0.5B for pylow Formatting Engine
Status: Proposed
Date: 2026-06-12
Deciders: System

── PROBLEM ──────────────────────────────────────────────────────────────────
How do we train a structured log-to-ASCII layout formatting engine without exceeding 1GB of memory on consumer CPU hardware, and how do we ensure the mathematical foundation of the training prevents catastrophic forgetting?

── FAILURE MODES WE ARE SOLVING ─────────────────────────────────────────────
FM-CURRENT-1: Full fine-tuning OOMs
  Symptom: CPU runs out of memory and crashes during gradient update.
  Root cause: Optimizer states for 500M parameters require >6GB RAM.
  Frequency: Every training run without quantization/adapters.
  Severity: CRITICAL — prevents local model iteration.

FM-CURRENT-2: Catastrophic forgetting
  Symptom: Model learns to format ASCII but forgets basic Python code context.
  Root cause: Over-writing base model weights W0 directly.
  Frequency: Common in causal language model SFT.
  Severity: HIGH — reduces debugging utility.

── DECISION DRIVERS ─────────────────────────────────────────────────────────
D1: Training memory footprint must stay strictly < 1GB.
D2: Base model knowledge (Python debugging) must be preserved mathematically.
D3: Training must converge on instruction-following formatting.

── OPTIONS CONSIDERED ───────────────────────────────────────────────────────
Option A: Full Fine-Tuning (SFTTrainer)
  Solves: D3
  Creates: FM-CURRENT-1, FM-CURRENT-2
  Eliminated because: Full updates of W0 mathematically guarantee OOMs on 1GB constraint.

Option B: LoRA (Low-Rank Adaptation)
  Solves: FM-CURRENT-1, FM-CURRENT-2, D1, D2, D3
  Creates: FM-NEW-1 (Adapter rank bottleneck)
  Chosen because: Freezing W0 and only training B*A (where r=8) ensures we only maintain optimizer states for a fraction of a megabyte, satisfying D1 while preserving D2.

── DECISION ─────────────────────────────────────────────────────────────────
Chosen: Option B (LoRA)
Because: D1 + D2 + D3 are satisfied by the W = W0 + BA mathematical definition.
Not Option A because: Full Fine-Tuning mathematically guarantees FM-CURRENT-1.

── FAILURE MODES CREATED ────────────────────────────────────────────────────
FM-NEW-1: Adapter rank bottleneck
  Symptom: Model fails to converge on complex layout mappings.
  Detection: Cross-entropy loss plateau > 2.0 during training.
  Threshold: Alert if validation loss > 2.0.
  Recovery: Increase rank r to 16, re-train.
  Prevention: Monitor loss curves and scale alpha proportionately.

── CONSEQUENCES ─────────────────────────────────────────────────────────────
Positive: Memory bounds strict, model trains safely without catastrophic forgetting.
Negative: Inference requires merging the adapter weights dynamically.

── REVIEW TRIGGER ───────────────────────────────────────────────────────────
Review if: The validation loss plateaus > 2.0 or if memory spikes beyond 950MB during adapter merge.
