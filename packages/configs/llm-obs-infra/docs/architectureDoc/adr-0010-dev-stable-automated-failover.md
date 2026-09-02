# ADR-0010: Active-Passive Zero-Downtime Failover & Fallback Architecture (Dev vs. Stable)

| Field | Value |
|---|---|
| **Document ID** | ADR-0010 |
| **Status** | Accepted |
| **Author(s)** | Distributed Systems Architect & Lead DevOps Engineer |
| **Target Package** | [`packages/configs/llm-obs-infra`](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/llm-obs-infra) |
| **Date** | 2026-09-02 |
| **Version** | 4.0.0 (Production-Grade Ultra-Deep Masterclass & Flawless Diagrams) |

---

## 1. Executive Summary & Problem Context

### 1.1 The "Dev-QA Clash" Problem
In modern distributed software teams, developers build new features or optimize existing backend microservices on experimental development branches (e.g. `v2-dev`). At the same time, QA testers, frontend developers, and integration test suites interact with the shared development environment to test their own features.

During active feature development:
1. **Uncaught Panics & Syntax Errors**: The developer makes an experimental code edit or breaks a runtime route in `v2-dev`.
2. **Instant Team Blockade**: The service crashes or starts returning `502 Bad Gateway` or `503 Service Unavailable`.
3. **Loss of Team Velocity**: QA testers and frontend developers cannot continue their work. They must message the developer ("Is the dev server down?"), wait for a fix, or ask them to revert code.
4. **Context Switching**: The developer must pause feature work to restore the environment for the team.

### 1.2 Architectural Goal
Establish an **Automated Active-Passive Failover & Fallback Architecture** using **Traefik v3**:
* **Normal Operation**: 100% of live traffic is routed to the new feature service (`v2-dev`).
* **During a Crash/Failure**: Traefik detects `v2-dev` is dead within **< 3 seconds** and seamlessly switches 100% of traffic to a pre-built **Stable Service (`v1-stable`)**.
* **Zero QA Downtime**: Testers never see a `502 Bad Gateway` error. They interact with the stable API version until the developer fixes `v2-dev`.

---

## 2. Comprehensive Visual Architecture Diagrams

### 2.1 Complete End-to-End System Topology (Mermaid Graph)

```mermaid
graph TD
    subgraph Client_Layer ["Client and Testing Layer"]
        QA_User["QA Engineer / Frontend App"]
        API_Tester["Automated Integration Test Runner"]
    end

    subgraph Ingress_Layer ["Traefik v3 Ingress Gateway - Port 80"]
        Entrypoint["Web Entrypoint - Port 80"]
        
        subgraph Router_Engine ["Traefik Routing and Priority Engine"]
            Router_Dev["Dev Router - Priority 100"]
            Router_Stable["Backup Router - Priority 1"]
        end
        
        subgraph Health_Engine ["Active Health Prober Engine"]
            Prober["HTTP Health Prober - Interval 3s, Timeout 1s"]
        end

        LB_Dev["Dev LoadBalancer Pool"]
        LB_Stable["Backup LoadBalancer Pool"]
    end

    subgraph Container_Layer ["Local Docker Engine Data Plane"]
        subgraph Dev_Container ["my-service-dev - Primary"]
            Dev_App["v2-dev App Code"]
            Dev_Health["GET /health Handler"]
        end

        subgraph Stable_Container ["my-service-stable - Backup"]
            Stable_App["v1-stable App Code"]
            Stable_Health["GET /health Handler"]
        end

        Database[("AlloyDB / ClickHouse DB")]
    end

    subgraph CI_CD_Layer ["Remote CI/CD and Image Registry"]
        GH_Actions["GitHub Actions Workflow"]
        GHCR["GitHub Container Registry"]
    end

    QA_User --> Entrypoint
    API_Tester --> Entrypoint
    Entrypoint --> Router_Dev
    Entrypoint --> Router_Stable

    Router_Dev -->|"Healthy - Priority 100"| LB_Dev
    Router_Stable -->|"Fallback - Priority 1"| LB_Stable

    LB_Dev -->|"Port 8082"| Dev_App
    LB_Stable -->|"Port 8081"| Stable_App

    Dev_App --> Database
    Stable_App --> Database

    Prober -.->|"Active Poll /health every 3s"| Dev_Health
    Prober -.->|"Active Poll /health every 3s"| Stable_Health

    GH_Actions -->|"Build and Push main-latest"| GHCR
    GHCR -.->|"docker pull - Layers Shared"| Stable_Container
```

---

### 2.2 Traefik Health State Machine Transition Diagram

```mermaid
stateDiagram-v2
    [*] --> STATE_HEALTHY : Service Container Startup

    state STATE_HEALTHY {
        [*] --> Priority_100_Active
        Priority_100_Active : Traffic routed to v2-dev
        Priority_100_Active : Response HTTP 200 OK
    }

    STATE_HEALTHY --> STATE_SUSPECT : Probe 1 Failed - Timeout or 500

    state STATE_SUSPECT {
        [*] --> First_Failure_Logged
        First_Failure_Logged : Traefik logs 1st failure
        First_Failure_Logged : Retries v2-dev probe
    }

    STATE_SUSPECT --> STATE_HEALTHY : Next Probe Returns 200 OK
    STATE_SUSPECT --> STATE_UNHEALTHY : Probe 2 Failed - Consecutive Failure

    state STATE_UNHEALTHY {
        [*] --> Priority_1_Fallback_Active
        Priority_1_Fallback_Active : Traefik evicts v2-dev from Active Pool
        Priority_1_Fallback_Active : 100 Percent Traffic routed to v1-stable
        Priority_1_Fallback_Active : QA Team Unblocked - Zero 502 Errors
    }

    STATE_UNHEALTHY --> STATE_RECOVERY : Prober detects GET /health returns 200 OK

    state STATE_RECOVERY {
        [*] --> Warmup_Validation
        Warmup_Validation : Developer fixed local dev code
    }

    STATE_RECOVERY --> STATE_HEALTHY : 2 Consecutive 200 OK Probes
    STATE_RECOVERY --> STATE_UNHEALTHY : Probe fails during recovery
```

---

### 2.3 Comprehensive Crash and Recovery Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Client as QA Tester / Frontend
    participant Traefik as Traefik Ingress Gateway
    participant Dev as my-service-dev (Priority 100)
    participant Stable as my-service-stable (Priority 1)
    participant Registry as GHCR Registry

    Note over Traefik, Stable: Initialization Phase
    Traefik->>Registry: Pull ghcr.io/org/service:main-latest (Layers Cached)
    Registry-->>Traefik: Image Layers Ready (Under 10MB Diff)
    Traefik->>Stable: Start v1-stable Container (:8081)
    Traefik->>Dev: Start v2-dev Container (:8082)

    Note over Traefik, Dev: Phase 1: Healthy Operation
    loop Every 3 Seconds
        Traefik->>Dev: GET /health
        Dev-->>Traefik: 200 OK status HEALTHY
    end
    Client->>Traefik: GET /api/v1/analytics/metrics
    Traefik->>Dev: Proxy Request (Priority 100)
    Dev-->>Client: 200 OK (v2-dev Response)

    Note over Dev: Phase 2: Runtime Crash or Panic in v2-dev
    Dev->>Dev: Unhandled Null Pointer Exception or Process Panic

    Note over Traefik, Dev: Phase 3: Active Health Detection (Under 3 Seconds)
    Traefik->>Dev: GET /health
    Dev-->>Traefik: Connection Refused or Timeout
    Note over Traefik: Failure 1 logged (State -> SUSPECT)
    Traefik->>Dev: GET /health (Retry Probe)
    Dev-->>Traefik: Connection Refused
    Note over Traefik: Failure 2 logged (State -> UNHEALTHY)<br/>Evict Priority 100 Router

    Note over Traefik, Stable: Phase 4: Transparent Fallback to Stable
    Client->>Traefik: GET /api/v1/analytics/metrics
    Traefik->>Stable: Proxy Request (Priority 1 Backup Active)
    Stable-->>Client: 200 OK (v1-stable Fallback Response)
    Note over Client: QA receives 200 OK! Zero downtime!

    Note over Dev: Phase 5: Developer Fixes Code & Restarts Container
    Dev->>Dev: Code Fix Hot-Reloaded or Container Restarts
    Traefik->>Dev: GET /health
    Dev-->>Traefik: 200 OK status HEALTHY
    Note over Traefik: Restore Priority 100 Router

    Client->>Traefik: GET /api/v1/analytics/metrics
    Traefik->>Dev: Proxy Request (Back to Priority 100)
    Dev-->>Client: 200 OK (v2-dev Response)
```

---

### 2.4 Docker Storage Layer Deduplication Architecture

```mermaid
graph LR
    subgraph Disk_Storage ["Host System Hard Drive Storage"]
        subgraph Shared_Layers ["Shared Docker Layers - Stored ONCE"]
            L1["Layer 1: Base OS - 30MB"]
            L2["Layer 2: Go / Node Runtime - 80MB"]
            L3["Layer 3: Installed Packages - 100MB"]
        end

        subgraph Diff_Layers ["Unique Application Diff Layers"]
            L4_Dev["Layer 4a: v2-dev Code - 5MB"]
            L4_Stable["Layer 4b: v1-stable Code - 5MB"]
        end
    end

    subgraph Running_Containers ["Active Container Execution Space"]
        C_Dev["my-service-dev Container<br/>Reads L1 + L2 + L3 + L4a"]
        C_Stable["my-service-stable Container<br/>Reads L1 + L2 + L3 + L4b"]
    end

    L1 --> C_Dev
    L2 --> C_Dev
    L3 --> C_Dev
    L4_Dev --> C_Dev

    L1 --> C_Stable
    L2 --> C_Stable
    L3 --> C_Stable
    L4_Stable --> C_Stable
```

---

### 2.5 Database Schema Compatibility (Expand-Contract Pattern)

```mermaid
flowchart TD
    Step1["Step 1: EXPAND - Backward Compatible<br/>ADD new columns as NULLABLE or with DEFAULT values.<br/>v1-stable reads old columns.<br/>v2-dev writes both old and new columns."]
    
    Step2["Step 2: ACTIVE-PASSIVE DEPLOYMENT<br/>Both v1-stable and v2-dev run concurrently against DB.<br/>If v2-dev crashes, v1-stable still operates seamlessly."]
    
    Step3["Step 3: CONTRACT - Clean up Legacy<br/>After v2-dev is merged to main and fully validated,<br/>drop deprecated columns in follow-up migration."]

    Step1 --> Step2 --> Step3
```

---

## 3. Deep-Dive Concepts for Beginners

### 3.1 Reverse Proxy & Priority-Based Traffic Routing
A **Reverse Proxy** (like Traefik, NGINX, or Envoy) sits in front of backend microservices. Instead of clients hitting microservices directly on random ports, all requests hit Traefik on port `80` or `443`.

Traefik uses **Routers** and **Priority Rules**:
* **Priority**: When multiple services match the same URL route (e.g., `/api/v1/analytics`), Traefik routes traffic to the service with the **highest priority number**.
* `v2-dev` is configured with `Priority = 100` (Primary).
* `v1-stable` is configured with `Priority = 1` (Backup).

As long as `v2-dev` is healthy, it handles all traffic. If `v2-dev` fails its health check, Traefik temporarily disables its router, automatically falling back to the `Priority = 1` router (`v1-stable`).

---

### 3.2 Active Health Checks & Probing
Traefik continuously sends an HTTP GET request to the microservice's `/health` endpoint every `3 seconds`.

* **Healthy State**: `/health` returns `HTTP 200 OK`. Traefik keeps `v2-dev` in the priority route.
* **Unhealthy State**: If `v2-dev` returns `500 Internal Server Error`, times out (>1s), or connection is refused (process died), Traefik counts a failure.
* **Eviction Threshold**: After **2 consecutive failures** (~3-6 seconds), Traefik marks `v2-dev` as `UNHEALTHY` and shifts traffic to `v1-stable`.
* **Automatic Recovery**: Once the developer fixes the bug and `v2-dev` starts returning `HTTP 200 OK` again, Traefik automatically restores `v2-dev` as the primary target.

---

### 3.3 How Docker Layer Sharing & Image Caching Works
A common beginner concern is: *"Won't running two Docker images take up double the hard drive space?"*

**No, because Docker images are built in layers.**

When Docker builds an image, it stacks layers:
1. Base Operating System (`alpine:3.19` or `ubuntu:22.04`) ~ 30MB
2. Programming Language Runtime (`golang:1.22` or `node:20`) ~ 80MB
3. System Dependencies & npm/go packages ~ 100MB
4. Application Source Code ~ 5MB

Because `v1-stable` and `v2-dev` share the exact same base OS, runtime, and package dependencies, **Docker stores Layers 1–3 only once on host disk**. 

Downloading and running the stable container consumes **less than 10MB of extra disk space**!

---

## 4. Production-Grade Configuration Blueprints

### 4.1 Complete `docker-compose.failover.yml` Blueprint

```yaml
version: "3.8"

networks:
  llmobs-net:
    driver: bridge

services:
  # ───────────────────────────────────────────────────────────────────────────
  # 1. TRAEFIK INGRESS GATEWAY (Port 80)
  # ───────────────────────────────────────────────────────────────────────────
  traefik:
    image: traefik:v3.0
    container_name: llmobs-ingress-gateway
    restart: unless-stopped
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--log.level=INFO"
    ports:
      - "80:80"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
    networks:
      - llmobs-net

  # ───────────────────────────────────────────────────────────────────────────
  # 2. PRIMARY DEVELOPMENT SERVICE (v2-dev)
  # ───────────────────────────────────────────────────────────────────────────
  analytics-engine-dev:
    build:
      context: ./packages/services/analytics-engine
      dockerfile: Dockerfile
    container_name: analytics-engine-dev
    restart: always
    environment:
      - PORT=8082
      - NODE_ENV=development
    networks:
      - llmobs-net
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.analytics-dev.rule=PathPrefix(`/api/v1/analytics`)"
      - "traefik.http.routers.analytics-dev.priority=100"
      - "traefik.http.routers.analytics-dev.service=analytics-dev-service"
      - "traefik.http.services.analytics-dev-service.loadbalancer.server.port=8082"
      - "traefik.http.services.analytics-dev-service.loadbalancer.healthcheck.path=/health"
      - "traefik.http.services.analytics-dev-service.loadbalancer.healthcheck.interval=3s"
      - "traefik.http.services.analytics-dev-service.loadbalancer.healthcheck.timeout=1s"

  # ───────────────────────────────────────────────────────────────────────────
  # 3. FALLBACK STABLE SERVICE (v1-stable from main branch)
  # ───────────────────────────────────────────────────────────────────────────
  analytics-engine-stable:
    image: ghcr.io/llm-obs/analytics-engine:main-latest
    container_name: analytics-engine-stable
    restart: always
    environment:
      - PORT=8081
      - NODE_ENV=production
    networks:
      - llmobs-net
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.analytics-stable.rule=PathPrefix(`/api/v1/analytics`)"
      - "traefik.http.routers.analytics-stable.priority=1"
      - "traefik.http.routers.analytics-stable.service=analytics-stable-service"
      - "traefik.http.services.analytics-stable-service.loadbalancer.server.port=8081"
```

---

## 5. Developer and QA CLI Field Guide

### 5.1 Step-by-Step Local Terminal Verification

1. **Launch Stack**:
   ```bash
   docker compose -f docker-compose.failover.yml up -d
   ```

2. **Test Active Primary Route**:
   ```bash
   curl -i http://localhost/api/v1/analytics/health
   # Returns: HTTP 200 OK -> {"status":"HEALTHY", "version":"v2-dev"}
   ```

3. **Simulate Crash**:
   ```bash
   docker stop analytics-engine-dev
   ```

4. **Verify Automatic Fallback (< 3s)**:
   ```bash
   curl -i http://localhost/api/v1/analytics/health
   # Returns: HTTP 200 OK -> {"status":"HEALTHY", "version":"v1-stable"}
   ```

5. **Restart Container**:
   ```bash
   docker start analytics-engine-dev
   ```

---

## 6. Summary Matrix

| Metric | Active-Passive Failover | Standard Setup |
|---|---|---|
| **QA Downtime during Crash** | **0 Seconds** | 30m – 2h (Blocked) |
| **Additional Hard Drive Usage** | **< 10 MB** (Layer Cached) | N/A |
| **Additional RAM Footprint** | **~15MB – 80MB** | N/A |
| **Registry Cost** | **$0.00** | N/A |

---

## 7. References
* [ADR-0004: Traefik v3 Ingress Gateway](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/llm-obs-infra/docs/architectureDoc/architecture-decision-record.md#adr-0004-traefik-v37-ingress-gateway)
* [ADR-0009: Service Registry and Discovery Architecture](file:///home/btpl-lap-22/live/llm-observability-platform/packages/configs/llm-obs-infra/docs/architectureDoc/adr-0009-service-registry-and-discovery.md)
