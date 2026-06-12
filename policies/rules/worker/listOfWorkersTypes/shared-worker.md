Shared Worker Contracts Tree
When a workflow, job, or schedule must be triggered by another package, its interface is published here. Internal-only workers that are never triggered externally do not publish to shared/.

shared/
├── workflows/                       ← public Temporal workflow interfaces
│   └── {workflow-name}/
│       ├── v1.yaml                  ← WorkflowInput, WorkflowOutput, signals, queries
│       └── changelog.md
│
├── jobs/                            ← public queue job payload schemas
│   └── {job-name}/
│       ├── v1.yaml
│       └── changelog.md
│
├── schedules/                       ← public cron schedule definitions
│   └── {schedule-name}/
│       └── v1.yaml
│
└── worker-registry.yaml             ← all workers, task queues, types, owners

