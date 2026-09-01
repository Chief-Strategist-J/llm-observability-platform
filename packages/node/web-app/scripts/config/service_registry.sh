#!/usr/bin/env bash

# Service Registry & Target Catalog Data

SERVICE_REGISTRY=(
  "web-app:Next.js Web Application:${PORT_UNIT}:${APP_DIR}:PORT=${PORT_UNIT} npx next dev -p ${PORT_UNIT}"
  "auth:Auth HTTP Service:${PORT_AUTH}:${AUTH_DIR}:PORT=${PORT_AUTH} npx tsx src/server.ts"
  "storybook:Storybook Server:${PORT_STORYBOOK}:${APP_DIR}:npx storybook dev -p ${PORT_STORYBOOK}"
  "latency-engine:Latency Engine Worker & API:${PORT_LATENCY}:${LATENCY_DIR}:${LATENCY_DIR}/scripts/run.sh"
  "latency:Latency Engine Worker & API:${PORT_LATENCY}:${LATENCY_DIR}:${LATENCY_DIR}/scripts/run.sh"
  "quality-engine:Quality Engine Scorer Worker:${PORT_QUALITY}:${QUALITY_DIR}:${QUALITY_DIR}/scripts/run.sh"
  "quality:Quality Engine Scorer Worker:${PORT_QUALITY}:${QUALITY_DIR}:${QUALITY_DIR}/scripts/run.sh"
  "alert-engine:Alert Engine Notification Worker:${PORT_ALERT}:${ALERT_DIR}:${ALERT_DIR}/scripts/run.sh"
  "alert:Alert Engine Notification Worker:${PORT_ALERT}:${ALERT_DIR}:${ALERT_DIR}/scripts/run.sh"
  "faithfulness:Faithfulness Scorer Service:${PORT_FAITHFULNESS}:${FAITHFULNESS_DIR}:${FAITHFULNESS_DIR}/scripts/run.sh"
  "perplexity:Perplexity Scorer Service:${PORT_PERPLEXITY}:${PERPLEXITY_DIR}:${PERPLEXITY_DIR}/scripts/run.sh"
  "toxicity:Toxicity Detector Service:${PORT_TOXICITY}:${TOXICITY_DIR}:${TOXICITY_DIR}/scripts/run.sh"
  "nli-worker:NLI Classifier Worker:${PORT_NLI}:${NLI_DIR}:${NLI_DIR}/scripts/run.sh"
  "nli:NLI Classifier Worker:${PORT_NLI}:${NLI_DIR}:${NLI_DIR}/scripts/run.sh"
  "queue-embedding-worker:Queue Embedding Worker:${PORT_EMBEDDING}:${EMBEDDING_DIR}:${EMBEDDING_DIR}/scripts/run.sh"
  "embedding:Queue Embedding Worker:${PORT_EMBEDDING}:${EMBEDDING_DIR}:${EMBEDDING_DIR}/scripts/run.sh"
  "semantic-coherence:Semantic Coherence Worker:${PORT_COHERENCE}:${COHERENCE_DIR}:${COHERENCE_DIR}/scripts/run.sh"
  "coherence:Semantic Coherence Worker:${PORT_COHERENCE}:${COHERENCE_DIR}:${COHERENCE_DIR}/scripts/run.sh"
  "slo-burn-worker:SLO Burn Rate Worker:${PORT_SLO}:${SLO_DIR}:${SLO_DIR}/scripts/run.sh"
  "slo:SLO Burn Rate Worker:${PORT_SLO}:${SLO_DIR}:${SLO_DIR}/scripts/run.sh"
  "temporal-ewma-worker:Temporal EWMA Worker:${PORT_EWMA}:${EWMA_DIR}:${EWMA_DIR}/scripts/run.sh"
  "ewma:Temporal EWMA Worker:${PORT_EWMA}:${EWMA_DIR}:${EWMA_DIR}/scripts/run.sh"
  "budget-provisioner:Budget Provisioner Service:${PORT_BUDGET}:${BUDGET_DIR}:${BUDGET_DIR}/scripts/run.sh"
  "budget:Budget Provisioner Service:${PORT_BUDGET}:${BUDGET_DIR}:${BUDGET_DIR}/scripts/run.sh"
  "event-cost:Event Cost Calculator Worker:${PORT_EVENT_COST}:${EVENT_COST_DIR}:${EVENT_COST_DIR}/scripts/run.sh"
  "cost:Event Cost Calculator Worker:${PORT_EVENT_COST}:${EVENT_COST_DIR}:${EVENT_COST_DIR}/scripts/run.sh"
  "forecast-worker:Forecast Engine Worker:${PORT_FORECAST}:${FORECAST_DIR}:${FORECAST_DIR}/scripts/run.sh"
  "forecast:Forecast Engine Worker:${PORT_FORECAST}:${FORECAST_DIR}:${FORECAST_DIR}/scripts/run.sh"
)

BUILD_TARGETS=(
  ".next"
  "storybook-static"
  "tsconfig.tsbuildinfo"
  ".cache"
  "coverage"
  ".vitest"
)

DEEP_TARGETS=(
  "node_modules"
  "package-lock.json"
)
