Agentic AI — Single Agent — Folder Structure

agent-{domain}/
├── contracts/v1.yaml
├── src/
│   ├── api/rest/v1/handler
│   │
│   ├── features/agent/
│   │   ├── index
│   │   ├── loop                 ← think → act → observe (ReAct / CoT)
│   │   ├── planner              ← decomposes task into steps
│   │   ├── executor             ← calls selected tool, captures observation
│   │   ├── memory/
│   │   │   ├── short-term       ← conversation, scratchpad
│   │   │   └── long-term        ← persistent facts, episodic memory
│   │   ├── types                ← Task, Step, Observation, AgentState
│   │   └── tests/
│   │
│   ├── tools/
│   │   ├── registry             ← lists all tools with name, description, schema
│   │   ├── {tool-name}/
│   │   │   ├── index            ← exports: name, description, inputSchema, execute
│   │   │   ├── tool
│   │   │   ├── types            ← ToolInput, ToolOutput
│   │   │   └── tests/
│   │   └── ...
│   │
│   ├── infra/adapters/{llm-vendor}/
│   └── shared/ports/
│       ├── llm.port
│       └── memory.port
│
├── prompts/
│   ├── system-v1.txt
│   ├── tool-selection-v1.txt
│   └── changelog.md
│
├── evaluation/
│   ├── datasets/                ← task → expected tool calls → expected result
│   ├── metrics/                 ← task success rate, tool accuracy, step count
│   └── reports/
├── scripts/
└── .env.example

