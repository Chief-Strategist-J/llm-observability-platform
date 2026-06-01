# Agent-to-Agent and Model Context Protocol (MCP) Integration Rules

## Core Architectural Principle
All Agent-to-Agent and MCP interfaces are **External Adapters** (Driving Adapters in Hexagonal Architecture). They exist strictly at the boundary of a package. They must never contain business or domain logic. They must map incoming protocol-specific requests directly to the package's core features/services.

---

## 1. Model Context Protocol (MCP) Standards

### Directory Structure & Placement
When adding MCP support to an existing package, it must reside in an isolated `api/mcp/` directory:

```
packages/python/{package-name}/
├── src/
│   ├── api/
│   │   ├── rest/v1/                   # REST Adapter (REST/HTTP Entrypoint)
│   │   └── mcp/                       # MCP Adapter (Agent/Tool Entrypoint)
│   │       ├── server.py              # Launch/Transport wrapper (Stdio/SSE)
│   │       ├── router.py              # Routes MCP Tools/Resources to features
│   │       └── tools.py               # Defines tool signature and schema maps
│   └── features/                      # Pure Business/Domain Logic (untouched)
```

### Transport Options
1. **Stdio (Command Line Execution):** Default for developer environments and local agents (e.g., Cursor, Claude Desktop). Standard Input/Output must only be used for JSON-RPC messages. Standard Error (`sys.stderr`) must be used for all logs.
2. **SSE (Server-Sent Events):** Default for production/multi-tenant web environments. Exposed as HTTP POST endpoints for sending client messages and an SSE stream for receiving server-to-client events.

### MCP Interface Rules
- **Contract-First Tool Mapping:** Define MCP tools under `contracts/mcp/tools.json` or inline via tool registry schemas before implementing.
- **Payload Limits:** Truncate or paginate responses exceeding 1MB to prevent client buffer overflows.
- **Zero Raw Exceptions:** Handlers in `api/mcp/` must catch all exceptions from the feature service layer and map them to the standard MCP error codes (e.g., `-32603` for Internal Error, `-32602` for Invalid Params).

---

## 2. Other Agent-to-Agent Protocols

If a service needs to support other standard agentic orchestration protocols (e.g., LangChain Remote Runnables, AutoGen Message Protocols, or Agent Protocol), the same boundary isolation applies.

### Directory Placement
```
packages/python/{package-name}/
├── src/
│   ├── api/
│   │   ├── rest/v1/
│   │   ├── mcp/
│   │   └── agent_protocol/            # Agent Protocol / LangChain API Adapter
│   │       ├── router.py
│   │       └── handlers.py
```

### Compliance Checklist for Agent Protocols
1. **Stateless Operations:** Agent APIs should be stateless, or delegate session states to the core feature services/repositories (which in turn rely on Redis/Postgres adapters).
2. **Streaming Execution Spans:** For long-running agent actions, use Server-Sent Events (SSE) or WebSockets to stream intermediate tool calls, reasoning steps, and partial outputs.
3. **Trace Propagation:** Ensure that headers (like OpenTelemetry traceparent) are captured from incoming messages (e.g., in `agent_protocol` metadata) and injected into the current execution context so the entire multi-agent trace chain is unified.

---

## 3. Distribution & Deployment

- **Single Artifact Principle:** A package must build into a single Docker image containing all entrypoint adapters.
- **Environment Flag Selection:** Use entrypoint script args or environment variables to switch between modes (e.g., `uvicorn api.rest.v1.app:app` vs. `python -m api.mcp.server`).
