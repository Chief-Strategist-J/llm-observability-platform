"""
pylow MCP Server
================
Exposes every pylow service as an MCP tool using the FastMCP SDK (mcp>=1.27).

Transport: Streamable-HTTP (default) — also supports stdio via `run_stdio()`.

Usage (HTTP/SSE, for MCP Inspector or Claude Desktop remote):
    python -m pylow_api.mcp.server

Usage (stdio, for Claude Desktop local config):
    python -m pylow_api.mcp.server --stdio

Environment variables:
    MCP_HOST  (default: 0.0.0.0)
    MCP_PORT  (default: 8765)
"""
from __future__ import annotations

import io
import sys
import contextlib
import argparse
from typing import Optional

from mcp.server.fastmcp import FastMCP

# ── service imports ──────────────────────────────────────────────────────────
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
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

# ── helpers ───────────────────────────────────────────────────────────────────

def _capture(fn, *args, **kwargs) -> str:
    """Redirect stdout to a string so MCP tools can return text content."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            fn(*args, **kwargs)
        except SystemExit:
            pass
    return buf.getvalue() or "(no output)"


# ── server bootstrap ──────────────────────────────────────────────────────────

mcp = FastMCP(
    name="pylow",
    instructions=(
        "pylow — zero-instrumentation observability toolkit.\n"
        "Each tool maps 1-to-1 to a pylow CLI command. All tools return plain-text "
        "diagnostic output exactly as the CLI would print. Pass pid=0 for services "
        "that don't require a live PID (they use mock/simulated data internally)."
    ),
    host="0.0.0.0",
    port=8765,
)

_col = RealTraceCollectorAdapter()

# ===========================================================================
# EBPF / KERNEL TOOLS
# ===========================================================================

@mcp.tool(description="Attach to a live Python process and collect execution traces (requires bpftrace + root).")
def attach(pid: int) -> str:
    return _capture(AttachService(_col).attach_and_collect, pid)


@mcp.tool(description="Render the last collected execution flow tree.")
def flow() -> str:
    svc = FlowService()
    return _capture(svc.render_tree, _col.get_events())


@mcp.tool(description="Stitch distributed traces across multiple services.")
def stitch(services: str) -> str:
    """services: comma-separated list e.g. 'payment-api,order-api'"""
    return _capture(StitchService().stitch_traces, [s.strip() for s in services.split(",")])


@mcp.tool(description="Surface slow execution paths above the given latency threshold.")
def slow(threshold_ms: int = 200, watch: bool = False) -> str:
    return _capture(SlowService().monitor, threshold_ms, watch)


@mcp.tool(description="Compare execution flow regressions between two releases.")
def diff(before: str, after: str) -> str:
    return _capture(DiffService().compare, before, after)


@mcp.tool(description="Trace syscall counts and latency distribution for a PID.")
def syscall(pid: int) -> str:
    return _capture(SyscallService(_col).trace, pid)


@mcp.tool(description="Trace memory allocation sizes and malloc callers for a PID.")
def malloc(pid: int) -> str:
    return _capture(MallocService(_col).trace, pid)


@mcp.tool(description="Trace TCP sendmsg latency for a PID.")
def tcp(pid: int) -> str:
    return _capture(TcpService(_col).trace, pid)


@mcp.tool(description="Trace file I/O latency histogram for a PID.")
def io_trace(pid: int) -> str:
    return _capture(IoService(_col).trace, pid)


@mcp.tool(description="Generate user+kernel stack flame graph for a PID.")
def flame(pid: int, duration: int = 5) -> str:
    return _capture(FlameService(_col).trace, pid, duration)


@mcp.tool(description="Trace runqueue scheduler latency for a PID.")
def sched(pid: int) -> str:
    return _capture(SchedService(_col).trace, pid)


@mcp.tool(description="Trace Python PyObject_Call latencies for a PID.")
def pycall(pid: int) -> str:
    return _capture(PycallService(_col).trace, pid)


@mcp.tool(description="Trace exact Python frames (file + line + func) for a PID.")
def pyframe(pid: int) -> str:
    return _capture(PyframeService(_col).trace, pid)


@mcp.tool(description="Profile CPU hotspots with stack trace resolving for a PID.")
def pycpu(pid: int) -> str:
    return _capture(PycpuService(_col).trace, pid)


@mcp.tool(description="Trace raised and caught Python exceptions for a PID.")
def pyexcept(pid: int) -> str:
    return _capture(PyexceptService(_col).trace, pid)


@mcp.tool(description="Trace blocking I/O wait calls in Python code for a PID.")
def pyiowait(pid: int) -> str:
    return _capture(PyiowaitService(_col).trace, pid)


@mcp.tool(description="Trace GIL lock wait contention profiles for a PID.")
def pygil(pid: int) -> str:
    return _capture(PygilService(_col).trace, pid)


@mcp.tool(description="Profile heap memory leak patterns for a PID.")
def pyleak(pid: int) -> str:
    return _capture(PyleakService(_col).trace, pid)


@mcp.tool(description="Measure end-to-end request lifecycle breakdown for a PID.")
def pyreq(pid: int) -> str:
    return _capture(PyreqService(_col).trace, pid)


@mcp.tool(description="Chronological timeline call graph for a PID.")
def timeline(pid: int, duration: float = 5.0, threshold: Optional[float] = None) -> str:
    return _capture(TimelineService(_col).trace, pid, duration, threshold)


@mcp.tool(description="Thread-aware function call timelines with self-time for a PID.")
def pythread(pid: int) -> str:
    return _capture(PythreadService(_col).trace, pid)


@mcp.tool(description="Trace async/await coroutine metrics for a PID.")
def pyasync(pid: int) -> str:
    return _capture(PyasyncService(_col).trace, pid)


@mcp.tool(description="Profile Python Vectorcall argument layouts for a PID.")
def pyargs(pid: int) -> str:
    return _capture(PyargsService(_col).trace, pid)


@mcp.tool(description="Profile syscalls attributed directly to Python code for a PID.")
def pysyscall(pid: int) -> str:
    return _capture(PysyscallService(_col).trace, pid)


@mcp.tool(description="Detect loop-driven N+1 ORM queries for a PID.")
def pynplus1(pid: int) -> str:
    return _capture(Pynplus1Service(_col).trace, pid)


@mcp.tool(description="Trace hierarchical call relationship graph for a PID.")
def pygraph(pid: int) -> str:
    return _capture(PygraphService(_col).trace, pid)


@mcp.tool(description="Profile statistical baselines to catch slow anomalies for a PID.")
def pyanomaly(pid: int) -> str:
    return _capture(PyanomalyService(_col).trace, pid)


@mcp.tool(description="Stream traces to live curses dashboard for a PID.")
def pydash(pid: int) -> str:
    return _capture(PydashService(_col).trace, pid)


@mcp.tool(description="Trace a single request/execution call tree with self-time.")
def pysingle(pid: int, target_func: str, tid: Optional[int] = None) -> str:
    return _capture(PysingleService(_col).trace, pid, target_func, tid)


@mcp.tool(description="Trace page fault hotspots for a PID.")
def page_faults(pid: int) -> str:
    return _capture(PageFaultsService(_col).trace, pid)


@mcp.tool(description="Trace context switch preemption latency for a PID.")
def context_switches(pid: int) -> str:
    return _capture(ContextSwitchesService(_col).trace, pid)


@mcp.tool(description="Trace kernel stack when a process blocks for a PID.")
def kernel_blocked(pid: int) -> str:
    return _capture(KernelBlockedService(_col).trace, pid)


@mcp.tool(description="Trace TLB shootdowns rate and reason for a PID.")
def tlb_shootdowns(pid: int) -> str:
    return _capture(TlbShootdownsService(_col).trace, pid)


@mcp.tool(description="Trace soft and hard IRQ CPU impact for a PID.")
def irq_impact(pid: int) -> str:
    return _capture(IrqImpactService(_col).trace, pid)


@mcp.tool(description="Run a quick 10-second triage profile for a PID.")
def triage(pid: int) -> str:
    return _capture(TriageService(_col).trace, pid)


@mcp.tool(description="Diagnose CPU bound hotspots for a PID.")
def cpu_bound(pid: int) -> str:
    return _capture(CpuBoundService(_col).trace, pid)


@mcp.tool(description="Diagnose I/O bound blocked paths for a PID.")
def io_bound(pid: int) -> str:
    return _capture(IoBoundService(_col).trace, pid)


@mcp.tool(description="Diagnose high-frequency syscall storms for a PID.")
def syscall_storm(pid: int, syscall_id: Optional[int] = None) -> str:
    return _capture(SyscallStormService(_col).trace, pid, syscall_id)


@mcp.tool(description="Diagnose deadlocks and thread contention locks for a PID.")
def deadlock(pid: int) -> str:
    return _capture(DeadlockService(_col).trace, pid)


@mcp.tool(description="Map inbound and outbound request flow for a PID.")
def service_map(pid: int) -> str:
    return _capture(ServiceMapService(_col).trace, pid)


@mcp.tool(description="Output ordered log of every function call for a PID.")
def ordered_log(pid: int, filter_internals: bool = False) -> str:
    return _capture(OrderedLogService(_col).trace, pid, filter_internals)


@mcp.tool(description="Intercept payloads at a boundary function for a PID.")
def intercept(pid: int, target_func: str = "process_payment") -> str:
    return _capture(InterceptService(_col).trace, pid, target_func)


@mcp.tool(description="Monitor exception-trigger anomalies and early returns at a function.")
def anomaly_trigger(pid: int, target_func: str = "validate_payment") -> str:
    return _capture(AnomalyTriggerService(_col).trace, pid, target_func)


@mcp.tool(description="Trace cross-service chronological correlation for a PID.")
def correlation(pid: int, service_name: str = "py-service") -> str:
    return _capture(CorrelationService(_col).trace, pid, service_name)


# ===========================================================================
# HTTP / NETWORK TOOLS
# ===========================================================================

@mcp.tool(description="Trace curl write-out timing metrics split by DNS/TCP/TLS/TTFB.")
def curl_perf(pid: int, target_url: str = "https://api.example.com/payments") -> str:
    return _capture(CurlPerfService(_col).trace, pid, target_url)


@mcp.tool(description="Introspect live TCP socket states, TLS sessions and handshake time splits.")
def net_tcp(pid: int, url: str = "https://api.example.com") -> str:
    return _capture(NetTcpService(_col).trace, pid, url)


@mcp.tool(description="Run chaos injection at a given failure rate percentage against a URL.")
def chaos_run(url: str, rate: int = 30) -> str:
    return _capture(ChaosRunService(_col).run, url, rate)


@mcp.tool(description="Assert JSON payload properties against consumer contract assertions.")
def contract_test(pid: int, contract: str = "") -> str:
    return _capture(ContractTestService(_col).run, pid, contract)


@mcp.tool(description="Trace and analyze HTTP rate-limit headers and resets.")
def rate_limit_check(pid: int, headers_file: str = "") -> str:
    return _capture(RateLimitCheckService(_col).trace, pid, headers_file)


@mcp.tool(description="Compare schema and value compatibility between production and staging responses.")
def shadow_compare(prod_file: str, staging_file: str) -> str:
    return _capture(ShadowCompareService(_col).compare, prod_file, staging_file)


@mcp.tool(description="Generate constant-rate load and measure latency percentiles for a URL.")
def load_gen(url: str, rps: int = 10, duration: int = 5) -> str:
    return _capture(LoadGenService(_col).run, url, rps, duration)


@mcp.tool(description="Start a local webhook receiver and validate HMAC signatures.")
def webhook_mock(port: int = 9000, secret: str = "whsec_abc123") -> str:
    return _capture(WebhookMockService(_col).listen, port, secret)


@mcp.tool(description="Probe target API endpoints for robust boundary edge cases (WAF/CDN fingerprinting).")
def behavior_fingerprint(url: str) -> str:
    return _capture(BehaviorFingerprintService(_col).probe, url)


@mcp.tool(description="Verify and diagnose mutual TLS (mTLS) configurations and CA chains.")
def mtls_diagnose(cert: str = "", key: str = "") -> str:
    return _capture(MtlsDiagnoseService(_col).run, cert, key)


@mcp.tool(description="Encode a protobuf request to a 5-byte big-endian gRPC binary frame.")
def grpc_proto(method: str, payload: str) -> str:
    return _capture(GrpcProtoService(_col).run, method, payload)


@mcp.tool(description="Profile GraphQL schema fields for N+1 ORM overheads via introspection.")
def graphql_nplus1(url: str) -> str:
    return _capture(GraphqlNplus1Service(_col).run, url)


@mcp.tool(description="Verify WebSocket HTTP upgrade headers and decode masked binary frames.")
def ws_handshake(url: str) -> str:
    return _capture(WsHandshakeService(_col).run, url)


@mcp.tool(description="Analyze reverse-proxy, WAF blocking rules, and CDN cache headers for a URL.")
def infra_fingerprint(url: str) -> str:
    return _capture(InfraFingerprintService(_col).run, url)


@mcp.tool(description="Drive differential fuzzing comparisons against two environment endpoints.")
def diff_fuzz(url_a: str, url_b: str) -> str:
    return _capture(DiffFuzzService(_col).run, url_a, url_b)


@mcp.tool(description="Run parallel request pipelines with concurrency control for a PID.")
def parallel_fetch(pid: int, concurrency: int = 4) -> str:
    return _capture(ParallelFetchService(_col).trace, pid, concurrency)


@mcp.tool(description="Monitor output stream branching to files and stdout for a PID.")
def tee_branch(pid: int) -> str:
    return _capture(TeeBranchService(_col).trace, pid)


@mcp.tool(description="Monitor named-pipe FIFO decoupler status for a PID.")
def pipe_decouple(pid: int, fifo_path: str = "/tmp/payment_pipe") -> str:
    return _capture(PipeDecoupleService(_col).trace, pid, fifo_path)


@mcp.tool(description="Trace and decode JWT authorization tokens inline for a PID.")
def jwt_decode(pid: int) -> str:
    return _capture(JwtDecodeService(_col).trace, pid)


@mcp.tool(description="Trace SSL/TLS handshake and certificate expiry info for a domain.")
def cert_check(pid: int, domain: str = "api.example.com") -> str:
    return _capture(CertCheckService(_col).trace, pid, domain)


@mcp.tool(description="Diagnose API rate-limit backoff and HTTP 429 responses for a PID.")
def rate_limit_test(pid: int) -> str:
    return _capture(RateLimitTestService(_col).trace, pid)


@mcp.tool(description="Monitor stream for PII masking and character sanitizing filters for a PID.")
def sed_mask(pid: int) -> str:
    return _capture(SedMaskService(_col).trace, pid)


# ===========================================================================
# JQ / JSON ANALYSIS TOOLS
# ===========================================================================

@mcp.tool(description="Trace JSON query paths and structured field matches for a PID.")
def jq_search(pid: int, query: str = "error") -> str:
    return _capture(JqSearchService(_col).trace, pid, query)


@mcp.tool(description="Compute statistics and percentages on a tabular data stream for a PID.")
def awk_stats(pid: int) -> str:
    return _capture(AwkStatsService(_col).trace, pid)


@mcp.tool(description="Discover structure schema shapes from streams recursively for a PID.")
def jq_schema(pid: int) -> str:
    return _capture(JqSchemaService(_col).trace, pid)


@mcp.tool(description="List all null fields in flat representation for a PID.")
def jq_nulls(pid: int) -> str:
    return _capture(JqNullsService(_col).trace, pid)


@mcp.tool(description="Discover all null fields with full dotted paths for a PID.")
def jq_null_paths(pid: int) -> str:
    return _capture(JqNullPathsService(_col).trace, pid)


@mcp.tool(description="Find all paths containing a target key in JSON for a PID.")
def jq_locate_key(pid: int, target_key: str = "salesActivities") -> str:
    return _capture(JqLocateKeyService(_col).trace, pid, target_key)


@mcp.tool(description="Find path and values of a matching key name for a PID.")
def jq_key_path(pid: int, target_key: str = "name") -> str:
    return _capture(JqKeyPathService(_col).trace, pid, target_key)


@mcp.tool(description="Discover entire document vocabulary (unique key list) for a PID.")
def jq_all_keys(pid: int) -> str:
    return _capture(JqAllKeysService(_col).trace, pid)


@mcp.tool(description="List all leaf paths and values in flat map for a PID.")
def jq_leaf_paths(pid: int, filter_val: str = "") -> str:
    return _capture(JqLeafPathsService(_col).trace, pid, filter_val)


@mcp.tool(description="Clean stream to filter out nulls and noise for a PID.")
def jq_clean_nulls(pid: int) -> str:
    return _capture(JqCleanNullsService(_col).trace, pid)


@mcp.tool(description="Calculate structure depth per key branch for a PID.")
def jq_depth_map(pid: int) -> str:
    return _capture(JqDepthMapService(_col).trace, pid)


@mcp.tool(description="Map every leaf path to its resolved data type for a PID.")
def jq_type_map(pid: int) -> str:
    return _capture(JqTypeMapService(_col).trace, pid)


@mcp.tool(description="Locate the path where a specific value occurs for a PID.")
def jq_find_value(pid: int, target_val: str = "gravity_admin") -> str:
    return _capture(JqFindValueService(_col).trace, pid, target_val)


@mcp.tool(description="Diagnose schema changes and structural diff for a PID.")
def jq_structural_diff(pid: int) -> str:
    return _capture(JqStructuralDiffService(_col).trace, pid)


@mcp.tool(description="Surgically extract a subtree by key for a PID.")
def jq_extract_subtree(pid: int, target_key: str = "appModulesId") -> str:
    return _capture(JqExtractSubtreeService(_col).trace, pid, target_key)


@mcp.tool(description="Analyze response statistics and summary parameters for a PID.")
def jq_summary(pid: int) -> str:
    return _capture(JqSummaryService(_col).trace, pid)


@mcp.tool(description="Verify document shape against a schema template file.")
def jq_validate_schema(pid: int, schema_file: str = "schema.json") -> str:
    return _capture(JqValidateSchemaService(_col).trace, pid, schema_file)


@mcp.tool(description="Trace array schemas with sizes and item types for a PID.")
def jq_array_schema(pid: int) -> str:
    return _capture(JqArraySchemaService(_col).trace, pid)


@mcp.tool(description="Track percentage of null fields per object tree for a PID.")
def jq_null_pct(pid: int) -> str:
    return _capture(JqNullPctService(_col).trace, pid)


@mcp.tool(description="List all filled (non-null) fields in flat mapping for a PID.")
def jq_non_null_leaves(pid: int) -> str:
    return _capture(JqNonNullLeavesService(_col).trace, pid)


@mcp.tool(description="Locate keys showing parent and sibling contexts for a PID.")
def jq_parent_context(pid: int, target_key: str = "salesActivities") -> str:
    return _capture(JqParentContextService(_col).trace, pid, target_key)


@mcp.tool(description="Find path of values matching a partial search term for a PID.")
def jq_locate_value_contains(pid: int, partial_val: str = "Kernel") -> str:
    return _capture(JqLocateValueContainsService(_col).trace, pid, partial_val)


@mcp.tool(description="Trace all occurrences of a key in nested entities for a PID.")
def jq_trace_all_keys(pid: int, target_key: str = "username") -> str:
    return _capture(JqTraceAllKeysService(_col).trace, pid, target_key)


@mcp.tool(description="Identify heavy nested objects with high field counts for a PID.")
def jq_heavy_objects(pid: int) -> str:
    return _capture(JqHeavyObjectsService(_col).trace, pid)


@mcp.tool(description="Find repeated schema patterns representing audit or references for a PID.")
def jq_repeated_schema(pid: int) -> str:
    return _capture(JqRepeatedSchemaService(_col).trace, pid)


@mcp.tool(description="Find nested objects sharing the same audit trail keys for a PID.")
def jq_common_audit(pid: int) -> str:
    return _capture(JqCommonAuditService(_col).trace, pid)


@mcp.tool(description="Compare endpoint pages to detect structural changes for a PID.")
def jq_schema_evolution(pid: int) -> str:
    return _capture(JqSchemaEvolutionService(_col).trace, pid)


@mcp.tool(description="Assert mandatory fields presence on endpoint data for a PID.")
def jq_validate_fields(pid: int) -> str:
    return _capture(JqValidateFieldsService(_col).trace, pid)


@mcp.tool(description="Track differences and field value updates over time for a PID.")
def jq_watch_changes(pid: int) -> str:
    return _capture(JqWatchChangesService(_col).trace, pid)


@mcp.tool(description="Summarize arrays by group totals and running averages for a PID.")
def jq_reduce(pid: int) -> str:
    return _capture(JqReduceService(_col).run, pid)


@mcp.tool(description="Perform early-exit label-breaks on large JSON payloads above a threshold.")
def jq_early_exit(pid: int, threshold: float = 1000.0) -> str:
    return _capture(JqEarlyExitService(_col).run, pid, threshold)


@mcp.tool(description="Find absolute path nodes matching a target type (null/string/number).")
def jq_path_find(pid: int, target_type: str = "null") -> str:
    return _capture(JqPathFindService(_col).run, pid, target_type)


@mcp.tool(description="Filter streams incrementally using streaming parsed paths for a PID.")
def jq_stream_filter(pid: int) -> str:
    return _capture(JqStreamFilterService(_col).run, pid)


@mcp.tool(description="Serialize nested objects to flat dotted keys and reconstruct them for a PID.")
def jq_flat_map(pid: int) -> str:
    return _capture(JqFlatMapService(_col).run, pid)


@mcp.tool(description="Convert raw JSON streams to CSV, TSV, Prometheus, or Elasticsearch format.")
def jq_format_matrix(pid: int, format: str = "csv") -> str:
    return _capture(JqFormatMatrixService(_col).run, pid, format)


@mcp.tool(description="Stateful loop accumulator tracking running averages for a PID.")
def jq_foreach(pid: int) -> str:
    return _capture(JqForeachService(_col).run, pid)


@mcp.tool(description="Run JQ custom stdlib math routines: percentile, zscore, sliding_window.")
def jq_custom_stdlib(action: str, data: str = "") -> str:
    """action: one of 'percentile', 'zscore', 'sliding_window'. data: comma-separated floats."""
    return _capture(JqCustomStdlibService(_col).run, action, data)


@mcp.tool(description="Convert JSON properties to SQL INSERT statements for a PID.")
def jq_sql_export(pid: int, table: str = "payments") -> str:
    return _capture(JqSqlExportService(_col).run, pid, table)


# ===========================================================================
# PIPELINE / DATA TOOLS
# ===========================================================================

@mcp.tool(description="Extract raw structured values from text using PCRE-style regex groups.")
def wire_grep(payload: str, pattern: str) -> str:
    return _capture(WireGrepService(_col).run, payload, pattern)


@mcp.tool(description="Run multi-stage ETL pipeline: Extract, Normalize, Validate, Aggregate.")
def pipeline_etl() -> str:
    return _capture(PipelineEtlService(_col).run)


@mcp.tool(description="Benchmark DFA pre-filter (grep) speed vs JQ AST parser on a dataset.")
def grep_jq_interleave(size: int = 1000) -> str:
    return _capture(GrepJqInterleaveService(_col).run, size)


# ===========================================================================
# DAG / SAGA ORCHESTRATION TOOLS
# ===========================================================================

@mcp.tool(description="Execute a DAG of steps in topological order with parallel workers.")
def dag_run(dag: str = "", dag_file: Optional[str] = None, workers: int = 4) -> str:
    """dag: 'step:dep1,dep2 step2:dep1' space-separated. Or provide a JSON dag_file path."""
    return _capture(DagEngineService(_col).run, dag, dag_file, False, workers)


@mcp.tool(description="Validate DAG structure and print execution levels without running.")
def dag_dry_run(dag: str = "", dag_file: Optional[str] = None, workers: int = 4) -> str:
    return _capture(DagEngineService(_col).run, dag, dag_file, True, workers)


@mcp.tool(description="Show status of the last DAG run.")
def dag_status() -> str:
    return _capture(DagEngineService(_col).status)


@mcp.tool(description="Run forward saga steps with automatic rollback on failure.")
def saga_run(steps: str, fail_at: Optional[str] = None, log_file: str = "/tmp/pylow_saga.log") -> str:
    """steps: comma-separated list of saga step names."""
    return _capture(SagaOrchestratorService(_col).run, steps, fail_at, log_file)


@mcp.tool(description="Display the saga event log from a log file.")
def saga_log(log_file: str = "/tmp/pylow_saga.log") -> str:
    return _capture(SagaOrchestratorService(_col).show_log, log_file)


@mcp.tool(description="Replay all steps from a committed saga log file.")
def saga_replay(log_file: str = "/tmp/pylow_saga.log") -> str:
    return _capture(SagaOrchestratorService(_col).replay, log_file)


# ===========================================================================
# PROMPTS
# ===========================================================================

@mcp.prompt()
def diagnose_performance(pid: int) -> str:
    """Prompt template for analyzing latency spikes, CPU hotspots, or slow requests."""
    return (
        f"You are investigating a latency anomaly or high CPU usage in Python process PID {pid}.\n"
        "Please follow these steps to locate the bottleneck:\n"
        f"1. Run `pycpu(pid={pid})` to profile CPU stack traces and find hotspot methods.\n"
        f"2. Run `slow(threshold_ms=200)` to see which operations cross latency boundaries.\n"
        f"3. Run `syscall(pid={pid})` to check if syscall overhead (e.g. read/write/epoll) is dragging down execution.\n"
        f"4. Run `pygil(pid={pid})` to check if lock contention or thread synchronization is blocking execution."
    )


@mcp.prompt()
def troubleshoot_memory(pid: int) -> str:
    """Prompt template for memory leaks, allocation spikes, or high RAM usage."""
    return (
        f"You are diagnosing high memory usage or a memory leak in Python process PID {pid}.\n"
        "Follow this diagnostic runbook:\n"
        f"1. Run `malloc(pid={pid})` to view live memory allocation sizes and traceback callers.\n"
        f"2. Run `pyleak(pid={pid})` to search for leak patterns and identify objects that aren't being garbage collected.\n"
        f"3. Run `page_faults(pid={pid})` to determine if frequent swapping or page re-allocations are slowing down process heap expansion."
    )


# ===========================================================================
# ENTRY POINTS
# ===========================================================================

def run_http() -> None:
    """Start the MCP server over Streamable-HTTP (default transport)."""
    import os
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8765"))
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.run(transport="streamable-http")


def run_stdio() -> None:
    """Start the MCP server over stdio (for Claude Desktop local config)."""
    mcp.run(transport="stdio")


def main() -> None:
    ap = argparse.ArgumentParser(description="pylow MCP server")
    ap.add_argument(
        "--stdio",
        action="store_true",
        help="Run over stdio transport instead of HTTP (use with Claude Desktop)",
    )
    args = ap.parse_args()
    if args.stdio:
        run_stdio()
    else:
        run_http()


if __name__ == "__main__":
    main()
