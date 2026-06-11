# PYTHON_ARGCOMPLETE_OK
import argparse
import sys
try:
    import argcomplete
except ImportError:
    argcomplete = None

from pytrace_features.attach.index import AttachService
from pytrace_features.flow.index import FlowService
from pytrace_features.stitch.index import StitchService
from pytrace_features.slow.index import SlowService
from pytrace_features.diff.index import DiffService
from pytrace_features.syscall.service import SyscallService
from pytrace_features.malloc.service import MallocService
from pytrace_features.tcp.service import TcpService
from pytrace_features.io.service import IoService
from pytrace_features.flame.service import FlameService
from pytrace_features.sched.service import SchedService
from pytrace_features.pycall.service import PycallService
from pytrace_features.pyframe.service import PyframeService
from pytrace_features.pycpu.service import PycpuService
from pytrace_features.pyexcept.service import PyexceptService
from pytrace_features.pyiowait.service import PyiowaitService
from pytrace_features.pygil.service import PygilService
from pytrace_features.pyleak.service import PyleakService
from pytrace_features.pyreq.service import PyreqService
from pytrace_features.timeline.service import TimelineService
from pytrace_features.pythread.service import PythreadService
from pytrace_features.pyasync.service import PyasyncService
from pytrace_features.pyargs.service import PyargsService
from pytrace_features.pysyscall.service import PysyscallService
from pytrace_features.pynplus1.service import Pynplus1Service
from pytrace_features.pygraph.service import PygraphService
from pytrace_features.pyanomaly.service import PyanomalyService
from pytrace_features.pydash.service import PydashService
from pytrace_features.pysingle.service import PysingleService
from pytrace_features.page_faults.service import PageFaultsService
from pytrace_features.context_switches.service import ContextSwitchesService
from pytrace_features.kernel_blocked.service import KernelBlockedService
from pytrace_features.tlb_shootdowns.service import TlbShootdownsService
from pytrace_features.irq_impact.service import IrqImpactService
from pytrace_features.triage.service import TriageService
from pytrace_features.cpu_bound.service import CpuBoundService
from pytrace_features.io_bound.service import IoBoundService
from pytrace_features.syscall_storm.service import SyscallStormService
from pytrace_features.deadlock.service import DeadlockService
from pytrace_features.service_map.service import ServiceMapService
from pytrace_features.ordered_log.service import OrderedLogService
from pytrace_features.intercept.service import InterceptService
from pytrace_features.anomaly_trigger.service import AnomalyTriggerService
from pytrace_features.correlation.service import CorrelationService
from pytrace_features.curl_perf.service import CurlPerfService
from pytrace_features.jq_search.service import JqSearchService
from pytrace_features.awk_stats.service import AwkStatsService
from pytrace_features.parallel_fetch.service import ParallelFetchService
from pytrace_features.tee_branch.service import TeeBranchService
from pytrace_features.pipe_decouple.service import PipeDecoupleService
from pytrace_features.jwt_decode.service import JwtDecodeService
from pytrace_features.cert_check.service import CertCheckService
from pytrace_features.rate_limit_test.service import RateLimitTestService
from pytrace_features.sed_mask.service import SedMaskService
from pytrace_features.jq_schema.service import JqSchemaService
from pytrace_features.jq_nulls.service import JqNullsService
from pytrace_features.jq_null_paths.service import JqNullPathsService
from pytrace_features.jq_locate_key.service import JqLocateKeyService
from pytrace_features.jq_key_path.service import JqKeyPathService
from pytrace_features.jq_all_keys.service import JqAllKeysService
from pytrace_features.jq_leaf_paths.service import JqLeafPathsService
from pytrace_features.jq_clean_nulls.service import JqCleanNullsService
from pytrace_features.jq_depth_map.service import JqDepthMapService
from pytrace_features.jq_type_map.service import JqTypeMapService
from pytrace_features.jq_find_value.service import JqFindValueService
from pytrace_features.jq_structural_diff.service import JqStructuralDiffService
from pytrace_features.jq_extract_subtree.service import JqExtractSubtreeService
from pytrace_features.jq_summary.service import JqSummaryService
from pytrace_features.jq_validate_schema.service import JqValidateSchemaService
from pytrace_features.jq_array_schema.service import JqArraySchemaService
from pytrace_features.jq_null_pct.service import JqNullPctService
from pytrace_features.jq_non_null_leaves.service import JqNonNullLeavesService
from pytrace_features.jq_parent_context.service import JqParentContextService
from pytrace_features.jq_locate_value_contains.service import JqLocateValueContainsService
from pytrace_features.jq_trace_all_keys.service import JqTraceAllKeysService
from pytrace_features.jq_heavy_objects.service import JqHeavyObjectsService
from pytrace_features.jq_repeated_schema.service import JqRepeatedSchemaService
from pytrace_features.jq_common_audit.service import JqCommonAuditService
from pytrace_features.jq_schema_evolution.service import JqSchemaEvolutionService
from pytrace_features.jq_validate_fields.service import JqValidateFieldsService
from pytrace_features.jq_watch_changes.service import JqWatchChangesService
from pytrace_features.dag_engine.service import DagEngineService
from pytrace_features.saga_orchestrator.service import SagaOrchestratorService
from pytrace_features.net_tcp.service import NetTcpService
from pytrace_features.chaos_run.service import ChaosRunService
from pytrace_features.contract_test.service import ContractTestService
from pytrace_features.rate_limit_check.service import RateLimitCheckService
from pytrace_features.shadow_compare.service import ShadowCompareService
from pytrace_features.load_gen.service import LoadGenService
from pytrace_features.webhook_mock.service import WebhookMockService
from pytrace_features.behavior_fingerprint.service import BehaviorFingerprintService
from pytrace_features.mtls_diagnose.service import MtlsDiagnoseService
from pytrace_features.grpc_proto.service import GrpcProtoService
from pytrace_features.graphql_nplus1.service import GraphqlNplus1Service
from pytrace_features.ws_handshake.service import WsHandshakeService
from pytrace_features.infra_fingerprint.service import InfraFingerprintService
from pytrace_features.diff_fuzz.service import DiffFuzzService
from pytrace_features.jq_reduce.service import JqReduceService
from pytrace_features.jq_early_exit.service import JqEarlyExitService
from pytrace_features.jq_path_find.service import JqPathFindService
from pytrace_features.jq_stream_filter.service import JqStreamFilterService
from pytrace_features.jq_flat_map.service import JqFlatMapService
from pytrace_features.jq_format_matrix.service import JqFormatMatrixService
from pytrace_features.wire_grep.service import WireGrepService
from pytrace_features.jq_foreach.service import JqForeachService
from pytrace_features.jq_custom_stdlib.service import JqCustomStdlibService
from pytrace_features.pipeline_etl.service import PipelineEtlService
from pytrace_features.grep_jq_interleave.service import GrepJqInterleaveService
from pytrace_features.jq_sql_export.service import JqSqlExportService
from pytrace_features.live_pipeline.service import LivePipelineService
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter






def main() -> None:
    parser = argparse.ArgumentParser(
        description="pytrace CLI — Full system flow visibility for Python services"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Attach CLI
    attach_parser = subparsers.add_parser("attach", aliases=["listen"], help="Attach to / listen to a running Python process")
    attach_parser.add_argument("pid", type=int, help="Target process PID")

    # Flow CLI
    flow_parser = subparsers.add_parser("flow", aliases=["tree", "show"], help="Render execution flow tree")
    flow_parser.add_argument("--last", action="store_true", help="Render last collected trace")

    # Stitch CLI
    stitch_parser = subparsers.add_parser("stitch", aliases=["combine", "link"], help="Stitch distributed traces")
    stitch_parser.add_argument("--services", type=str, required=True, help="Comma-separated list of services")

    # Slow CLI
    slow_parser = subparsers.add_parser("slow", aliases=["monitor", "watch"], help="Monitor and surface slow paths")
    slow_parser.add_argument("--threshold", type=str, default="200ms", help="Latency threshold (e.g. 200ms)")
    slow_parser.add_argument("--watch", action="store_true", help="Watch continuously in background")

    # Diff CLI
    diff_parser = subparsers.add_parser("diff", aliases=["compare"], help="Compare execution flow regressions")
    diff_parser.add_argument("--before", type=str, required=True, help="Baseline release/trace ID")
    diff_parser.add_argument("--after", type=str, required=True, help="Target release/trace ID")

    # Syscall CLI
    syscall_parser = subparsers.add_parser("syscall", aliases=["system-calls"], help="Trace syscall counts and latency")
    syscall_parser.add_argument("pid", type=int, help="Target process PID")

    # Malloc CLI
    malloc_parser = subparsers.add_parser("malloc", aliases=["memory", "allocations"], help="Trace memory allocation sizes and callers")
    malloc_parser.add_argument("pid", type=int, help="Target process PID")

    # TCP CLI
    tcp_parser = subparsers.add_parser("tcp", aliases=["network"], help="Trace TCP sendmsg latency")
    tcp_parser.add_argument("pid", type=int, help="Target process PID")

    # IO CLI
    io_parser = subparsers.add_parser("io", aliases=["files", "disk"], help="Trace File I/O latency histogram")
    io_parser.add_argument("pid", type=int, help="Target process PID")

    # Flame CLI
    flame_parser = subparsers.add_parser("flame", aliases=["chart", "graph"], help="Generate user/kernel stack flame graphs")
    flame_parser.add_argument("pid", type=int, help="Target process PID")
    flame_parser.add_argument("--duration", type=int, default=5, help="Sampling duration in seconds")

    # Sched CLI
    sched_parser = subparsers.add_parser("sched", aliases=["scheduler"], help="Trace runqueue scheduler latency")
    sched_parser.add_argument("pid", type=int, help="Target process PID")

    # Pycall CLI
    pycall_parser = subparsers.add_parser("pycall", aliases=["python-calls"], help="Trace Python PyObject_Call function latencies")
    pycall_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyframe CLI
    pyframe_parser = subparsers.add_parser("pyframe", aliases=["frames"], help="Trace exact Python frames (file + line + func)")
    pyframe_parser.add_argument("pid", type=int, help="Target process PID")

    # Pycpu CLI
    pycpu_parser = subparsers.add_parser("pycpu", aliases=["cpu"], help="Profile CPU hotspots with stack trace resolving")
    pycpu_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyexcept CLI
    pyexcept_parser = subparsers.add_parser("pyexcept", aliases=["errors", "exceptions"], help="Trace raised and caught Python exceptions")
    pyexcept_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyiowait CLI
    pyiowait_parser = subparsers.add_parser("pyiowait", aliases=["blocked-io"], help="Trace blocking I/O wait calls in Python code")
    pyiowait_parser.add_argument("pid", type=int, help="Target process PID")

    # Pygil CLI
    pygil_parser = subparsers.add_parser("pygil", aliases=["gil", "locks"], help="Trace GIL lock wait contention profiles")
    pygil_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyleak CLI
    pyleak_parser = subparsers.add_parser("pyleak", aliases=["leaks"], help="Profile heap memory leak patterns")
    pyleak_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyreq CLI
    pyreq_parser = subparsers.add_parser("pyreq", aliases=["requests", "endpoints"], help="Measure end-to-end request lifecycle breakdown")
    pyreq_parser.add_argument("pid", type=int, help="Target process PID")

    # Timeline CLI
    timeline_parser = subparsers.add_parser("timeline", aliases=["chronological"], help="Trace absolute chronological timeline call graph")
    timeline_parser.add_argument("pid", type=int, help="Target process PID")
    timeline_parser.add_argument("--duration", type=float, default=5.0, help="Sampling duration in seconds")
    timeline_parser.add_argument("--threshold", type=float, default=None, help="Show only functions slower than this threshold in ms")

    # Pythread CLI
    pythread_parser = subparsers.add_parser("pythread", aliases=["threads"], help="Trace thread-aware function call timelines with self-time")
    pythread_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyasync CLI
    pyasync_parser = subparsers.add_parser("pyasync", aliases=["async"], help="Trace async await coroutine metrics")
    pyasync_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyargs CLI
    pyargs_parser = subparsers.add_parser("pyargs", aliases=["arguments"], help="Profile Python Vectorcall argument layouts")
    pyargs_parser.add_argument("pid", type=int, help="Target process PID")

    # Pysyscall CLI
    pysyscall_parser = subparsers.add_parser("pysyscall", aliases=["python-syscalls"], help="Profile syscalls attributed directly to Python code")
    pysyscall_parser.add_argument("pid", type=int, help="Target process PID")

    # Pynplus1 CLI
    pynplus1_parser = subparsers.add_parser("pynplus1", aliases=["loops", "database-loops"], help="Profile ORM queries to detect loop-driven N+1 queries")
    pynplus1_parser.add_argument("pid", type=int, help="Target process PID")

    # Pygraph CLI
    pygraph_parser = subparsers.add_parser("pygraph", aliases=["diagram"], help="Trace hierarchical call relationship graph")
    pygraph_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyanomaly CLI
    pyanomaly_parser = subparsers.add_parser("pyanomaly", aliases=["anomalies", "outliers"], help="Profile statistical baselines to catch slow anomalies")
    pyanomaly_parser.add_argument("pid", type=int, help="Target process PID")

    # Pydash CLI
    pydash_parser = subparsers.add_parser("pydash", aliases=["dashboard", "live"], help="Stream traces directly to live curses dashboard")
    pydash_parser.add_argument("pid", type=int, help="Target process PID")

    # Pysingle CLI
    pysingle_parser = subparsers.add_parser("pysingle", aliases=["single-request"], help="Trace single request / execution call tree with self time")
    pysingle_parser.add_argument("pid", type=int, help="Target process PID")
    pysingle_parser.add_argument("target_func", type=str, help="Name of entry point function to trace")
    pysingle_parser.add_argument("--tid", type=int, default=None, help="Trace only target thread ID")

    # Page Faults CLI
    page_faults_parser = subparsers.add_parser("page-faults", aliases=["faults"], help="Trace page fault hotspots")
    page_faults_parser.add_argument("pid", type=int, help="Target process PID")

    # Context Switches CLI
    context_switches_parser = subparsers.add_parser("context-switches", aliases=["preemption", "switches"], help="Trace context switch preemption latency")
    context_switches_parser.add_argument("pid", type=int, help="Target process PID")

    # Kernel Blocked CLI
    kernel_blocked_parser = subparsers.add_parser("kernel-blocked", aliases=["blocked"], help="Trace kernel stack when process blocks")
    kernel_blocked_parser.add_argument("pid", type=int, help="Target process PID")

    # TLB Shootdowns CLI
    tlb_shootdowns_parser = subparsers.add_parser("tlb-shootdowns", aliases=["tlb"], help="Trace TLB shootdowns rate and reason")
    tlb_shootdowns_parser.add_argument("pid", type=int, help="Target process PID")

    # IRQ Impact CLI
    irq_impact_parser = subparsers.add_parser("irq-impact", aliases=["irq"], help="Trace soft and hard IRQ CPU impact")
    irq_impact_parser.add_argument("pid", type=int, help="Target process PID")

    # Triage CLI
    triage_parser = subparsers.add_parser("triage", help="Run quick 10s triage profile")
    triage_parser.add_argument("pid", type=int, help="Target process PID")

    # CPU Bound CLI
    cpu_bound_parser = subparsers.add_parser("cpu-bound", help="Diagnose CPU bound hotspots")
    cpu_bound_parser.add_argument("pid", type=int, help="Target process PID")

    # I/O Bound CLI
    io_bound_parser = subparsers.add_parser("io-bound", help="Diagnose I/O bound blocked paths")
    io_bound_parser.add_argument("pid", type=int, help="Target process PID")

    # Syscall Storm CLI
    syscall_storm_parser = subparsers.add_parser("syscall-storm", help="Diagnose high frequency syscall storms")
    syscall_storm_parser.add_argument("pid", type=int, help="Target process PID")
    syscall_storm_parser.add_argument("--id", type=int, default=None, help="Filter to specific syscall ID")

    # Deadlock CLI
    deadlock_parser = subparsers.add_parser("deadlock", help="Diagnose deadlocks and thread contention locks")
    deadlock_parser.add_argument("pid", type=int, help="Target process PID")

    # Service Map CLI
    service_map_parser = subparsers.add_parser("service-map", help="Map inbound and outbound request flow")
    service_map_parser.add_argument("pid", type=int, help="Target process PID")

    # Ordered Log CLI
    ordered_log_parser = subparsers.add_parser("ordered-log", help="Output ordered log of every function call")
    ordered_log_parser.add_argument("pid", type=int, help="Target process PID")
    ordered_log_parser.add_argument("--filter-internals", action="store_true", help="Strip CPython internal bootstrap and thread files")

    # Intercept CLI
    intercept_parser = subparsers.add_parser("intercept", help="Intercept payloads at boundary functions")
    intercept_parser.add_argument("pid", type=int, help="Target process PID")
    intercept_parser.add_argument("target_func", type=str, default="process_payment", nargs="?", help="Target function to watch")

    # Anomaly Trigger CLI
    anomaly_trigger_parser = subparsers.add_parser("anomaly-trigger", help="Monitor exception trigger anomalies and early returns")
    anomaly_trigger_parser.add_argument("pid", type=int, help="Target process PID")
    anomaly_trigger_parser.add_argument("target_func", type=str, default="validate_payment", nargs="?", help="Target function to watch")

    # Correlation CLI
    correlation_parser = subparsers.add_parser("correlation", help="Trace cross-service chronological correlation")
    correlation_parser.add_argument("pid", type=int, help="Target process PID")
    correlation_parser.add_argument("service_name", type=str, default="py-service", nargs="?", help="Name of this service")

    # Curl Perf CLI
    curl_perf_parser = subparsers.add_parser("curl-perf", help="Trace curl write-out metrics and connection latency")
    curl_perf_parser.add_argument("pid", type=int, help="Target process PID")
    curl_perf_parser.add_argument("target_url", type=str, default="https://api.example.com/payments", nargs="?", help="Target URL to measure")

    # Jq Search CLI
    jq_search_parser = subparsers.add_parser("jq-search", help="Trace JSON query paths and structured field matches")
    jq_search_parser.add_argument("pid", type=int, help="Target process PID")
    jq_search_parser.add_argument("query", type=str, default="error", nargs="?", help="Field or pattern search query")

    # Awk Stats CLI
    awk_stats_parser = subparsers.add_parser("awk-stats", help="Compute statistics and percentages on tabular data stream")
    awk_stats_parser.add_argument("pid", type=int, help="Target process PID")

    # Parallel Fetch CLI
    parallel_fetch_parser = subparsers.add_parser("parallel-fetch", help="Trace parallel request pipelines with concurrency control")
    parallel_fetch_parser.add_argument("pid", type=int, help="Target process PID")
    parallel_fetch_parser.add_argument("--concurrency", type=int, default=4, help="Maximum concurrent connections")

    # Tee Branch CLI
    tee_branch_parser = subparsers.add_parser("tee-branch", help="Monitor output stream branching to files and stdout")
    tee_branch_parser.add_argument("pid", type=int, help="Target process PID")

    # Pipe Decouple CLI
    pipe_decouple_parser = subparsers.add_parser("pipe-decouple", help="Monitor named pipe FIFO decoupler status")
    pipe_decouple_parser.add_argument("pid", type=int, help="Target process PID")
    pipe_decouple_parser.add_argument("fifo_path", type=str, default="/tmp/payment_pipe", nargs="?", help="Path to named pipe FIFO file")

    # Jwt Decode CLI
    jwt_decode_parser = subparsers.add_parser("jwt-decode", help="Trace and decode JWT authorization tokens inline")
    jwt_decode_parser.add_argument("pid", type=int, help="Target process PID")

    # Cert Check CLI
    cert_check_parser = subparsers.add_parser("cert-check", help="Trace SSL/TLS handshake and certificate expiry info")
    cert_check_parser.add_argument("pid", type=int, help="Target process PID")
    cert_check_parser.add_argument("domain", type=str, default="api.example.com", nargs="?", help="Domain to check certificate expiry")

    # Rate Limit Test CLI
    rate_limit_test_parser = subparsers.add_parser("rate-limit-test", help="Diagnose API rate limit backoff and HTTP 429 status")
    rate_limit_test_parser.add_argument("pid", type=int, help="Target process PID")

    # Sed Mask CLI
    sed_mask_parser = subparsers.add_parser("sed-mask", help="Monitor stream for PII masking and character sanitizing filters")
    sed_mask_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Schema CLI
    jq_schema_parser = subparsers.add_parser("jq-schema", help="Discover structure schema shapes from streams recursively")
    jq_schema_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Nulls CLI
    jq_nulls_parser = subparsers.add_parser("jq-nulls", help="List all null fields flat representation")
    jq_nulls_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Null Paths CLI
    jq_null_paths_parser = subparsers.add_parser("jq-null-paths", help="Discover all null fields with full dotted paths")
    jq_null_paths_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Locate Key CLI
    jq_locate_key_parser = subparsers.add_parser("jq-locate-key", help="Find all paths containing target key")
    jq_locate_key_parser.add_argument("pid", type=int, help="Target process PID")
    jq_locate_key_parser.add_argument("target_key", type=str, default="salesActivities", nargs="?", help="Key to locate path of")

    # Jq Key Path CLI
    jq_key_path_parser = subparsers.add_parser("jq-key-path", help="Find path and values of matching key name")
    jq_key_path_parser.add_argument("pid", type=int, help="Target process PID")
    jq_key_path_parser.add_argument("target_key", type=str, default="name", nargs="?", help="Key name to retrieve paths and values for")

    # Jq All Keys CLI
    jq_all_keys_parser = subparsers.add_parser("jq-all-keys", help="Discover entire document vocabulary keys unique list")
    jq_all_keys_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Leaf Paths CLI
    jq_leaf_paths_parser = subparsers.add_parser("jq-leaf-paths", help="List all leaf paths and values flat map")
    jq_leaf_paths_parser.add_argument("pid", type=int, help="Target process PID")
    jq_leaf_paths_parser.add_argument("--filter-val", type=str, default="", help="Filter leaf paths having matching term")

    # Jq Clean Nulls CLI
    jq_clean_nulls_parser = subparsers.add_parser("jq-clean-nulls", help="Clean stream to filter out nulls and noise")
    jq_clean_nulls_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Depth Map CLI
    jq_depth_map_parser = subparsers.add_parser("jq-depth-map", help="Calculate structure depth per key branch")
    jq_depth_map_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Type Map CLI
    jq_type_map_parser = subparsers.add_parser("jq-type-map", help="Map every leaf path to its resolved data type")
    jq_type_map_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Find Value CLI
    jq_find_value_parser = subparsers.add_parser("jq-find-value", help="Locate path where specific value occurs")
    jq_find_value_parser.add_argument("pid", type=int, help="Target process PID")
    jq_find_value_parser.add_argument("target_val", type=str, default="gravity_admin", nargs="?", help="Value to search for")

    # Jq Structural Diff CLI
    jq_structural_diff_parser = subparsers.add_parser("jq-structural-diff", help="Diagnose schema changes and structural diff")
    jq_structural_diff_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Extract Subtree CLI
    jq_extract_subtree_parser = subparsers.add_parser("jq-extract-subtree", help="Surgically extract subtree by key")
    jq_extract_subtree_parser.add_argument("pid", type=int, help="Target process PID")
    jq_extract_subtree_parser.add_argument("target_key", type=str, default="appModulesId", nargs="?", help="Subtree key to extract")

    # Jq Summary CLI
    jq_summary_parser = subparsers.add_parser("jq-summary", help="Analyze response statistics and summary parameters")
    jq_summary_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Validate Schema CLI
    jq_validate_schema_parser = subparsers.add_parser("jq-validate-schema", help="Verify documents shape against schema template")
    jq_validate_schema_parser.add_argument("pid", type=int, help="Target process PID")
    jq_validate_schema_parser.add_argument("schema_file", type=str, default="schema.json", nargs="?", help="Path to schema JSON file")

    # Jq Array Schema CLI
    jq_array_schema_parser = subparsers.add_parser("jq-array-schema", help="Trace array schemas with sizes and item types")
    jq_array_schema_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Null Pct CLI
    jq_null_pct_parser = subparsers.add_parser("jq-null-pct", help="Track percentage of null fields per object tree")
    jq_null_pct_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Non Null Leaves CLI
    jq_non_null_leaves_parser = subparsers.add_parser("jq-non-null-leaves", help="List all filled fields flat mapping")
    jq_non_null_leaves_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Parent Context CLI
    jq_parent_context_parser = subparsers.add_parser("jq-parent-context", help="Locate keys showing parent and sibling contexts")
    jq_parent_context_parser.add_argument("pid", type=int, help="Target process PID")
    jq_parent_context_parser.add_argument("target_key", type=str, default="salesActivities", nargs="?", help="Key name to inspect siblings")

    # Jq Locate Value Contains CLI
    jq_locate_value_contains_parser = subparsers.add_parser("jq-locate-value-contains", help="Find path of values matching partial search term")
    jq_locate_value_contains_parser.add_argument("pid", type=int, help="Target process PID")
    jq_locate_value_contains_parser.add_argument("partial_val", type=str, default="Kernel", nargs="?", help="Partial string to search")

    # Jq Trace All Keys CLI
    jq_trace_all_keys_parser = subparsers.add_parser("jq-trace-all-keys", help="Trace all occurrences of a key in nested entities")
    jq_trace_all_keys_parser.add_argument("pid", type=int, help="Target process PID")
    jq_trace_all_keys_parser.add_argument("target_key", type=str, default="username", nargs="?", help="Key name to track globally")

    # Jq Heavy Objects CLI
    jq_heavy_objects_parser = subparsers.add_parser("jq-heavy-objects", help="Identify heavy nested objects with high fields count")
    jq_heavy_objects_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Repeated Schema CLI
    jq_repeated_schema_parser = subparsers.add_parser("jq-repeated-schema", help="Find repeated patterns representing audit or references")
    jq_repeated_schema_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Common Audit CLI
    jq_common_audit_parser = subparsers.add_parser("jq-common-audit", help="Find nested objects sharing the same audit trail keys")
    jq_common_audit_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Schema Evolution CLI
    jq_schema_evolution_parser = subparsers.add_parser("jq-schema-evolution", help="Compare endpoint pages to detect structural changes")
    jq_schema_evolution_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Validate Fields CLI
    jq_validate_fields_parser = subparsers.add_parser("jq-validate-fields", help="Assert mandatory fields presence on endpoint data")
    jq_validate_fields_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Watch Changes CLI
    jq_watch_changes_parser = subparsers.add_parser("jq-watch-changes", help="Track differences and field value updates over time")
    jq_watch_changes_parser.add_argument("pid", type=int, help="Target process PID")

    # DAG Engine CLI
    dag_run_parser = subparsers.add_parser("dag-run", help="Execute a DAG of steps in topological order with parallelism")
    dag_run_parser.add_argument("--dag", type=str, default="", help="DAG spec: 'step:dep1,dep2 step2:dep1' (space-separated nodes)")
    dag_run_parser.add_argument("--dag-file", type=str, default=None, help="Path to JSON file mapping step->deps list")
    dag_run_parser.add_argument("--workers", type=int, default=4, help="Max parallel workers per level (default: 4)")

    dag_dry_run_parser = subparsers.add_parser("dag-dry-run", help="Validate DAG structure and print execution levels without running")
    dag_dry_run_parser.add_argument("--dag", type=str, default="", help="DAG spec: 'step:dep1,dep2 step2:dep1'")
    dag_dry_run_parser.add_argument("--dag-file", type=str, default=None, help="Path to JSON file mapping step->deps list")
    dag_dry_run_parser.add_argument("--workers", type=int, default=4, help="Max parallel workers (default: 4)")

    dag_status_parser = subparsers.add_parser("dag-status", help="Show status of last DAG run")

    # Saga Orchestrator CLI
    saga_run_parser = subparsers.add_parser("saga-run", help="Run forward steps with automatic rollback on failure")
    saga_run_parser.add_argument("--steps", type=str, required=True, help="Comma-separated list of saga steps")
    saga_run_parser.add_argument("--fail-at", type=str, default=None, help="Inject failure at this step (for testing rollback)")
    saga_run_parser.add_argument("--log-file", type=str, default="/tmp/pylow_saga.log", help="Saga log file path (default: /tmp/pylow_saga.log)")

    saga_log_parser = subparsers.add_parser("saga-log", help="Display the saga event log")
    saga_log_parser.add_argument("--log-file", type=str, default="/tmp/pylow_saga.log", help="Saga log file path")

    saga_replay_parser = subparsers.add_parser("saga-replay", help="Replay all steps from a committed saga log")
    saga_replay_parser.add_argument("--log-file", type=str, default="/tmp/pylow_saga.log", help="Saga log file to replay")

    # TCP Connection Introspection CLI
    net_tcp_parser = subparsers.add_parser("net-tcp", help="Introspect TCP socket states, TLS sessions and handshake time splits")
    net_tcp_parser.add_argument("pid", type=int, help="Target process PID")
    net_tcp_parser.add_argument("--url", type=str, default="https://api.example.com", help="Target URL to test connects")

    # Chaos Run CLI
    chaos_run_parser = subparsers.add_parser("chaos-run", help="Run orchestrator request pipeline with random failure injection")
    chaos_run_parser.add_argument("--url", type=str, required=True, help="Target URL to test with chaos proxy")
    chaos_run_parser.add_argument("--rate", type=int, default=30, help="Failure injection rate percentage (default: 30)")

    # Contract Test CLI
    contract_test_parser = subparsers.add_parser("contract-test", help="Assert JSON payload properties against consumer contracts")
    contract_test_parser.add_argument("pid", type=int, help="Target process PID")
    contract_test_parser.add_argument("--contract", type=str, default="", help="Path to contract assertions file")

    # Rate Limit Check CLI
    rate_limit_check_parser = subparsers.add_parser("rate-limit-check", help="Trace and analyze HTTP rate limits and resets")
    rate_limit_check_parser.add_argument("pid", type=int, help="Target process PID")
    rate_limit_check_parser.add_argument("--headers-file", type=str, default="", help="Optional parsed headers file path")

    # Shadow Compare CLI
    shadow_compare_parser = subparsers.add_parser("shadow-compare", help="Compare schema and value compatibility between production and staging")
    shadow_compare_parser.add_argument("--prod-file", type=str, default="", help="Path to production response JSON")
    shadow_compare_parser.add_argument("--staging-file", type=str, default="", help="Path to staging response JSON")

    # Load Generator CLI
    load_gen_parser = subparsers.add_parser("load-gen", help="Generate constant rate load and measure latency percentiles")
    load_gen_parser.add_argument("--url", type=str, required=True, help="URL to target for load generation")
    load_gen_parser.add_argument("--rps", type=int, default=10, help="Requests per second target (default: 10)")
    load_gen_parser.add_argument("--duration", type=int, default=5, help="Duration of test in seconds (default: 5)")

    # Webhook Mock CLI
    webhook_mock_parser = subparsers.add_parser("webhook-mock", help="Start local webhook receiver and validate HMAC signatures")
    webhook_mock_parser.add_argument("--port", type=int, default=9000, help="Port to listen on (default: 9000)")
    webhook_mock_parser.add_argument("--secret", type=str, default="whsec_abc123", help="HMAC validation secret")

    # Behavior Fingerprint CLI
    behavior_fingerprint_parser = subparsers.add_parser("behavior-fingerprint", help="Probe target API endpoints for robust boundary edge cases")
    behavior_fingerprint_parser.add_argument("--url", type=str, required=True, help="Endpoint URL to probe")

    # Mtls Diagnose CLI
    mtls_diagnose_parser = subparsers.add_parser("mtls-diagnose", help="Verify and diagnose mutual TLS (mTLS) configurations and CA chains")
    mtls_diagnose_parser.add_argument("--cert", type=str, default="", help="Path to client cert PEM")
    mtls_diagnose_parser.add_argument("--key", type=str, default="", help="Path to client key PEM")

    # Grpc Proto CLI
    grpc_proto_parser = subparsers.add_parser("grpc-proto", help="Encode protobuf request to 5-byte big-endian gRPC binary frame")
    grpc_proto_parser.add_argument("--method", type=str, required=True, help="gRPC Service/Method endpoint")
    grpc_proto_parser.add_argument("--payload", type=str, required=True, help="Protobuf message content in string format")

    # Graphql Nplus1 CLI
    graphql_nplus1_parser = subparsers.add_parser("graphql-nplus1", help="Profile GraphQL schema fields for N+1 ORM overheads")
    graphql_nplus1_parser.add_argument("--url", type=str, required=True, help="GraphQL endpoint URL")

    # Ws Handshake CLI
    ws_handshake_parser = subparsers.add_parser("ws-handshake", help="Verify WebSocket HTTP upgrade headers and mask binary text frames")
    ws_handshake_parser.add_argument("--url", type=str, required=True, help="WebSocket URL to handshake (e.g. ws://...)")

    # Infra Fingerprint CLI
    infra_fingerprint_parser = subparsers.add_parser("infra-fingerprint", help="Analyze reverse proxy, WAF blocking rules, and CDN cache headers")
    infra_fingerprint_parser.add_argument("--url", type=str, required=True, help="API URL to fingerprint")

    # Diff Fuzz CLI
    diff_fuzz_parser = subparsers.add_parser("diff-fuzz", help="Drive differential fuzzing comparisons against two environments")
    diff_fuzz_parser.add_argument("--url-a", type=str, required=True, help="Target URL endpoint A")
    diff_fuzz_parser.add_argument("--url-b", type=str, required=True, help="Target URL endpoint B")

    # Jq Reduce CLI
    jq_reduce_parser = subparsers.add_parser("jq-reduce", help="Summarize arrays by group totals and running averages")
    jq_reduce_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Early Exit CLI
    jq_early_exit_parser = subparsers.add_parser("jq-early-exit", help="Perform early-exit label-breaks on large JSON payloads")
    jq_early_exit_parser.add_argument("pid", type=int, help="Target process PID")
    jq_early_exit_parser.add_argument("--threshold", type=float, default=1000.0, help="Search value threshold")

    # Jq Path Find CLI
    jq_path_find_parser = subparsers.add_parser("jq-path-find", help="Find absolute path nodes matching target types")
    jq_path_find_parser.add_argument("pid", type=int, help="Target process PID")
    jq_path_find_parser.add_argument("--type", type=str, default="null", help="Type mapping query (e.g. null, string, number)")

    # Jq Stream Filter CLI
    jq_stream_filter_parser = subparsers.add_parser("jq-stream-filter", help="Filter streams incrementally using streaming parsed paths")
    jq_stream_filter_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Flat Map CLI
    jq_flat_map_parser = subparsers.add_parser("jq-flat-map", help="Serialize nested objects to flat dotted keys and reconstruct them")
    jq_flat_map_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Format Matrix CLI
    jq_format_matrix_parser = subparsers.add_parser("jq-format-matrix", help="Convert raw JSON streams to CSV, TSV, Prometheus, and Elasticsearch formats")
    jq_format_matrix_parser.add_argument("pid", type=int, help="Target process PID")
    jq_format_matrix_parser.add_argument("--format", type=str, default="csv", help="Target output format (csv, tsv, prometheus, elasticsearch)")

    # Wire Grep CLI
    wire_grep_parser = subparsers.add_parser("wire-grep", help="Extract raw structured values directly from text using regex groups")
    wire_grep_parser.add_argument("--payload", type=str, required=True, help="Payload text to parse")
    wire_grep_parser.add_argument("--pattern", type=str, required=True, help="PCRE-styled regex match pattern")

    # Jq Foreach CLI
    jq_foreach_parser = subparsers.add_parser("jq-foreach", help="Stateful loop accumulator tracking running averages")
    jq_foreach_parser.add_argument("pid", type=int, help="Target process PID")

    # Jq Custom Stdlib CLI
    jq_custom_stdlib_parser = subparsers.add_parser("jq-custom-stdlib", help="Run JQ Custom stdlib math routines (percentile, zscore, window)")
    jq_custom_stdlib_parser.add_argument("--action", type=str, required=True, help="Helper action to run (percentile, zscore, sliding_window)")
    jq_custom_stdlib_parser.add_argument("--data", type=str, default="", help="Comma-separated values to evaluate")

    # Pipeline ETL CLI
    pipeline_etl_parser = subparsers.add_parser("pipeline-etl", help="Run data cleaning, normalization, and aggregation ETL checks")

    # GrepJq Interleave CLI
    grep_jq_interleave_parser = subparsers.add_parser("grep-jq-interleave", help="Benchmark DFA pre-filter speeds vs JQ AST parser checks")
    grep_jq_interleave_parser.add_argument("--size", type=int, default=1000, help="Benchmark dataset size")

    # Jq SQL Export CLI
    jq_sql_export_parser = subparsers.add_parser("jq-sql-export", help="Convert JSON properties to SQL INSERT statements")
    jq_sql_export_parser.add_argument("pid", type=int, help="Target process PID")
    jq_sql_export_parser.add_argument("--table", type=str, default="payments", help="SQL target table name")

    # Live Pipeline CLI Commands
    pipeline_run_parser = subparsers.add_parser("pipeline-run", help="Run the source-agnostic live transformation pipeline")

    pipeline_inject_parser = subparsers.add_parser("pipeline-inject", help="Inject a manual test record into the live pipeline")
    pipeline_inject_parser.add_argument("record", type=str, help="Raw JSON string to inject")
    pipeline_inject_parser.add_argument("--stage", type=str, default="ingest", help="Target stage FIFO (e.g. ingest, normalize)")

    pipeline_replay_parser = subparsers.add_parser("pipeline-replay", help="Replay dead letter box records into the pipeline")
    pipeline_replay_parser.add_argument("--filter", type=str, default=".", help="JQ query filter to select records to replay")
    pipeline_replay_parser.add_argument("--stage", type=str, default="normalize", help="Target stage to replay into")

    pipeline_test_stage_parser = subparsers.add_parser("pipeline-test-stage", help="Test a single stage transform without the full pipeline")
    pipeline_test_stage_parser.add_argument("record", type=str, help="Raw JSON record input")
    pipeline_test_stage_parser.add_argument("transform", type=str, help="Filename of transform (e.g. 01_normalize.jq)")

    pipeline_tap_parser = subparsers.add_parser("pipeline-tap", help="Tap and display live logs from a specific pipeline stage")
    pipeline_tap_parser.add_argument("stage", type=str, help="Stage name to tap (e.g. normalize, enrich, validate, route)")




    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()
    collector = RealTraceCollectorAdapter()
    
    cmd = args.command
    if cmd in ["attach", "listen"]:
        service = AttachService(collector)
        sys.exit(service.attach_and_collect(args.pid))
        
    elif cmd in ["flow", "tree", "show"]:
        service = FlowService()
        events = collector.get_events()
        service.render_tree(events)
        sys.exit(0)

    elif cmd in ["stitch", "combine", "link"]:
        service = StitchService()
        services = [s.strip() for s in args.services.split(",")]
        service.stitch_traces(services)
        sys.exit(0)

    elif cmd in ["slow", "monitor", "watch"]:
        service = SlowService()
        threshold_ms = 200
        if args.threshold.endswith("ms"):
            try:
                threshold_ms = int(args.threshold[:-2])
            except ValueError:
                pass
        service.monitor(threshold_ms, args.watch)
        sys.exit(0)

    elif cmd in ["diff", "compare"]:
        service = DiffService()
        service.compare(args.before, args.after)
        sys.exit(0)

    elif cmd in ["syscall", "system-calls"]:
        service = SyscallService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["malloc", "memory", "allocations"]:
        service = MallocService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["tcp", "network"]:
        service = TcpService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["io", "files", "disk"]:
        service = IoService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["flame", "chart", "graph"]:
        service = FlameService(collector)
        service.trace(args.pid, args.duration)
        sys.exit(0)

    elif cmd in ["sched", "scheduler"]:
        service = SchedService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pycall", "python-calls"]:
        service = PycallService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pyframe", "frames"]:
        service = PyframeService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pycpu", "cpu"]:
        service = PycpuService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pyexcept", "errors", "exceptions"]:
        service = PyexceptService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pyiowait", "blocked-io"]:
        service = PyiowaitService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pygil", "gil", "locks"]:
        service = PygilService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pyleak", "leaks"]:
        service = PyleakService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pyreq", "requests", "endpoints"]:
        service = PyreqService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["timeline", "chronological"]:
        service = TimelineService(collector)
        service.trace(args.pid, args.duration, args.threshold)
        sys.exit(0)

    elif cmd in ["pythread", "threads"]:
        service = PythreadService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pyasync", "async"]:
        service = PyasyncService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pyargs", "arguments"]:
        service = PyargsService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pysyscall", "python-syscalls"]:
        service = PysyscallService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pynplus1", "loops", "database-loops"]:
        service = Pynplus1Service(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pygraph", "diagram"]:
        service = PygraphService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pyanomaly", "anomalies", "outliers"]:
        service = PyanomalyService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pydash", "dashboard", "live"]:
        service = PydashService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["pysingle", "single-request"]:
        service = PysingleService(collector)
        service.trace(args.pid, args.target_func, args.tid)
        sys.exit(0)

    elif cmd in ["page-faults", "faults"]:
        service = PageFaultsService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["context-switches", "preemption", "switches"]:
        service = ContextSwitchesService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["kernel-blocked", "blocked"]:
        service = KernelBlockedService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["tlb-shootdowns", "tlb"]:
        service = TlbShootdownsService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd in ["irq-impact", "irq"]:
        service = IrqImpactService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "triage":
        service = TriageService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "cpu-bound":
        service = CpuBoundService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "io-bound":
        service = IoBoundService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "syscall-storm":
        service = SyscallStormService(collector)
        service.trace(args.pid, args.id)
        sys.exit(0)

    elif cmd == "deadlock":
        service = DeadlockService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "service-map":
        service = ServiceMapService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "ordered-log":
        service = OrderedLogService(collector)
        service.trace(args.pid, args.filter_internals)
        sys.exit(0)

    elif cmd == "intercept":
        service = InterceptService(collector)
        service.trace(args.pid, args.target_func)
        sys.exit(0)

    elif cmd == "anomaly-trigger":
        service = AnomalyTriggerService(collector)
        service.trace(args.pid, args.target_func)
        sys.exit(0)

    elif cmd == "correlation":
        service = CorrelationService(collector)
        service.trace(args.pid, args.service_name)
        sys.exit(0)

    elif cmd == "curl-perf":
        service = CurlPerfService(collector)
        service.trace(args.pid, args.target_url)
        sys.exit(0)

    elif cmd == "jq-search":
        service = JqSearchService(collector)
        service.trace(args.pid, args.query)
        sys.exit(0)

    elif cmd == "awk-stats":
        service = AwkStatsService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "parallel-fetch":
        service = ParallelFetchService(collector)
        service.trace(args.pid, args.concurrency)
        sys.exit(0)

    elif cmd == "tee-branch":
        service = TeeBranchService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "pipe-decouple":
        service = PipeDecoupleService(collector)
        service.trace(args.pid, args.fifo_path)
        sys.exit(0)

    elif cmd == "jwt-decode":
        service = JwtDecodeService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "cert-check":
        service = CertCheckService(collector)
        service.trace(args.pid, args.domain)
        sys.exit(0)

    elif cmd == "rate-limit-test":
        service = RateLimitTestService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "sed-mask":
        service = SedMaskService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-schema":
        service = JqSchemaService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-nulls":
        service = JqNullsService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-null-paths":
        service = JqNullPathsService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-locate-key":
        service = JqLocateKeyService(collector)
        service.trace(args.pid, args.target_key)
        sys.exit(0)

    elif cmd == "jq-key-path":
        service = JqKeyPathService(collector)
        service.trace(args.pid, args.target_key)
        sys.exit(0)

    elif cmd == "jq-all-keys":
        service = JqAllKeysService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-leaf-paths":
        service = JqLeafPathsService(collector)
        service.trace(args.pid, args.filter_val)
        sys.exit(0)

    elif cmd == "jq-clean-nulls":
        service = JqCleanNullsService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-depth-map":
        service = JqDepthMapService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-type-map":
        service = JqTypeMapService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-find-value":
        service = JqFindValueService(collector)
        service.trace(args.pid, args.target_val)
        sys.exit(0)

    elif cmd == "jq-structural-diff":
        service = JqStructuralDiffService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-extract-subtree":
        service = JqExtractSubtreeService(collector)
        service.trace(args.pid, args.target_key)
        sys.exit(0)

    elif cmd == "jq-summary":
        service = JqSummaryService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-validate-schema":
        service = JqValidateSchemaService(collector)
        service.trace(args.pid, args.schema_file)
        sys.exit(0)

    elif cmd == "jq-array-schema":
        service = JqArraySchemaService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-null-pct":
        service = JqNullPctService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-non-null-leaves":
        service = JqNonNullLeavesService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-parent-context":
        service = JqParentContextService(collector)
        service.trace(args.pid, args.target_key)
        sys.exit(0)

    elif cmd == "jq-locate-value-contains":
        service = JqLocateValueContainsService(collector)
        service.trace(args.pid, args.partial_val)
        sys.exit(0)

    elif cmd == "jq-trace-all-keys":
        service = JqTraceAllKeysService(collector)
        service.trace(args.pid, args.target_key)
        sys.exit(0)

    elif cmd == "jq-heavy-objects":
        service = JqHeavyObjectsService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-repeated-schema":
        service = JqRepeatedSchemaService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-common-audit":
        service = JqCommonAuditService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-schema-evolution":
        service = JqSchemaEvolutionService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-validate-fields":
        service = JqValidateFieldsService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "jq-watch-changes":
        service = JqWatchChangesService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif cmd == "dag-run":
        service = DagEngineService(collector)
        service.run(args.dag, args.dag_file, dry=False, max_workers=args.workers)
        sys.exit(0)

    elif cmd == "dag-dry-run":
        service = DagEngineService(collector)
        service.run(args.dag, args.dag_file, dry=True, max_workers=args.workers)
        sys.exit(0)

    elif cmd == "dag-status":
        service = DagEngineService(collector)
        service.status()
        sys.exit(0)

    elif cmd == "saga-run":
        service = SagaOrchestratorService(collector)
        service.run(args.steps, fail_at=args.fail_at, log_file=args.log_file)
        sys.exit(0)

    elif cmd == "saga-log":
        service = SagaOrchestratorService(collector)
        service.show_log(args.log_file)
        sys.exit(0)

    elif cmd == "saga-replay":
        service = SagaOrchestratorService(collector)
        service.replay(args.log_file)
        sys.exit(0)

    elif cmd == "net-tcp":
        service = NetTcpService(collector)
        service.trace(args.pid, args.url)
        sys.exit(0)

    elif cmd == "chaos-run":
        service = ChaosRunService(collector)
        service.run(args.url, args.rate)
        sys.exit(0)

    elif cmd == "contract-test":
        service = ContractTestService(collector)
        service.run(args.pid, args.contract)
        sys.exit(0)

    elif cmd == "rate-limit-check":
        service = RateLimitCheckService(collector)
        service.trace(args.pid, args.headers_file)
        sys.exit(0)

    elif cmd == "shadow-compare":
        service = ShadowCompareService(collector)
        service.compare(args.prod_file, args.staging_file)
        sys.exit(0)

    elif cmd == "load-gen":
        service = LoadGenService(collector)
        service.run(args.url, args.rps, args.duration)
        sys.exit(0)

    elif cmd == "webhook-mock":
        service = WebhookMockService(collector)
        service.listen(args.port, args.secret)
        sys.exit(0)

    elif cmd == "behavior-fingerprint":
        service = BehaviorFingerprintService(collector)
        service.probe(args.url)
        sys.exit(0)

    elif cmd == "mtls-diagnose":
        service = MtlsDiagnoseService(collector)
        service.run(args.cert, args.key)
        sys.exit(0)

    elif cmd == "grpc-proto":
        service = GrpcProtoService(collector)
        service.run(args.method, args.payload)
        sys.exit(0)

    elif cmd == "graphql-nplus1":
        service = GraphqlNplus1Service(collector)
        service.run(args.url)
        sys.exit(0)

    elif cmd == "ws-handshake":
        service = WsHandshakeService(collector)
        service.run(args.url)
        sys.exit(0)

    elif cmd == "infra-fingerprint":
        service = InfraFingerprintService(collector)
        service.run(args.url)
        sys.exit(0)

    elif cmd == "diff-fuzz":
        service = DiffFuzzService(collector)
        service.run(args.url_a, args.url_b)
        sys.exit(0)

    elif cmd == "jq-reduce":
        service = JqReduceService(collector)
        service.run(args.pid)
        sys.exit(0)

    elif cmd == "jq-early-exit":
        service = JqEarlyExitService(collector)
        service.run(args.pid, args.threshold)
        sys.exit(0)

    elif cmd == "jq-path-find":
        service = JqPathFindService(collector)
        service.run(args.pid, args.type)
        sys.exit(0)

    elif cmd == "jq-stream-filter":
        service = JqStreamFilterService(collector)
        service.run(args.pid)
        sys.exit(0)

    elif cmd == "jq-flat-map":
        service = JqFlatMapService(collector)
        service.run(args.pid)
        sys.exit(0)

    elif cmd == "jq-format-matrix":
        service = JqFormatMatrixService(collector)
        service.run(args.pid, args.format)
        sys.exit(0)

    elif cmd == "wire-grep":
        service = WireGrepService(collector)
        service.run(args.payload, args.pattern)
        sys.exit(0)

    elif cmd == "jq-foreach":
        service = JqForeachService(collector)
        service.run(args.pid)
        sys.exit(0)

    elif cmd == "jq-custom-stdlib":
        service = JqCustomStdlibService(collector)
        service.run(args.action, args.data)
        sys.exit(0)

    elif cmd == "pipeline-etl":
        service = PipelineEtlService(collector)
        service.run()
        sys.exit(0)

    elif cmd == "grep-jq-interleave":
        service = GrepJqInterleaveService(collector)
        service.run(args.size)
        sys.exit(0)

    elif cmd == "jq-sql-export":
        service = JqSqlExportService(collector)
        service.run(args.pid, args.table)
        sys.exit(0)

    elif cmd == "pipeline-run":
        service = LivePipelineService(collector)
        service.run()
        sys.exit(0)

    elif cmd == "pipeline-inject":
        service = LivePipelineService(collector)
        service.inject(args.record, args.stage)
        sys.exit(0)

    elif cmd == "pipeline-replay":
        service = LivePipelineService(collector)
        service.replay(args.filter, args.stage)
        sys.exit(0)

    elif cmd == "pipeline-test-stage":
        service = LivePipelineService(collector)
        service.test_stage(args.record, args.transform)
        sys.exit(0)

    elif cmd == "pipeline-tap":
        service = LivePipelineService(collector)
        service.tap(args.stage)
        sys.exit(0)




if __name__ == "__main__":
    main()
