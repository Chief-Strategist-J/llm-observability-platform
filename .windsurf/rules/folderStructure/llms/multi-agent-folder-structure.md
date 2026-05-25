Multi-Agent System — Folder Structure

multi-agent-{domain}/
├── contracts/v1.yaml
├── src/
│   ├── api/rest/v1/handler
│   │
│   ├── features/
│   │   ├── supervisor/
│   │   │   ├── index
│   │   │   ├── router           ← decides which agent handles the task
│   │   │   ├── aggregator       ← merges worker results
│   │   │   └── types
│   │   │
│   │   └── workers/
│   │       ├── {agent-a}/
│   │       │   ├── index
│   │       │   ├── loop
│   │       │   ├── tools/
│   │       │   ├── memory/
│   │       │   └── types
│   │       └── {agent-b}/
│   │
│   ├── messaging/
│   │   ├── bus                  ← routes messages between agents
│   │   ├── types                ← AgentMessage, TaskAssignment, Result
│   │   └── protocols/           ← message schemas per agent pair
│   │
│   └── shared-memory/
│       ├── workspace            ← shared scratchpad
│       └── knowledge-base       ← shared facts and context
│
├── prompts/
│   ├── supervisor/
│   └── workers/{agent-name}/
├── evaluation/
└── scripts/

