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

## 2. Agent Communication Protocol (ACP) & Other Agentic Standards

If a service needs to support ACP (Agent Communication Protocol) or other agentic protocols (e.g., Agent Protocol, LangChain Remote Runnables, AutoGen Message Protocol), the same boundary isolation applies.

### Directory Placement
```
packages/python/{package-name}/
├── src/
│   ├── api/
│   │   ├── rest/v1/
│   │   ├── mcp/
│   │   └── acp/                       # ACP Adapter Layer
│   │       ├── router.py              # Listens for and dispatches ACP envelopes
│   │       ├── envelope.py            # Standard ACP envelope model & validation
│   │       └── performatives.py       # Handlers mapped by communicative act type
```

### Strict ACP Envelope Structure
Every incoming or outgoing ACP message must strictly adhere to the following schema contract:

```json
{
  "id": "uuid4-string",
  "conversation_id": "uuid4-string",
  "sender": "agent-uri-identifier",
  "receiver": "agent-uri-identifier",
  "performative": "REQUEST | INFORM | PROPOSE | ACCEPT_PROPOSAL | REJECT_PROPOSAL | FAILURE",
  "content": {
    "response_text": "...",
    "parameters": {}
  },
  "ontology": "urn:llm-observability:perplexity:v1",
  "protocol": "request-response",
  "timestamp": "ISO-8601-UTC-datetime",
  "metadata": {
    "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
  }
}
```

### ACP Compliance & Execution Rules
1. **Communicative Performative Mapping:**
   - **`REQUEST`**: Triggers core feature/service scoring execution.
   - **`INFORM`**: Used to send back success payloads or telemetry updates.
   - **`FAILURE`**: Used to return standardized error codes and skip signals.
2. **Conversational Threading:** The adapter must validate that the `conversation_id` is present. If it belongs to a multi-turn conversation, it must check the local session repository for matching execution context.
3. **Trace Context Propagation:** The `metadata.traceparent` field must be parsed to extract the W3C trace context, which must then be registered as the active OpenTelemetry span context before invoking the feature service.
4. **Stateless Operations:** ACP adapters must remain stateless; any session persistence or caching must be offloaded to the core features infra layer via interfaces.

---

## 3. Other Agent Orchestration Frameworks
For integration with client frameworks (e.g., LangChain Remote Runnables):
1. **Streaming Execution Spans:** For long-running agent actions, use Server-Sent Events (SSE) or WebSockets to stream intermediate tool calls, reasoning steps, and partial outputs.
2. **Standard Serialization:** Force JSON-safe input/output mapping at the boundary. No python-specific pickling or model objects should leak outside the adapter.


## 3. Distribution & Deployment

- **Single Artifact Principle:** A package must build into a single Docker image containing all entrypoint adapters.
- **Environment Flag Selection:** Use entrypoint script args or environment variables to switch between modes (e.g., `uvicorn api.rest.v1.app:app` vs. `python -m api.mcp.server`).
