Fine-Tuning Pipeline — Folder Structure

fine-tuning-{model}-{domain}/
│
├── data/
│   ├── raw/
│   ├── processed/
│   │   ├── train/
│   │   ├── validation/
│   │   └── test/
│   └── schema.yaml
│
├── datasets/
│   ├── builder              ← raw → transforms → processed
│   ├── validator            ← validates against schema
│   ├── formatter/
│   │   ├── instruction-format
│   │   ├── completion-format
│   │   └── types            ← DatasetRow, FormattedExample
│   └── augmentor
│
├── training/
│   ├── config/
│   │   ├── base.yaml        ← base model, tokenizer, format
│   │   ├── lora.yaml        ← rank, alpha, dropout, target modules
│   │   ├── qlora.yaml       ← quantisation config
│   │   └── hyperparams.yaml ← lr, batch size, epochs, warmup
│   ├── trainer
│   ├── callbacks/           ← checkpoint, early-stop, logging
│   └── types                ← TrainingConfig, TrainingResult
│
├── adapters/
│   └── {run-id}/
│       ├── adapter_config.json
│       ├── adapter_model.bin
│       └── training_args.bin
│
├── evaluation/
│   ├── datasets/
│   ├── metrics/
│   │   ├── perplexity
│   │   ├── task-accuracy
│   │   └── human-eval-schema.yaml
│   ├── runner
│   └── reports/{run-id}/
│       ├── metrics.json
│       └── examples.jsonl
│
├── experiments/
│   └── {YYYY-MM-DD}-{hypothesis}/
│       ├── hypothesis.md
│       ├── config-diff.yaml
│       └── findings.md
│
├── model-registry/
│   └── registry.yaml
│
└── scripts/
    ├── prepare-data.sh
    ├── train.sh
    ├── evaluate.sh
    └── push-adapter.sh

