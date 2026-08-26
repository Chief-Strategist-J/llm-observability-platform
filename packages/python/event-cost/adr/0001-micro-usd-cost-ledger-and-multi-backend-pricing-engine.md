# ADR 0001: Micro-USD Cost Ledger and Multi-Backend Pricing Engine

| Field | Value |
| --- | --- |
| **ADR ID** | `ADR-PYTHON-EVENT-COST-0001` |
| **Title** | Micro-USD Cost Ledger and Multi-Backend Pricing Engine |
| **Status** | **Accepted** |
| **Date** | 2026-08-25 |
| **Scope** | Core Cost Engine (`event-cost`), Pricing Registry (`model_price_versions.yaml`), Storage Backends (`SQLiteBackend`, `RedisBackend`) |

---

## 1. Context & Problem Statement

LLM observability platforms require precise, deterministic cost tracking across various providers (OpenAI, Anthropic, Google, Meta). Floating-point math introduces rounding errors over millions of transactions. Furthermore, client applications range from local zero-infrastructure CLI scripts (requiring SQLite) to distributed Kafka-scale microservices (requiring Redis).

`event-cost` addresses these challenges by:
1. Standardizing all cost calculations in **micro-USD** ($1\text{ USD} = 1,000,000\text{ micro-USD}$) using integer math.
2. Abstracting storage backends behind a unified `CostLedger` interface supporting zero-config SQLite and scalable Redis.
3. Maintaining a central model price version registry (`model_price_versions.yaml`).
4. Serving as the single consolidated Python package (`event-cost`) containing both client ledger facades (`event_cost.ledger`) and high-throughput Kafka ingestion workers (`event_cost.worker`).

---

## 2. High-Level Design (HLD)

### 2.1 High-Level Architecture Topology

```mermaid
flowchart TD
    subgraph ClientApp["1. Application & SDK Integration"]
        SDK["instrumentation-sdk / Direct Python App"]
        TokenStats["Token Counts (prompt_tokens, completion_tokens)"]
        SDK --> TokenStats
    end

    subgraph CostEngine["2. Event Cost Core Ledger Engine"]
        CostLedgerFacade["CostLedger Facade"]
        PricingRegistry["Model Price Registry (model_price_versions.yaml)"]
        MicroUsdCalc["Integer Micro-USD Math Engine"]

        TokenStats --> CostLedgerFacade
        CostLedgerFacade --> PricingRegistry
        PricingRegistry --> MicroUsdCalc
    end

    subgraph BackendAdapters["3. Pluggable Storage Backends"]
        BackendInterface["Backend Abstract Base Class"]
        SqliteBackend["SQLiteBackend (~/.event-cost/ledger.db)\n(Time-windowed local queries)"]
        RedisBackend["RedisBackend (redis://...)\n(High-throughput cumulative counters)"]

        MicroUsdCalc --> BackendInterface
        BackendInterface --> SqliteBackend
        BackendInterface --> RedisBackend
    end
```

### 2.2 Three-Plane Architectural Blueprint (Control, Data & Messaging)

```mermaid
flowchart TD
    subgraph ControlPlane["1. CONTROL PLANE (Price Governance & Config)"]
        YamlPrices["model_price_versions.yaml Registry"]
        VersionLookup["Model Price Versioning"]
        WindowConfig["Time Window Parameters (1h, 24h, 7d, 30d)"]
    end

    subgraph DataPlane["2. DATA PLANE (Micro-USD Calculation & Ledger Storage)"]
        LedgerFacade["CostLedger.record(span_input)"]
        IntegerCalc["Micro-USD Integer Cost Calculation"]
        SQLiteDriver["SQLite WAL Local Ledger Driver"]
        RedisDriver["Redis HINCRBY Counter Driver"]

        LedgerFacade --> IntegerCalc
        IntegerCalc --> SQLiteDriver
        IntegerCalc --> RedisDriver
    end

    subgraph MessagingPlane["3. MESSAGING PLANE (Event Emission & Metric Sync)"]
        WorkerBridge["event_cost.worker Interface"]
        PrometheusExport["Prometheus Cost Metrics (cost_engine_spans_processed_total)"]

        RedisDriver --> WorkerBridge
        SQLiteDriver --> PrometheusExport
    end

    ControlPlane --> DataPlane
    DataPlane --> MessagingPlane
```

---

## 3. Low-Level Design (LLD)

### 3.1 Sequence Diagram: Cost Calculation & Ledger Record Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor App as Client Application / Worker
    participant Ledger as CostLedger Facade
    participant Prices as Price Registry
    participant Backend as Storage Backend (SQLite / Redis)

    App->>Ledger: record(model="gpt-4o", provider="openai", prompt_tokens=150, completion_tokens=200, org_id="org-1")
    activate Ledger
    
    Ledger->>Prices: get_model_price("gpt-4o", "openai")
    activate Prices
    Prices-->>Ledger: PriceEntry(input_price_per_token_micro=5, output_price_per_token_micro=15)
    deactivate Prices

    Ledger->>Ledger: calculate_cost_micro_usd(150, 200, 5, 15)
    Note over Ledger: (150 * 5 + 200 * 15) = 3750 micro-USD

    Ledger->>Backend: record(SpanInput(cost_usd_micro=3750, org_id="org-1"...))
    activate Backend
    alt SQLite Backend
        Backend->>Backend: INSERT INTO spans (...) VALUES (...)
    else Redis Backend
        Backend->>Backend: Redis Fenwick + Token Bucket Pipeline Update
    end
    Backend-->>Ledger: Success OK
    deactivate Backend

    Ledger-->>App: returns cost_usd_micro = 3750 ($0.003750 USD)
    deactivate Ledger
```

### 3.2 Key Function Contracts (`src/event_cost/ledger.py`)

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class SpanInput:
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    org_id: str = ""
    project_id: str = ""
    service_name: str = ""
    user_id: str = ""
    estimated_tokens: int = 0
    cost_usd_micro: Optional[int] = None

class CostLedger:
    def __init__(self, backend: Optional[Backend] = None, price_config_path: Optional[str] = None):
        self._backend = backend or SQLiteBackend()
        self._prices = _load_prices(price_config_path)

    def record(self, **kwargs) -> None:
        span = SpanInput(**kwargs)
        ...

    def total_cost_usd(self, org_id: str, window: str = "24h", ...) -> float:
        micro = self._backend.query_total(org_id=org_id, window=window, ...)
        return micro / 1_000_000.0
```

---

## 4. End-to-End Call Stack Topology

```text
└── [Client Application] ledger.record(model="gpt-4o", prompt_tokens=150, completion_tokens=200)
    ├── 1. event_cost/ledger.py :: CostLedger.record(**kwargs)
    │   ├── 2. event_cost/ledger.py :: _load_prices()
    │   │   └── Read rates from model_price_versions.yaml
    │   ├── 3. event_cost/ledger.py :: _compute_cost(span, prices)
    │   │   └── Integer math: returns cost_usd_micro = 3750 ($0.003750 USD)
    │   └── 4. Build `SpanInput` dataclass record
    │
    ├── 5. [SQLite Mode] event_cost/backends/sqlite.py :: SQLiteBackend.record(span, cost)
    │   ├── 6. sqlite3.connect("~/.event-cost/ledger.db")
    │   └── 7. INSERT INTO spans (model, provider, prompt_tokens, cost_usd_micro...)
    │
    └── 8. [Redis Mode] event_cost/backends/redis.py :: RedisBackend.record(span, cost)
        ├── 9. Pipeline Fenwick tree updates across dimensions (org, project, service, model, user)
        └── 10. Deduct overshoot from token bucket
```

---

## 5. Decision Rationale & Consequences

### Positive Consequences
- **Zero Floating-Point Drift**: Micro-USD integer math ensures exact financial auditability across millions of span records.
- **Zero Infrastructure Footprint**: Out-of-the-box SQLite backend works locally without requiring Redis or PostgreSQL servers.
- **Plug-and-Play Scaling**: Single-line configuration change (`CostLedger(backend=RedisBackend(...))`) upgrades local code to enterprise cluster scale.
- **Single Monorepo Package**: Client ledger and Kafka worker live under `event_cost`, eliminating package fragmentation.
