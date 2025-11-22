```
DATA FLOW
└── logs_source
    └── provider (agent)
        └── processors (parser / redact / ...)
            └── exporter (loki_exporter)
                └── Loki (destination)
                    ↑
                    └── verification (query)


WORKFLOW EXECUTION TREE
START (API request)
└── Validate API request
    ├── missing required fields → FAIL_IMMEDIATE (400)
    ├── unknown/extra fields → WARN (log) → continue
    └── OK

└── Create working directory & lock (atomic)
    ├── lock exists → FAIL or wait+backoff
    ├── disk/permission error → 500
    └── OK

└── Step A: generate_config_logs.py
    ├── Validate Input (schema + ranges)
    │   ├── missing pipeline_id → ERROR
    │   ├── missing source_type → ERROR
    │   ├── missing exporter name/url → ERROR
    │   └── invalid timeout/interval → ERROR
    │
    ├── Provider selection
    │   ├── map source_type → candidates
    │   ├── if override → verify installed
    │   ├── provider binary missing → ERROR
    │   └── incompatible version → WARN/ERROR
    │
    ├── Processors validation
    │   ├── processor exists
    │   ├── plugin required missing → ERROR
    │   └── invalid regex → ERROR
    │
    ├── Exporter validation
    │   ├── supported exporter
    │   ├── url present
    │   └── preflight OPTIONS/HEAD
    │
    ├── Build canonical artifact
    │   ├── reuse cached fragments
    │   └── deterministic manifest
    │
    ├── Write artifact atomically
    │   ├── temp → fsync → mv
    │   └── write failed → ERROR
    │
    ├── Create SHA256 hash
    │   └── hashing fail → ERROR
    │
    └── Return { artifact_path, artifact_hash, manifest }

└── Step B: deploy_processor_logs.py
    ├── Load manifest (missing → ERROR)
    ├── For each processor (ordered):
    │   ├── verify template & deps
    │   ├── render config
    │   ├── atomic write (.bak + mv)
    │   ├── start runtime
    │   ├── health probe
    │   ├── partial start → rollback → ERROR
    │   └── dependency conflict → ERROR
    │
    ├── dry-run validation (schema + syntax)
    └── Return processors_manifest

└── Step C: configure_source_paths_logs.py
    ├── Read manifest.paths (empty → ERROR)
    ├── Expand globs
    │   ├── no matches → ERROR/WARN
    │   ├── too many → WARN/ERROR
    │   └── symlink loops/mount wait → retry
    │
    ├── Normalize paths
    ├── Atomic write of path config
    └── Return { paths_config_path, resolved_paths }

└── Step D: configure_source_logs.py
    ├── Validate source block (invalid → ERROR)
    ├── Select provider config location
    ├── Render provider-specific source fragment
    ├── Syntax check (if supported)
    ├── Apply config
    │   ├── file → atomic write
    │   ├── API → POST/PUT idempotent
    │   └── k8s → patch/apply
    │
    ├── permission denied → ERROR
    ├── API 4xx → ERROR
    ├── k8s race → retry
    └── Return provider_config_path or api_response

└── Step E: restart_source_logs.py
    ├── determine reload method (API / SIGHUP / rollout)
    ├── reload + health checks
    ├── reload fail → retry → rollback pipeline
    │   ├── restore previous artifact
    │   ├── restart provider
    │   └── rollback paths & processors
    │
    ├── reload success but healthfail → ERROR
    ├── crash during reload → revert backup
    └── Return { restart_status, health_check_result }

└── Step F: emit_test_event_logs.py
    ├── Build synthetic token
    ├── Inject event
    │   ├── file → atomic append
    │   ├── syslog → send framed
    │   └── http → POST with idempotency
    │
    ├── propagation wait
    ├── inject fail → retry → rollback → ERROR
    └── Return { synthetic_token, injection_result }

└── Step G: verify_event_ingestion_logs.py
    ├── build query
    ├── execute with retries
    ├── parse results
    │   ├── 0 matches → wait → retry → ERROR
    │   ├── >=1 match → validate content/labels/timestamps
    │   └── mismatch → ERROR
    │
    ├── diagnostics on failure
    │   ├── tail provider logs
    │   ├── exporter responses
    │   ├── manifests
    │   └── provider metrics
    │
    ├── remediation
    │   ├── transient → retry
    │   ├── config mismatch → FAIL
    │   └── quota issues → surface
    │
    └── Return verification result

└── FINALIZE (atomic)
    ├── success:
    │   ├── mark ACTIVE
    │   ├── persist manifest
    │   ├── emit telemetry
    │   └── return success response
    │
    └── failure:
        ├── rollback (reverse order)
        ├── persist failure state + diagnostics
        ├── emit failure telemetry
        └── return failure response
```
