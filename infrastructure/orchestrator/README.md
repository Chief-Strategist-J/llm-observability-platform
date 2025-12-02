# Infrastructure Orchestrator - Technical Documentation

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Deployment Methods](#deployment-methods)
  - [Docker Compose](#docker-compose-deployment)
  - [Python API](#python-api-deployment)
  - [Temporal Workflows](#temporal-workflow-deployment)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Monitoring & Observability](#monitoring--observability)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Infrastructure Orchestrator provides a unified platform for deploying, managing, and monitoring containerized infrastructure services with comprehensive observability, security, and automation capabilities.

### Key Features

- **Centralized Configuration**: Single `.env` file for all service configurations
- **Port Management**: Dynamic port allocation with zero conflicts
- **Network Isolation**: Segmented networks for different service types
- **Security**: TLS encryption, authentication, rate limiting, IP whitelisting
- **Multi-Instance Support**: Run multiple instances of any service
- **Three Deployment Methods**: Docker Compose, Python API, or Temporal Workflows
- **Full Observability**: Metrics (Prometheus), Logs (Loki), Traces (Tempo/Jaeger)

### Supported Services

**Observability Stack:**
- Prometheus (Metrics)
- Grafana (Visualization)
- Loki (Logs Aggregation)
- Tempo (Distributed Tracing)
- Jaeger (Trace Visualization)
- OpenTelemetry Collector
- Promtail (Log Shipper)
- AlertManager (Alerting)
- Traefik (Reverse Proxy & Ingress)

**Data Layer:**
- MongoDB (Document Database)
- Redis (Cache & Message Broker)
- Neo4j (Graph Database)
- Qdrant (Vector Database)

**Messaging:**
- Kafka (Event Streaming)

**CI/CD:**
- ArgoCD Server & Repo Server

**Admin Tools:**
- MongoExpress (MongoDB UI)

---

## Architecture

### Network Topology

```
┌─────────────────────────────────────────────────────────────┐
│                         Traefik                              │
│                    (Reverse Proxy)                           │
│              HTTPS Entry Point (Port 443)                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
       ┌───────────┴──────────────┬──────────────┬────────────┐
       │                          │              │            │
┌──────▼────────┐      ┌─────────▼────┐  ┌──────▼───┐  ┌────▼─────┐
│ Observability │      │    Data      │  │ Messaging│  │  CI/CD   │
│   Network     │      │   Network    │  │  Network │  │  Network │
│ 172.20.0.0/16 │      │172.21.0.0/16 │  │172.22../16│ │172.23../16│
└───────────────┘      └──────────────┘  └──────────┘  └──────────┘
```

### Data Flow

```
Application → OTEL Collector → {Tempo (traces), Prometheus (metrics)}
                ↓
            Loki ← Promtail ← Docker Logs
                ↓
            Grafana (Unified Dashboard)
```

---

---
