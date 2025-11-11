This final tree is:

* **Modular** (loose coupling)
* **Activity-based** (clear automation tasks you can implement in Temporal/Airflow)
* **Priority-graded** (P0 → P3; P3 = future AI/monetization)
* **Extensible** (OTel Collector today → metrics/traces later → AI later)
* **Productizable** (how to package/sell as a product)

Read straight through — it’s a single self-contained artifact you can copy into docs.

---

# START: ONE-COLLECTOR OBSERVABILITY PLATFORM (FINAL MASTER TREE)

```
START: ONE-COLLECTOR OBSERVABILITY PLATFORM
│
? intent = [INGEST | QUERY | ALERT | OPERATE | CONTROL_PLANE | AI_PRODUCT]
│
├─ INGEST  ───────────────────────────────► TREE A  (P0→P1)
├─ QUERY   ───────────────────────────────► TREE B  (P1)
├─ ALERT   ───────────────────────────────► TREE C  (P1→P2)
├─ OPERATE ───────────────────────────────► TREE D  (P0→P1→P2)
├─ CONTROL_PLANE ────────────────────────► TREE E  (P0→P1→P2)
└─ AI_PRODUCT (future ML/analytics) ─────► TREE F  (P3)
```

---

## TREE A — INGEST (Apps & Containers → OpenTelemetry Collector → Loki now; metrics/traces later)  **(P0 first)**

```
INGEST
│
? signal_type = [logs | metrics | traces]
│
├─ LOGS (P0 - FULLY AUTOMATED)
│   │
│   CONTROL PLANE TRIGGERS THESE ACTIVITIES AUTOMATICALLY:
│   │
│   ├─ auto_discover_all_log_sources_activity
│   │   WHAT IT DOES:
│   │   • Scans Docker containers (via Docker API)
│   │   • Scans Kubernetes pods (via K8s API)
│   │   • Scans filesystem log directories (/var/log/*)
│   │   • Detects application-specific log paths from environment variables
│   │   • Returns complete inventory of all log sources
│   │
│   │   LOGIC:
│   │   • Connect to Docker socket, subscribe to container events
│   │   • Watch K8s pod lifecycle events in all namespaces
│   │   • Recursively scan configured filesystem paths
│   │   • Parse container labels/pod annotations for custom log hints
│   │   • Merge all discovered sources into unified registry
│   │   • Emit "new_log_source_discovered" event for each source
│   │
│   │   SERVICES NEEDED:
│   │   • DockerEventStreamService - maintains Docker socket connection
│   │   • K8sPodWatchService - maintains K8s API watch connection
│   │   • FilesystemScannerService - scans directories with patterns
│   │   • MetadataExtractorService - extracts labels/annotations/env vars
│   │
│   │   MODELS:
│   │   • DiscoveredLogSource
│   │       - source_id: str (unique hash)
│   │       - source_type: enum (docker, k8s, filesystem)
│   │       - log_path: str
│   │       - metadata: Dict (container_id, pod_name, namespace, labels)
│   │       - discovered_at: datetime
│   │       - status: enum (active, inactive)
│   │
│   │   API CLIENTS:
│   │   • DockerAPIClient - Docker Engine API wrapper
│   │   • KubernetesAPIClient - K8s API wrapper
│   │
│   ├─ auto_register_log_sources_activity
│   │   WHAT IT DOES:
│   │   • Takes discovered sources from previous activity
│   │   • Automatically registers them in LogSourceRegistry database
│   │   • Assigns unique IDs, timestamps, default labels
│   │   • No human approval needed
│   │
│   │   LOGIC:
│   │   • Check if source already exists (by log_path hash)
│   │   • If new: insert into registry with auto-generated ID
│   │   • If exists: update metadata, set last_seen timestamp
│   │   • Assign default labels based on source type
│   │   • Mark inactive sources (not seen in last N minutes)
│   │   • Emit "log_source_registered" event
│   │
│   │   SERVICES NEEDED:
│   │   • RegistryStorageService - CRUD operations on registry DB
│   │   • LabelGeneratorService - auto-generates default labels
│   │   • DeduplicationService - prevents duplicate registrations
│   │
│   │   MODELS:
│   │   • RegisteredLogSource
│   │       - id: UUID
│   │       - source: DiscoveredLogSource
│   │       - labels: Dict[str, str]
│   │       - registered_at: datetime
│   │       - last_seen: datetime
│   │       - config_version: int
│   │
│   ├─ auto_generate_collector_config_activity
│   │   WHAT IT DOES:
│   │   • Reads all registered sources from registry
│   │   • Automatically generates complete OTel Collector YAML config
│   │   • Includes receivers, processors, exporters for ALL sources
│   │   • No manual YAML editing needed
│   │
│   │   LOGIC:
│   │   • Query registry for all active log sources
│   │   • For each source, generate filelog receiver block:
│   │       - include: [log_path]
│   │       - multiline detection (stacktraces, JSON)
│   │       - json_parser if JSON format detected
│   │       - timestamp extraction
│   │   • Generate resource processor with service.name, host.name
│   │   • Generate attributes processor for label enrichment
│   │   • Generate k8sattributes processor if K8s sources exist
│   │   • Generate batch processor (optimize throughput)
│   │   • Generate memory_limiter processor (prevent OOM)
│   │   • Generate loki exporter pointing to Loki endpoint
│   │   • Render complete YAML config
│   │   • Store config in versioned artifact store
│   │   • Return config_artifact_id
│   │
│   │   SERVICES NEEDED:
│   │   • ConfigTemplateEngine - Jinja2 templates for config generation
│   │   • ReceiverBuilder - builds receiver configs
│   │   • ProcessorBuilder - builds processor configs
│   │   • ExporterBuilder - builds exporter configs
│   │   • ConfigValidator - validates generated YAML
│   │   • ConfigArtifactStore - stores versioned configs
│   │
│   │   MODELS:
│   │   • CollectorConfig
│   │       - receivers: Dict[str, Any]
│   │       - processors: Dict[str, Any]
│   │       - exporters: Dict[str, Any]
│   │       - service_pipelines: Dict[str, Pipeline]
│   │       - version: int
│   │       - generated_at: datetime
│   │
│   ├─ auto_deploy_collector_config_activity
│   │   WHAT IT DOES:
│   │   • Takes generated config from previous activity
│   │   • Automatically deploys it to OTel Collector instance
│   │   • Triggers hot reload (no collector restart)
│   │   • No manual kubectl/docker commands needed
│   │
│   │   LOGIC:
│   │   • Fetch config artifact from store
│   │   • Push config to collector's config endpoint (HTTP API)
│   │   • OR write config to mounted volume if collector watches file
│   │   • Trigger collector reload via reload endpoint
│   │   • Wait for reload acknowledgment
│   │   • Poll collector health endpoint
│   │   • Emit "config_deployed" event
│   │
│   │   SERVICES NEEDED:
│   │   • CollectorAPIClient - HTTP client for collector management API
│   │   • ConfigDeploymentService - handles config push & reload
│   │   • HealthCheckService - polls collector health
│   │
│   │   MODELS:
│   │   • DeploymentResult
│   │       - config_version: int
│   │       - deployed_at: datetime
│   │       - collector_id: str
│   │       - status: enum (success, failed)
│   │       - rollback_config: Optional[int]
│   │
│   ├─ auto_verify_log_pipeline_activity
│   │   WHAT IT DOES:
│   │   • Automatically tests that logs are flowing end-to-end
│   │   • Injects test log entry
│   │   • Queries Loki to verify it arrived
│   │   • No manual verification needed
│   │
│   │   LOGIC:
│   │   • Generate unique test log message with UUID
│   │   • Write test log to one of the monitored log files
│   │   • Wait 30 seconds for ingestion
│   │   • Query Loki for test log using UUID
│   │   • Check if log found with correct labels
│   │   • Return verification result
│   │
│   │   SERVICES NEEDED:
│   │   • TestLogInjectorService - writes test logs
│   │   • LokiQueryService - queries Loki API
│   │   • VerificationService - compares expected vs actual
│   │
│   │   MODELS:
│   │   • VerificationResult
│   │       - test_id: UUID
│   │       - log_found: bool
│   │       - latency_seconds: float
│   │       - labels_correct: bool
│   │       - verified_at: datetime
│   │
│   └─ auto_rollback_on_failure_activity
│       WHAT IT DOES:
│       • If verification fails, automatically rolls back config
│       • Restores previous working config version
│       • Sends alert to monitoring
│       • No manual intervention needed
│
│       LOGIC:
│       • Detect failed verification from previous activity
│       • Fetch last known good config version from artifact store
│       • Deploy previous config to collector
│       • Trigger reload
│       • Verify rollback succeeded
│       • Send alert with failure details
│       • Mark failed config as "broken"
│
│       SERVICES NEEDED:
│       • RollbackService - manages config version history
│       • AlertingService - sends alerts to Slack/PagerDuty
│       • ConfigDeploymentService (reuse)
│
│       MODELS:
│       • RollbackEvent
│           - failed_config_version: int
│           - rollback_to_version: int
│           - reason: str
│           - rolled_back_at: datetime
│
├─ METRICS (P1 - FULLY AUTOMATED)
│   │
│   CONTROL PLANE TRIGGERS THESE ACTIVITIES AUTOMATICALLY:
│   │
│   ├─ auto_discover_all_metric_sources_activity
│   │   WHAT IT DOES:
│   │   • Scans K8s pods for prometheus.io/scrape=true annotations
│   │   • Detects OTLP-enabled applications (via env vars or labels)
│   │   • Discovers host metrics endpoints
│   │   • Returns complete inventory of metric sources
│   │
│   │   LOGIC:
│   │   • Query K8s API for all pods in all namespaces
│   │   • Filter pods with prometheus.io/scrape="true"
│   │   • Extract prometheus.io/port and prometheus.io/path
│   │   • Scan pods for OTEL_EXPORTER_OTLP_ENDPOINT env var
│   │   • Detect applications with OTLP SDK libraries loaded
│   │   • Identify host metric collection requirement (node-level)
│   │   • Emit "new_metric_source_discovered" event
│   │
│   │   SERVICES NEEDED:
│   │   • K8sAnnotationScanner - reads pod annotations
│   │   • OTLPEndpointDetector - detects OTLP-enabled apps
│   │   • HostMetricsDetector - identifies nodes needing host metrics
│   │
│   │   MODELS:
│   │   • DiscoveredMetricSource
│   │       - source_id: str
│   │       - source_type: enum (prometheus_scrape, otlp, hostmetrics)
│   │       - endpoint: str
│   │       - scrape_config: Optional[ScrapeConfig]
│   │       - metadata: Dict
│   │       - discovered_at: datetime
│   │
│   ├─ auto_register_metric_sources_activity
│   │   WHAT IT DOES:
│   │   • Automatically registers discovered metric sources
│   │   • Assigns IDs, default labels, scrape intervals
│   │   • No human approval needed
│   │
│   │   LOGIC:
│   │   • Check if metric source already exists
│   │   • Insert new sources into MetricSourceRegistry
│   │   • Update existing sources with latest metadata
│   │   • Assign default scrape_interval based on source type
│   │   • Emit "metric_source_registered" event
│   │
│   │   SERVICES NEEDED:
│   │   • MetricRegistryService - CRUD for metric sources
│   │   • ScrapeConfigGenerator - generates scrape configs
│   │
│   │   MODELS:
│   │   • RegisteredMetricSource
│   │       - id: UUID
│   │       - source: DiscoveredMetricSource
│   │       - scrape_interval: int
│   │       - labels: Dict[str, str]
│   │       - registered_at: datetime
│   │
│   ├─ auto_generate_metric_pipeline_config_activity
│   │   WHAT IT DOES:
│   │   • Automatically generates OTel Collector metric pipeline config
│   │   • Adds OTLP receiver, Prometheus scrape receiver, hostmetrics receiver
│   │   • Configures Prometheus remote_write exporter
│   │   • No manual YAML editing needed
│   │
│   │   LOGIC:
│   │   • Query MetricSourceRegistry for all active sources
│   │   • Generate OTLP receiver (gRPC + HTTP) if OTLP sources exist
│   │   • Generate Prometheus receiver with scrape_configs for Prometheus sources
│   │   • Generate hostmetrics receiver if host monitoring needed
│   │   • Generate batch, memory_limiter, resource processors
│   │   • Generate prometheusremotewrite exporter to Prometheus endpoint
│   │   • Merge with existing log pipeline config
│   │   • Validate complete config
│   │   • Store versioned config artifact
│   │
│   │   SERVICES NEEDED:
│   │   • MetricPipelineBuilder - builds metric pipeline config
│   │   • ConfigMerger - merges log + metric pipelines
│   │   • ConfigValidator (reuse)
│   │   • ConfigArtifactStore (reuse)
│   │
│   │   MODELS:
│   │   • MetricPipelineConfig
│   │       - receivers: Dict[str, Any]
│   │       - processors: Dict[str, Any]
│   │       - exporters: Dict[str, Any]
│   │       - version: int
│   │
│   ├─ auto_deploy_metric_pipeline_activity
│   │   WHAT IT DOES:
│   │   • Automatically deploys updated config to collector
│   │   • Hot reloads collector with metric pipeline enabled
│   │   • No manual deployment needed
│   │
│   │   LOGIC:
│   │   • (Same as auto_deploy_collector_config_activity)
│   │   • Push merged config to collector
│   │   • Trigger reload
│   │   • Wait for health check
│   │
│   │   SERVICES NEEDED:
│   │   • CollectorAPIClient (reuse)
│   │   • ConfigDeploymentService (reuse)
│   │
│   ├─ auto_verify_metric_pipeline_activity
│   │   WHAT IT DOES:
│   │   • Automatically verifies metrics are flowing to Prometheus
│   │   • Queries Prometheus for expected metrics
│   │   • No manual verification needed
│   │
│   │   LOGIC:
│   │   • Wait 60 seconds for metrics to arrive
│   │   • Query Prometheus for known metric names from discovered sources
│   │   • Verify metric labels match expected values
│   │   • Check scrape success rate
│   │   • Return verification result
│   │
│   │   SERVICES NEEDED:
│   │   • PrometheusQueryService - queries Prometheus API
│   │   • MetricVerificationService - validates metrics
│   │
│   │   MODELS:
│   │   • MetricVerificationResult
│   │       - metrics_found: int
│   │       - scrape_success_rate: float
│   │       - verified_at: datetime
│   │
│   └─ auto_rollback_on_metric_failure_activity
│       WHAT IT DOES:
│       • Automatically rolls back if metric pipeline fails
│       • (Same logic as auto_rollback_on_failure_activity)
│
└─ TRACES (P1 - FULLY AUTOMATED)
    │
    CONTROL PLANE TRIGGERS THESE ACTIVITIES AUTOMATICALLY:
    │
    ├─ auto_discover_all_trace_sources_activity
    │   WHAT IT DOES:
    │   • Detects applications sending OTLP traces
    │   • Detects Jaeger-instrumented applications
    │   • Detects Zipkin-instrumented applications
    │   • Returns complete inventory of trace sources
    │
    │   LOGIC:
    │   • Scan pods for OTEL_TRACES_EXPORTER env var
    │   • Detect Jaeger client libraries in running processes
    │   • Detect Zipkin client libraries in running processes
    │   • Check for trace endpoints being accessed (network traffic analysis)
    │   • Emit "new_trace_source_discovered" event
    │
    │   SERVICES NEEDED:
    │   • TraceEndpointDetector - detects trace instrumentation
    │   • NetworkTrafficAnalyzer - monitors trace endpoint traffic
    │
    │   MODELS:
    │   • DiscoveredTraceSource
    │       - source_id: str
    │       - source_type: enum (otlp, jaeger, zipkin)
    │       - protocol: str
    │       - endpoint: str
    │       - metadata: Dict
    │
    ├─ auto_register_trace_sources_activity
    │   WHAT IT DOES:
    │   • Automatically registers discovered trace sources
    │   • No human approval needed
    │
    │   LOGIC:
    │   • Insert trace sources into TraceSourceRegistry
    │   • Assign default sampling rates
    │   • Emit "trace_source_registered" event
    │
    │   SERVICES NEEDED:
    │   • TraceRegistryService - CRUD for trace sources
    │
    │   MODELS:
    │   • RegisteredTraceSource
    │       - id: UUID
    │       - source: DiscoveredTraceSource
    │       - sampling_rate: float
    │       - registered_at: datetime
    │
    ├─ auto_generate_trace_pipeline_config_activity
    │   WHAT IT DOES:
    │   • Automatically generates OTel Collector trace pipeline config
    │   • Adds OTLP, Jaeger, Zipkin receivers as needed
    │   • Configures Tempo and/or Jaeger exporters
    │   • No manual YAML editing needed
    │
    │   LOGIC:
    │   • Query TraceSourceRegistry for all active sources
    │   • Generate OTLP receiver if OTLP sources exist
    │   • Generate Jaeger receiver if Jaeger sources exist
    │   • Generate Zipkin receiver if Zipkin sources exist
    │   • Generate trace processors (batch, sampling, memory_limiter)
    │   • Generate Tempo exporter (OTLP to Tempo)
    │   • Generate Jaeger exporter if Jaeger backend configured
    │   • Merge with existing log + metric pipeline config
    │   • Validate complete config
    │   • Store versioned config artifact
    │
    │   SERVICES NEEDED:
    │   • TracePipelineBuilder - builds trace pipeline config
    │   • ConfigMerger (reuse)
    │   • ConfigValidator (reuse)
    │   • ConfigArtifactStore (reuse)
    │
    │   MODELS:
    │   • TracePipelineConfig
    │       - receivers: Dict[str, Any]
    │       - processors: Dict[str, Any]
    │       - exporters: Dict[str, Any]
    │       - version: int
    │
    ├─ auto_deploy_trace_pipeline_activity
    │   WHAT IT DOES:
    │   • Automatically deploys updated config to collector
    │   • Hot reloads collector with trace pipeline enabled
    │   • No manual deployment needed
    │
    │   LOGIC:
    │   • (Same as auto_deploy_collector_config_activity)
    │
    │   SERVICES NEEDED:
    │   • CollectorAPIClient (reuse)
    │   • ConfigDeploymentService (reuse)
    │
    ├─ auto_verify_trace_pipeline_activity
    │   WHAT IT DOES:
    │   • Automatically verifies traces are flowing to Tempo/Jaeger
    │   • Generates test trace and queries backend
    │   • No manual verification needed
    │
    │   LOGIC:
    │   • Inject test trace with unique trace_id
    │   • Wait 60 seconds for trace to arrive
    │   • Query Tempo/Jaeger for test trace_id
    │   • Verify trace found with correct spans
    │   • Return verification result
    │
    │   SERVICES NEEDED:
    │   • TestTraceGenerator - generates synthetic traces
    │   • TempoQueryService - queries Tempo API
    │   • JaegerQueryService - queries Jaeger API
    │
    │   MODELS:
    │   • TraceVerificationResult
    │       - trace_found: bool
    │       - span_count: int
    │       - verified_at: datetime
    │
    └─ auto_rollback_on_trace_failure_activity
        WHAT IT DOES:
        • Automatically rolls back if trace pipeline fails
        • (Same logic as auto_rollback_on_failure_activity)
```

**INGEST: Key design rules**

* Keep labels low-cardinality (enforce in `attributes_processor`).
* All activities idempotent & time-bounded.
* Use event bus (Kafka/NATS) for discovery events to decouple watchers from builder.
* Persist registry in transactional DB (Postgres/etcd) with schema versioning.

---

## TREE B — QUERY (Grafana + API; Logs now, Metrics/Traces later)  **(P1)**

```
QUERY
│
? signal = [logs | metrics | traces]
│
├─ LOGS (P1 - FULLY AUTOMATED)
│   │
│   CONTROL PLANE TRIGGERS THESE ACTIVITIES AUTOMATICALLY:
│   │
│   ├─ auto_create_loki_datasource_activity
│   │   WHAT IT DOES:
│   │   • Automatically creates Loki datasource in Grafana
│   │   • Detects Loki endpoint from service discovery
│   │   • Configures auth automatically
│   │   • No manual Grafana UI clicks needed
│   │
│   │   LOGIC:
│   │   • Discover Loki service endpoint (K8s service DNS or Docker network)
│   │   • Check if Loki datasource already exists in Grafana
│   │   • If not exists: create via Grafana API
│   │   • Configure derived fields for trace linking (extract trace_id from logs)
│   │   • Set as default datasource for logs
│   │   • Test datasource connection
│   │   • Emit "loki_datasource_created" event
│   │
│   │   SERVICES NEEDED:
│   │   • ServiceDiscoveryClient - discovers Loki endpoint
│   │   • GrafanaAPIClient - manages Grafana datasources
│   │
│   │   MODELS:
│   │   • GrafanaDatasource
│   │       - name: str
│   │       - type: str
│   │       - url: str
│   │       - is_default: bool
│   │       - derived_fields: List[DerivedField]
│   │
│   ├─ auto_create_log_dashboards_activity
│   │   WHAT IT DOES:
│   │   • Automatically generates Grafana dashboards for logs
│   │   • Creates dashboards per service, namespace, pod
│   │   • No manual dashboard creation needed
│   │
│   │   LOGIC:
│   │   • Query LogSourceRegistry for all registered services
│   │   • For each service, generate dashboard JSON with:
│   │       - Log volume panel (rate of logs per service)
│   │       - Error rate panel (count of error-level logs)
│   │       - Log stream panel (live tail)
│   │       - Log level distribution panel
│   │   • Push dashboard to Grafana via API
│   │   • Create folder structure (e.g., "Auto-Generated Logs")
│   │   • Emit "dashboard_created" event
│   │
│   │   SERVICES NEEDED:
│   │   • DashboardTemplateEngine - generates dashboard JSON
│   │   • GrafanaAPIClient (reuse)
│   │
│   │   MODELS:
│   │   • GrafanaDashboard
│   │       - title: str
│   │       - panels: List[Panel]
│   │       - folder: str
│   │       - uid: str
│   │
│   └─ auto_configure_log_query_caching_activity
│       WHAT IT DOES:
│       • Automatically configures query frontend caching
│       • No manual Redis/Memcached setup needed
│
│       LOGIC:
│       • Deploy Redis/Memcached if not exists
│       • Configure Loki query-frontend to use cache
│       • Set cache TTL based on query patterns
│       • Emit "caching_configured" event
│
│       SERVICES NEEDED:
│       • CacheDeploymentService - deploys cache backend
│       • LokiConfigService - updates Loki config
│
├─ METRICS (P1 - FULLY AUTOMATED)
│   │
│   CONTROL PLANE TRIGGERS THESE ACTIVITIES AUTOMATICALLY:
│   │
│   ├─ auto_create_prometheus_datasource_activity
│   │   WHAT IT DOES:
│   │   • Automatically creates Prometheus datasource in Grafana
│   │   • No manual configuration needed
│   │
│   │   LOGIC:
│   │   • Discover Prometheus endpoint
│   │   • Check if datasource exists
│   │   • Create datasource via Grafana API
│   │   • Set as default for metrics
│   │   • Test connection
│   │
│   │   SERVICES NEEDED:
│   │   • ServiceDiscoveryClient (reuse)
│   │   • GrafanaAPIClient (reuse)
│   │
│   ├─ auto_create_metric_dashboards_activity
│   │   WHAT IT DOES:
│   │   • Automatically generates Grafana dashboards for metrics
│   │   • Creates RED dashboards (Rate, Errors, Duration) per service
│   │   • No manual dashboard creation needed
│   │
│   │   LOGIC:
│   │   • Query MetricSourceRegistry for all services
│   │   • For each service, generate dashboard with:
│   │       - Request rate panel
│   │       - Error rate panel
│   │       - Request duration (latency) panel
│   │       - CPU/Memory usage panels
│   │       - Saturation metrics
│   │   • Push dashboards to Grafana
│   │
│   │   SERVICES NEEDED:
│   │   • DashboardTemplateEngine (reuse)
│   │   • GrafanaAPIClient (reuse)
│   │
│   └─ auto_create_slo_dashboards_activity
│       WHAT IT DOES:
│       • Automatically creates SLO tracking dashboards
│       • No manual SLO definition needed (uses defaults)
│
│       LOGIC:
│       • Define default SLOs (99.9% availability, p99 < 500ms)
│       • Generate SLO dashboard with error budget burn rate
│       • Push to Grafana
│
│       SERVICES NEEDED:
│       • SLODashboardGenerator
│       • GrafanaAPIClient (reuse)
│
└─ TRACES (P1 - FULLY AUTOMATED)
    │
    CONTROL PLANE TRIGGERS THESE ACTIVITIES AUTOMATICALLY:
    │
    ├─ auto_create_tempo_datasource_activity
    │   WHAT IT DOES:
    │   • Automatically creates Tempo datasource in Grafana
    │   • No manual configuration needed
    │
    │   LOGIC:
    │   • Discover Tempo endpoint
    │   • Check if datasource exists
    │   • Create datasource via Grafana API
    │   • Configure trace-to-logs linking (Loki derived fields)
    │   • Test connection
    │
    │   SERVICES NEEDED:
    │   • ServiceDiscoveryClient (reuse)
    │   • GrafanaAPIClient (reuse)
    │
    ├─ auto_create_jaeger_datasource_activity
    │   WHAT IT DOES:
    │   • Automatically creates Jaeger datasource if Jaeger backend used
    │   • No manual configuration needed
    │
    │   LOGIC:
    │   • (Same as Tempo datasource creation)
    │
    └─ auto_create_trace_dashboards_activity
        WHAT IT DOES:
        • Automatically generates service dependency map dashboard
        • Creates trace latency dashboards per service
        • No manual dashboard creation needed
    
        LOGIC:
        • Query TraceSourceRegistry for all services
        • Generate service map dashboard (nodes = services, edges = calls)
        • Generate latency distribution dashboard per service
        • Push dashboards to Grafana
    
        SERVICES NEEDED:
        • TraceDashboardGenerator
        • GrafanaAPIClient (reuse)
```

**QUERY: Notes**

* Query Frontend caching + rate limiting to protect backends.
* BatchQueryExecutor splits large time windows into fan-out jobs.

---

## TREE C — ALERT (Log-based & metric-based alerts)  **(P1)**

```
ALERT
│
? engine = [loki_ruler | grafana_alerts | prom_alerts]
│
├─ loki_ruler (log rules)
│   CLASSES: LokiRulerClient
│   METHODS: create_rule(), test_rule()
│   ACTIVITIES:
│     - deploy_log_rule_activity
│     - evaluate_and_fire_activity
│
├─ grafana_alerts
│   ACTIVITIES:
│     - create_grafana_alert_activity
│     - route_alert_activity
│
└─ prom_alerts (later, P1)
    ACTIVITIES:
      - create_prometheus_rule_activity
```

**ALERT: Design**

* Use dedupe & grouping in AlertGenerator.
* Include runbooks links in alerts.
* Tempo linking for trace on alert (P2).

---

## TREE D — OPERATE (Lifecycle, Scale, Security, SLOs)  **(P0→P1→P2)**

```
OPERATE
│
? maturity = [P0 | P1 | P2]
│
├─ P0: Lifecycle (essential)
│   ACTIVITIES:
│     - start_collector_activity
│     - stop_collector_activity
│     - reload_collector_activity
│     - start_loki_activity
│     - verify_services_health_activity
│   ACCEPTANCE:
│     - collector / loki ready probes pass
│
├─ P1: Scale & Storage
│   CLASSES:
│     - ChunkStorageBackend (S3/MinIO)
│     - HealthMonitor
│   ACTIVITIES:
│     - scale_component_activity(component, replicas)
│     - verify_replication_activity()
│     - compact_and_retention_activity()
│   ACCEPTANCE:
│     - chunk upload success rate > 99.9%
│
└─ P2: Security, Tenancy & Governance
    CLASSES:
      - CertManager
      - GatewayAuthMiddleware
      - AccessPolicyManager
      - SLOEvaluator
    ACTIVITIES:
      - issue_agent_certificate_activity()
      - rotate_certificate_activity()
      - enforce_tenant_quota_activity()
      - evaluate_SLOs_activity()
      - run_chaos_test_activity()
    ACCEPTANCE:
      - mTLS validated; per-tenant quotas in effect; SLO alerts configured
```

**OPERATE: Principles**

* Automation for lifecycle via Temporal / Kubernetes operators.
* All lifecycle activities idempotent & safe to re-run.
* Extensive metrics & dashboards for platform health.

---

## TREE E — CONTROL_PLANE (Discovery → Registry → Config Builder → AgentManager)  **(P0→P2)**

```
CONTROL_PLANE
│
? mode = [simple_polling | event_stream (recommended) | hybrid]
│
├─ DiscoveryService
│   METHODS:
│     - watch_docker_events()
│     - watch_k8s_api()
│     - watch_filesystem()
│     - emit_discovery_event()
│   ACTIVITIES:
│     - docker_watch_activity
│     - k8s_watch_activity
│
├─ LogSourceRegistry
│   METHODS:
│     - register_source(metadata)
│     - update_source()
│     - delete_source()
│     - list_sources()
│   ACTIVITIES:
│     - upsert_registry_record_activity
│
├─ OtelConfigBuilder
│   METHODS:
│     - load_registry_state()
│     - generate_log_pipeline()
│     - generate_metrics_pipeline()
│     - generate_traces_pipeline()
│     - validate_config()
│     - render_yaml()
│   ACTIVITIES:
│     - build_config_activity
│     - validate_config_activity
│
├─ AgentManager
│   METHODS:
│     - push_config_to_collector()
│     - trigger_reload_api()
│     - check_reload_result()
│   ACTIVITIES:
│     - push_config_activity
│     - canary_reload_activity (P1)
│     - rollback_config_activity
│
└─ Coordination (workflow)
    ACTIVITIES:
      - promtail_dynamic_reload_workflow (rename → collector_dynamic_reload_workflow)
      - schedule_reconcile_activity
      - handle_config_change_event_activity
```

**CONTROL_PLANE: Architecture**

* **Event-driven**: discovery emits events → config builder subscribes → generates config → agentmanager reloads.
* **Message bus** recommended (Kafka, NATS) for loose coupling & replayability.
* **Config versioning** + immutable artifacts + rollback.

---

## TREE F — AI_PRODUCT (Analytics, ML, Monetization)  **(P3 future)**

```
AI_PRODUCT
│
? goal = [smart_routing | anomaly_detection | insights_market]
│
├─ Anomaly Detection & Insights (P3)
│   USE:
│     • Training Data Pipeline
│         - export_labelled_logs_activity
│         - transform_and_enrich_activity
│         - store_training_artifact_activity
│     • Model Training & Serving
│         - train_model_activity
│         - evaluate_model_activity
│         - serve_model_inference_activity
│     • Real-time Detection
│         - stream_inference_activity
│         - raise_ai_alert_activity
│
├─ Smart Routing & Auto-Remediation (P3)
│   ACTIVITIES:
│     - recommend_relabel_rules_activity
│     - auto_rollout_config_activity (human-in-loop)
│
└─ Productization & Marketplace (P3)
    ACTIVITIES:
      - package_saas_offer_activity
      - provide_self_hosted_helm_chart_activity
      - telemetry_privacy_and_compliance_activity
```

**AI_PRODUCT: Design**

* Strict data governance & opt-in for training data.
* Use offline exports + synthetic labels for supervised models.
* Human-in-loop for auto actions (canary + approval).
* Monetize via features (anomaly detection, insights, managed hosting).

---

# MODULES / CLASSES SUMMARY (Single-screen)

```
CONTROL PLANE:
  DiscoveryService, LogSourceRegistry, RegistryRepository,
  OtelConfigBuilder, ConfigTemplateLoader, AgentManager, HealthMonitor

DATA PLANE:
  OTelCollectorAgent, LokiDistributorClient, LokiQuerierClient, LokiRulerClient, ChunkStorageBackend

SDK (minimal; optional):
  Auto-instrumentation wrappers (startup scripts only)

SECURITY:
  CertManager, GatewayAuthMiddleware, AccessPolicyManager

OBSERVABILITY:
  MetricsCollector, SLOEvaluator, AlertGenerator, ChaosTester

AI/MODELS:
  TrainingPipeline, ModelTrainer, InferenceService, DataExportService
```

---

# ACTIVITIES (Actionable, Activity-level names for Temporal / Orchestration)

> Activities are intentionally fine-grained and **loosely coupled** so you can compose them into workflows.

**Discovery / Registry / Config**

```
docker_watch_activity
k8s_watch_activity
filesystem_watch_activity
register_service_activity
deregister_service_activity
upsert_registry_record_activity
build_config_activity
validate_config_activity
render_config_activity
store_config_artifact_activity
```

**Deployment / Agent**

```
push_config_activity
canary_reload_activity
rollback_config_activity
verify_reload_activity
verify_collector_health_activity
list_active_collectors_activity
register_new_collector_activity
```

**Ingestion / Shipping**

```
discover_log_files_activity
tail_and_ship_logs_activity
collect_otlp_activity
route_streams_activity
label_enrichment_activity
```

**Query / Export / Alerts**

```
serve_query_activity
run_batch_query_activity
export_logs_to_datalake_activity
deploy_log_rule_activity
evaluate_rule_activity
send_alert_activity
```

**Ops / Scale / Security**

```
start_collector_activity
stop_collector_activity
restart_collector_activity
start_loki_activity
scale_component_activity
issue_agent_certificate_activity
rotate_certificate_activity
enforce_tenant_quota_activity
evaluate_SLOs_activity
run_chaos_test_activity
```

**AI / ML (P3)**

```
export_labelled_logs_activity
preprocess_training_data_activity
train_model_activity
evaluate_model_activity
deploy_model_activity
stream_inference_activity
recommend_config_activity
auto_rollout_recommendation_activity
```

---

# FULL WORKFLOW (Event-driven sequence — ASCII)

```
[Container start] ──▶ docker_k8s_watch_activity ──▶ register_service_activity ──▶ upsert_registry_record_activity
     │                                                                                     │
     └─────────────────────────────────────────▶ build_config_activity ──▶ validate_config_activity ──▶ store_config_artifact_activity
                                                                                                 │
                                                                                                 └─▶ push_config_activity ──▶ canary_reload_activity ──▶ verify_reload_activity
                                                                                                                              │
                                                                                                                              ├─ if ok ─▶ promote_config_activity
                                                                                                                              └─ if fail ─▶ rollback_config_activity + send_alert_activity
```

---

# PRIORITY ROADMAP (Concrete, with deliverables & acceptance tests)

**P0 (Weeks 0–2) — Logs working end-to-end**

* Deliverables:

  * Loki + Grafana (dev compose)
  * OTel Collector (filelog→Loki)
  * DiscoveryService basic (docker watcher)
  * LogSourceRegistry (sqlite)
  * OtelConfigBuilder (logs only)
  * AgentManager push & reload
  * Temporal workflow `collector_dynamic_reload_workflow`
* Acceptance:

  * New container → logs appear in Grafana within 30s
  * Collector / Loki health checks green

**P1 (Weeks 3–8) — Hardening & Metrics**

* Deliverables:

  * Move Loki to distributed + object store
  * Query Frontend + caching
  * LokiRuler alerts + dashboards
  * Add OTLP receiver + prometheusremotewrite pipeline
  * Auto-instrumentation wrappers & docs
  * Canary reload & rollback support
* Acceptance:

  * Metrics available in Grafana; alerts fire on synthetic tests
  * Canary reload validated, rollback works automatically

**P2 (Weeks 9–16) — Security, multi-tenant & SLOs**

* Deliverables:

  * mTLS, CertManager, per-tenant OrgID
  * Quotas & retention policies (AccessPolicyManager)
  * SLOEvaluator + Alerting pipeline
  * Chaos tests & runbooks
* Acceptance:

  * mTLS validated; tenant isolation confirmed; SLOs enforced

**P3 (Months 4–ongoing) — AI/Monetization**

* Deliverables:

  * Training data export pipeline
  * ML models (anomaly detection & recommendations)
  * Human-in-loop auto-remediation features
  * Packaging: SaaS offering + Helm chart + docs + billing hooks
* Acceptance:

  * Models trained on representative data, anomaly alerts reduce MTTD
  * Productized offering (pricing, onboarding, SLAs)

---

# DESIGN PRINCIPLES (to enforce during build)

1. **Loose coupling** — use event bus + activities; no synchronous blocking between discovery and builder.
2. **Idempotency** — all activities are retryable and idempotent.
3. **Config as Artifact** — version configs, store immutable artifacts, allow rollback.
4. **Human-in-loop** — canary + approval before global rollouts (especially for AI actions).
5. **Privacy & Compliance** — redact PII in collectors; opt-in for training exports.
6. **Observability of the observability** — metrics for every component + alerts.
7. **Product-ready modularity** — small microservices or functions for each activity so you can license/sell components.

---

# ✅ HIGH-LEVEL FLOW (Plain-English)

```
A service runs → It produces logs → Logs written to container stdout
→ OpenTelemetry Collector reads them → Normalizes & labels them
→ Sends them to Loki → Visible in Grafana

Meanwhile…

Control Plane watches for new/removed services
→ Updates registry → Rebuilds collector config → Reloads collector safely
→ Verifies pipeline health → Alerts if issues → Auto-recovers if needed
```

---

# ✅ SYSTEM FLOW (ASCII SEQUENCE)

```
┌─────────────────┐
│ Application Pods │   (no instrumentation needed)
└───────┬─────────┘
        │ stdout logs
        ▼
┌─────────────────────────┐
│ Container Log Files     │  (/var/log/containers/*.log)
└───────┬─────────────────┘
        │ filelog receiver reads files
        ▼
┌──────────────────────────────────┐
│ OpenTelemetry Collector Agent    │ (Single Collector)
│   filelog_receiver()             │
│   + attributes/resource/batch     │
│   + loki_exporter()              │
└───────┬──────────────────────────┘
        │ pushes logs
        ▼
┌────────────────┐
│     Loki       │
└───────┬────────┘
        │ query API
        ▼
┌────────────────┐
│    Grafana     │ (Explore/Alerts)
└────────────────┘
```

---

# ✅ CONTROL PLANE FLOW (DYNAMIC AUTO-DISCOVERY + CONFIG ROLLOUT)

```
       [New Service Starts]
                   │
                   ▼
      ┌────────────────────────┐
      │ DiscoveryService       │ (watches docker/k8s events)
      │ detect_service()       │
      └───────────┬────────────┘
                  │ emits event
                  ▼
      ┌────────────────────────┐
      │ LogSourceRegistry      │
      │ register_log_target()  │
      └───────────┬────────────┘
                  │ fetch registry state
                  ▼
      ┌────────────────────────┐
      │ OtelConfigBuilder      │
      │ generate_config()      │ (log pipeline only in P0)
      └───────────┬────────────┘
                  │ push config
                  ▼
      ┌────────────────────────┐
      │ AgentManager           │
      │ reload_collector()     │ (hot reload, no downtime)
      └───────────┬────────────┘
                  │ verify
                  ▼
      ┌────────────────────────┐
      │ HealthMonitor          │
      │ verify_pipeline_ok()   │
      └───────────┬────────────┘
      if fail:     │
      rollback, alert, retry
```

---

# ✅ TEMPORAL WORKFLOW LOOP (Automation)

```
LOOP forever (every 15-30s or event-triggered)
│
├─ docker_watch_activity
├─ k8s_watch_activity
│
├─ register_or_update_registry_activity
│
├─ build_config_activity
├─ validate_config_activity
│
├─ push_config_activity
├─ canary_reload_activity
│
├─ verify_reload_activity
│
└─ if failed → rollback_config_activity + send_alert_activity
```

This workflow **never stops** — it is the *brain* of the system.

---

# ✅ FUTURE FLOW (WHEN YOU LATER ADD METRICS + TRACES)

You **do not** change the system, you **only add 2 lines in config**:

```
APP → otel auto-instrument → otlp → Collector
                   │
                   ├─ metrics → Prometheus
                   └─ traces → Tempo/Jaeger
```

The **Control Plane** already knows how to:

```
generate_metrics_pipeline()
generate_traces_pipeline()
reload_collector()
verify_health()
```

So **the same workflow continues working**.

---

# ✅ WHAT MAKES THIS DESIGN CORRECT & FUTURE-PROOF

| Goal                      | Achieved By                                    |
| ------------------------- | ---------------------------------------------- |
| No code changes in apps   | Logs collected from stdout by filelog receiver |
| Single ingestion pipeline | Collector handles logs+metrics+traces          |
| Dynamic configuration     | Registry + ConfigBuilder + AgentManager        |
| Safe rollouts             | Canary reload + rollback activity              |
| Horizontal scaling        | Distributed Loki + S3/MinIO chunk backend      |
| AI-ready later            | Export pipelines in TREE F, P3                 |

---

# ✅ TL;DR (One Sentence)

> **Logs now, metrics later, traces later — all via one collector — automatically discovered, dynamically configured, hot-reloaded, monitored, and ready for AI training export.**

---

## 🎯 NEXT (Your immediate engineering move)

Pick one and I will generate it **ready to paste into your code**:

| Option  | I will deliver                                                 |
| ------- | -------------------------------------------------------------- |
| **A**   | `otel-collector.yaml` (filelog→Loki, production safe)          |
| **B**   | `collector_dynamic_reload_workflow.py` (Temporal workflow)     |
| **C**   | Full `control_plane/` repo skeleton (classes + activity stubs) |
| **D**   | Kubernetes DaemonSet version of the collector                  |
| **ALL** | Everything, ordered in correct implementation sequence         |

Reply with: **A**, **B**, **C**, **D**, or **ALL**.
Great question — this is **core architecture clarity**.
Once you understand **Control Plane vs Data Plane**, everything else becomes obvious.

---

# ✅ SHORT DEFINITION

| Plane             | What it Does                                                                  | Example Components                                                     | Your Responsibility                         |
| ----------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------------------------- |
| **Data Plane**    | Actually **collects, processes, and ships logs/metrics/traces**               | OpenTelemetry Collector, Loki, Prometheus, Tempo, Jaeger               | Reliable + fast + stable ingestion          |
| **Control Plane** | **Decides configuration**, manages discovery, orchestration, scaling, reloads | DiscoveryService, Registry, ConfigBuilder, AgentManager, HealthMonitor | Intelligence + automation + dynamic updates |

**Data Plane = “Do the work.”**
**Control Plane = “Decide *how* the work happens.”**

---

# ✅ MASTER SYSTEM TREE (Control Plane vs Data Plane)

```
START: OBSERVABILITY PLATFORM ARCHITECTURE
│
? layer = [DATA_PLANE | CONTROL_PLANE | BACKENDS]
│
├─ DATA_PLANE     ───────────────► TREE A (Log/Metrics/Traces flow)
├─ CONTROL_PLANE  ───────────────► TREE B (Automation & Management)
└─ BACKENDS       ───────────────► TREE C (Storage & Query)
```

---

## TREE A — DATA PLANE (the actual runtime pipeline)

```
DATA_PLANE
│
? signal = [logs | metrics | traces]
│
├─ logs  (current P0)
│   USE:
│     • OTelCollectorAgent
│         - filelog_receiver()
│         - attributes_processor()
│         - resource_processor()
│         - batch_processor()
│         - loki_exporter()
│   PURPOSE:
│     Move logs → from stdout → to Loki reliably.

├─ metrics (P1 later)
│   USE:
│     • OTelCollectorAgent (same agent!)
│         - otlp_receiver()
│         - metric_aggregation_processor()
│         - prometheusremotewrite_exporter()
│   PURPOSE:
│     Collect app metrics → Prometheus → dashboards → alerts.

└─ traces (P1/P2 later)
    USE:
      • OTelCollectorAgent (same agent!)
          - otlp_receiver()
          - sampling_processor()
          - tempo_exporter() or jaeger_exporter()
    PURPOSE:
      Distributed tracing → root cause analysis.

```

### DATA PLANE Key Rule

**One collector → Three pipelines**
You do **NOT** deploy different agents later.

---

## TREE B — CONTROL PLANE (automation & intelligence layer)

```
CONTROL_PLANE
│
? function = [discover | store | build_config | deploy_config | verify | heal]
│
├─ discover  (detect new services/log paths)
│   CLASS: DiscoveryService
│   METHODS:
│     - watch_docker_events()
│     - watch_k8s_api()
│     - detect_container_log_paths()

├─ store  (state tracking)
│   CLASS: LogSourceRegistry
│   METHODS:
│     - register_log_target()
│     - update_source_labels()
│     - list_sources()

├─ build_config  (collector config generation)
│   CLASS: OtelConfigBuilder
│   METHODS:
│     - generate_log_pipeline()
│     - generate_metrics_pipeline()     (later)
│     - generate_traces_pipeline()      (later)
│     - validate_config()

├─ deploy_config  (reload collector safely)
│   CLASS: AgentManager
│   METHODS:
│     - push_config_to_collector()
│     - canary_reload()
│     - rollback_config()
│     - verify_reload()

├─ verify (health & correctness)
│   CLASS: HealthMonitor
│   METHODS:
│     - check_collector_queue_backpressure()
│     - check_loki_push_errors()
│     - check_end_to_end_sample_log()

└─ heal (self-recovery control loops)
    CLASS: RepairController (optional P2)
    METHODS:
      - auto_apply_fallback_config()
      - restart_failed_components()
      - notify_on_persistent_failure()

```

### CONTROL PLANE Key Rule

**Control Plane never touches logs.
It only decides how logs should be collected.**

---

## TREE C — BACKENDS (storage & query layer)

```
BACKENDS
│
├─ Logs Store → Loki
│   - chunk_storage (S3 / MinIO)
│   - index_store (boltdb-shipper)
│   - query_frontend (parallelized search)

├─ Metrics Store → Prometheus / Mimir
│   - time-series retention
│   - alert evaluation

└─ Traces Store → Tempo / Jaeger
    - span graph storage
    - service dependency maps
```

---

# ✅ FLOW TOGETHER (COMBINED SYSTEM SEQUENCE, PRODUCTION)

```
[APP] ── stdout ──▶ [DATA PLANE: OTel Collector] ──▶ [LOKI]

[New container starts] ──▶ [CONTROL PLANE: Discovery] 
    └─▶ Registry
        └─▶ ConfigBuilder
            └─▶ AgentManager reloads collector
                └─▶ HealthMonitor verifies success
```

Data Plane **does the work**.
Control Plane **keeps it correct, updated, safe, auto-healing**.

---
