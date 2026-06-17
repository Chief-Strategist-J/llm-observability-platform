# Latency Engine

The `latency-engine` is a Kafka consumer worker service that processes raw LLM span events to track and store latency metrics, SLO errors, and latency attribution information.

## Technology Stack & Dependencies

- **Language:** Python 3.11+
- **Protocols:** Kafka, Redis
- **Metrics/Sketches:** `ddsketch` (DataDog DDSketch) with Protocol Buffers serialization

## Features Covered

*   **F-L-01: DDSketch updates**: Dynamic DDSketch creation, update, and base64 Protocol Buffers serialization to Redis.
*   **F-L-02: TPOT calculation**: TPOT computation and storage in Redis rolling list.
*   **F-L-03: SLO error counter update**: Compares span total latency to SLO thresholds and increments minute-based Redis error counters with TTL.
*   **F-L-04: Latency attribution**: Extracts OpenTelemetry latency tags and aggregates them per model/hour.
*   **F-L-05: Retry latency separation**: Routes retry span metrics to a separate retry sketch key.
*   **F-L-06: Dead letter buffering**: Memory buffering and replay mechanism during Redis server outages to prevent blocking Kafka progress.

## Running Tests

Execute the unit tests suite with:
```bash
pytest packages/python/latency-engine/tests/unit -v
```
