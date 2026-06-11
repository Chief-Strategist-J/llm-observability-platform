import pytest
from unittest.mock import MagicMock
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

def test_syscall_service_runs(capsys):
    service = SyscallService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "SLOW SYSCALL" in captured.out or "Streaming events" in captured.out


def test_malloc_service_runs(capsys):
    service = MallocService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "alloc_sizes" in captured.out or "Streaming events" in captured.out

def test_tcp_service_runs(capsys):
    service = TcpService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "tcp_send_us" in captured.out or "Streaming events" in captured.out

def test_io_service_runs(capsys):
    service = IoService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "read_lat" in captured.out or "Streaming events" in captured.out

def test_flame_service_runs(capsys):
    service = FlameService()
    service.trace(1234, duration_s=1)
    captured = capsys.readouterr()
    assert "flamegraph.svg" in captured.out

def test_sched_service_runs(capsys):
    service = SchedService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "runq_latency_us" in captured.out or "Streaming events" in captured.out

def test_pycall_service_runs(capsys):
    service = PycallService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "latency" in captured.out or "timer active" in captured.out

def test_pyframe_service_runs(capsys):
    service = PyframeService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "hotspots" in captured.out or "USDT tracer active" in captured.out

def test_pycpu_service_runs(capsys):
    service = PycpuService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Resolved" in captured.out or "CPU sampler active" in captured.out

def test_pyexcept_service_runs(capsys):
    service = PyexceptService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "EXCEPTION" in captured.out or "Exception tracer active" in captured.out

def test_pyiowait_service_runs(capsys):
    service = PyiowaitService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "BLOCKING READ" in captured.out or "Wait tracer active" in captured.out

def test_pygil_service_runs(capsys):
    service = PygilService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "GIL WAIT" in captured.out or "GIL wait tracer active" in captured.out

def test_pyleak_service_runs(capsys):
    service = PyleakService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "TOP ALLOCATORS" in captured.out or "Memory leak tracer active" in captured.out

def test_pyreq_service_runs(capsys):
    service = PyreqService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "REQ DONE" in captured.out or "Request Lifecycle tracer active" in captured.out

def test_timeline_service_runs(capsys):
    from pytrace_features.timeline.service import TimelineService
    service = TimelineService()
    service.trace(1234, duration_s=1.0)
    captured = capsys.readouterr()
    assert "handle_request" in captured.out

def test_pythread_service_runs(capsys):
    from pytrace_features.pythread.service import PythreadService
    service = PythreadService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Thread ID" in captured.out or "thread-aware tracer active" in captured.out

def test_pyasync_service_runs(capsys):
    from pytrace_features.pyasync.service import PyasyncService
    service = PyasyncService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Coroutine" in captured.out or "Async tracer active" in captured.out

def test_pyargs_service_runs(capsys):
    from pytrace_features.pyargs.service import PyargsService
    service = PyargsService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "obj=" in captured.out or "Argument tracer active" in captured.out

def test_pysyscall_service_runs(capsys):
    from pytrace_features.pysyscall.service import PysyscallService
    service = PysyscallService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "SLOW READ" in captured.out or "Syscall attribution active" in captured.out

def test_pynplus1_service_runs(capsys):
    from pytrace_features.pynplus1.service import Pynplus1Service
    service = Pynplus1Service()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "N+1 CANDIDATE" in captured.out or "detector active" in captured.out

def test_pygraph_service_runs(capsys):
    from pytrace_features.pygraph.service import PygraphService
    service = PygraphService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "handle_request" in captured.out or "Call-graph active" in captured.out

def test_pyanomaly_service_runs(capsys):
    from pytrace_features.pyanomaly.service import PyanomalyService
    service = PyanomalyService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "BASELINE" in captured.out or "Anomaly detector active" in captured.out

def test_pydash_service_runs(capsys):
    from pytrace_features.pydash.service import PydashService
    service = PydashService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "LIVE FUNCTION TRACER" in captured.out or "curses dashboard" in captured.out

def test_pysingle_service_runs(capsys):
    from pytrace_features.pysingle.service import PysingleService
    service = PysingleService()
    service.trace(1234, "handle_request")
    captured = capsys.readouterr()
    assert "handle_request" in captured.out

def test_page_faults_service_runs(capsys):
    from pytrace_features.page_faults.service import PageFaultsService
    service = PageFaultsService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "PAGE FAULT" in captured.out or "Page faults tracer active" in captured.out

def test_context_switches_service_runs(capsys):
    from pytrace_features.context_switches.service import ContextSwitchesService
    service = ContextSwitchesService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "OFF CPU" in captured.out or "Context switches tracer active" in captured.out

def test_kernel_blocked_service_runs(capsys):
    from pytrace_features.kernel_blocked.service import KernelBlockedService
    service = KernelBlockedService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "BLOCKED" in captured.out or "Kernel blocked stack tracer active" in captured.out

def test_tlb_shootdowns_service_runs(capsys):
    from pytrace_features.tlb_shootdowns.service import TlbShootdownsService
    service = TlbShootdownsService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "TLB" in captured.out or "TLB shootdowns tracer active" in captured.out

def test_irq_impact_service_runs(capsys):
    from pytrace_features.irq_impact.service import IrqImpactService
    service = IrqImpactService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "IRQ" in captured.out or "IRQ impact tracer active" in captured.out

def test_triage_service_runs(capsys):
    from pytrace_features.triage.service import TriageService
    service = TriageService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "triage" in captured.out or "Triage" in captured.out

def test_cpu_bound_service_runs(capsys):
    from pytrace_features.cpu_bound.service import CpuBoundService
    service = CpuBoundService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "CPU" in captured.out or "slow" in captured.out or "diagnostic" in captured.out

def test_io_bound_service_runs(capsys):
    from pytrace_features.io_bound.service import IoBoundService
    service = IoBoundService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "BLOCKED" in captured.out or "I/O bound" in captured.out

def test_syscall_storm_service_runs(capsys):
    from pytrace_features.syscall_storm.service import SyscallStormService
    service = SyscallStormService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "storm" in captured.out or "SYSCALLS" in captured.out

def test_deadlock_service_runs(capsys):
    from pytrace_features.deadlock.service import DeadlockService
    service = DeadlockService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "SLEEPS" in captured.out or "Deadlock" in captured.out

def test_service_map_service_runs(capsys):
    from pytrace_features.service_map.service import ServiceMapService
    service = ServiceMapService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "SERVICE" in captured.out or "Service flow" in captured.out

def test_ordered_log_service_runs(capsys):
    from pytrace_features.ordered_log.service import OrderedLogService
    service = OrderedLogService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "ENTER" in captured.out or "Ordered" in captured.out

def test_intercept_service_runs(capsys):
    from pytrace_features.intercept.service import InterceptService
    service = InterceptService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "CALLED" in captured.out or "intercept" in captured.out

def test_anomaly_trigger_service_runs(capsys):
    from pytrace_features.anomaly_trigger.service import AnomalyTriggerService
    service = AnomalyTriggerService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "EXCEPTION" in captured.out or "Anomaly trigger" in captured.out

def test_correlation_service_runs(capsys):
    from pytrace_features.correlation.service import CorrelationService
    service = CorrelationService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "SVC" in captured.out or "Correlation" in captured.out

def test_curl_perf_service_runs(capsys):
    from pytrace_features.curl_perf.service import CurlPerfService
    service = CurlPerfService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "metrics" in captured.out or "curl-perf" in captured.out

def test_jq_search_service_runs(capsys):
    from pytrace_features.jq_search.service import JqSearchService
    service = JqSearchService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "results" in captured.out or "jq-search" in captured.out

def test_awk_stats_service_runs(capsys):
    from pytrace_features.awk_stats.service import AwkStatsService
    service = AwkStatsService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "status" in captured.out or "awk-stats" in captured.out

def test_parallel_fetch_service_runs(capsys):
    from pytrace_features.parallel_fetch.service import ParallelFetchService
    service = ParallelFetchService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "concurrency" in captured.out or "parallel-fetch" in captured.out

def test_tee_branch_service_runs(capsys):
    from pytrace_features.tee_branch.service import TeeBranchService
    service = TeeBranchService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "branched" in captured.out or "tee-branch" in captured.out

def test_pipe_decouple_service_runs(capsys):
    from pytrace_features.pipe_decouple.service import PipeDecoupleService
    service = PipeDecoupleService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "FIFO" in captured.out or "pipe-decouple" in captured.out

def test_jwt_decode_service_runs(capsys):
    from pytrace_features.jwt_decode.service import JwtDecodeService
    service = JwtDecodeService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "JWT" in captured.out or "jwt-decode" in captured.out

def test_cert_check_service_runs(capsys):
    from pytrace_features.cert_check.service import CertCheckService
    service = CertCheckService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "SSL" in captured.out or "cert-check" in captured.out

def test_rate_limit_test_service_runs(capsys):
    from pytrace_features.rate_limit_test.service import RateLimitTestService
    service = RateLimitTestService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Rate" in captured.out or "rate-limit-test" in captured.out

def test_sed_mask_service_runs(capsys):
    from pytrace_features.sed_mask.service import SedMaskService
    service = SedMaskService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Masked" in captured.out or "sed-mask" in captured.out

def test_jq_schema_service_runs(capsys):
    from pytrace_features.jq_schema.service import JqSchemaService
    service = JqSchemaService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Schema" in captured.out or "jq-schema" in captured.out

def test_jq_nulls_service_runs(capsys):
    from pytrace_features.jq_nulls.service import JqNullsService
    service = JqNullsService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Null" in captured.out or "jq-nulls" in captured.out

def test_jq_null_paths_service_runs(capsys):
    from pytrace_features.jq_null_paths.service import JqNullPathsService
    service = JqNullPathsService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Null" in captured.out or "jq-null-paths" in captured.out

def test_jq_locate_key_service_runs(capsys):
    from pytrace_features.jq_locate_key.service import JqLocateKeyService
    service = JqLocateKeyService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Path" in captured.out or "jq-locate-key" in captured.out

def test_jq_key_path_service_runs(capsys):
    from pytrace_features.jq_key_path.service import JqKeyPathService
    service = JqKeyPathService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Path" in captured.out or "jq-key-path" in captured.out

def test_jq_all_keys_service_runs(capsys):
    from pytrace_features.jq_all_keys.service import JqAllKeysService
    service = JqAllKeysService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Unique" in captured.out or "jq-all-keys" in captured.out

def test_jq_leaf_paths_service_runs(capsys):
    from pytrace_features.jq_leaf_paths.service import JqLeafPathsService
    service = JqLeafPathsService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Leaf" in captured.out or "jq-leaf-paths" in captured.out

def test_jq_clean_nulls_service_runs(capsys):
    from pytrace_features.jq_clean_nulls.service import JqCleanNullsService
    service = JqCleanNullsService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Cleaned" in captured.out or "jq-clean-nulls" in captured.out

def test_jq_depth_map_service_runs(capsys):
    from pytrace_features.jq_depth_map.service import JqDepthMapService
    service = JqDepthMapService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Depth" in captured.out or "jq-depth-map" in captured.out

def test_jq_type_map_service_runs(capsys):
    from pytrace_features.jq_type_map.service import JqTypeMapService
    service = JqTypeMapService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Type" in captured.out or "jq-type-map" in captured.out

def test_jq_find_value_service_runs(capsys):
    from pytrace_features.jq_find_value.service import JqFindValueService
    service = JqFindValueService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Value" in captured.out or "jq-find-value" in captured.out

def test_jq_structural_diff_service_runs(capsys):
    from pytrace_features.jq_structural_diff.service import JqStructuralDiffService
    service = JqStructuralDiffService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Diff" in captured.out or "jq-structural-diff" in captured.out

def test_jq_extract_subtree_service_runs(capsys):
    from pytrace_features.jq_extract_subtree.service import JqExtractSubtreeService
    service = JqExtractSubtreeService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Subtree" in captured.out or "jq-extract-subtree" in captured.out

def test_jq_summary_service_runs(capsys):
    from pytrace_features.jq_summary.service import JqSummaryService
    service = JqSummaryService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Summary" in captured.out or "jq-summary" in captured.out

def test_jq_validate_schema_service_runs(capsys):
    from pytrace_features.jq_validate_schema.service import JqValidateSchemaService
    service = JqValidateSchemaService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Validation" in captured.out or "jq-validate-schema" in captured.out

def test_jq_array_schema_service_runs(capsys):
    from pytrace_features.jq_array_schema.service import JqArraySchemaService
    service = JqArraySchemaService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Discovering" in captured.out or "jq-array-schema" in captured.out

def test_jq_null_pct_service_runs(capsys):
    from pytrace_features.jq_null_pct.service import JqNullPctService
    service = JqNullPctService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Percentage" in captured.out or "jq-null-pct" in captured.out

def test_jq_non_null_leaves_service_runs(capsys):
    from pytrace_features.jq_non_null_leaves.service import JqNonNullLeavesService
    service = JqNonNullLeavesService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Non-Null" in captured.out or "jq-non-null-leaves" in captured.out

def test_jq_parent_context_service_runs(capsys):
    from pytrace_features.jq_parent_context.service import JqParentContextService
    service = JqParentContextService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Context" in captured.out or "jq-parent-context" in captured.out

def test_jq_locate_value_contains_service_runs(capsys):
    from pytrace_features.jq_locate_value_contains.service import JqLocateValueContainsService
    service = JqLocateValueContainsService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Locations" in captured.out or "jq-locate-value-contains" in captured.out

def test_jq_trace_all_keys_service_runs(capsys):
    from pytrace_features.jq_trace_all_keys.service import JqTraceAllKeysService
    service = JqTraceAllKeysService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Traced" in captured.out or "jq-trace-all-keys" in captured.out

def test_jq_heavy_objects_service_runs(capsys):
    from pytrace_features.jq_heavy_objects.service import JqHeavyObjectsService
    service = JqHeavyObjectsService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "HEAVIEST" in captured.out or "jq-heavy-objects" in captured.out

def test_jq_repeated_schema_service_runs(capsys):
    from pytrace_features.jq_repeated_schema.service import JqRepeatedSchemaService
    service = JqRepeatedSchemaService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Repeated" in captured.out or "jq-repeated-schema" in captured.out

def test_jq_common_audit_service_runs(capsys):
    from pytrace_features.jq_common_audit.service import JqCommonAuditService
    service = JqCommonAuditService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Audit" in captured.out or "jq-common-audit" in captured.out

def test_jq_schema_evolution_service_runs(capsys):
    from pytrace_features.jq_schema_evolution.service import JqSchemaEvolutionService
    service = JqSchemaEvolutionService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Evolution" in captured.out or "jq-schema-evolution" in captured.out

def test_jq_validate_fields_service_runs(capsys):
    from pytrace_features.jq_validate_fields.service import JqValidateFieldsService
    service = JqValidateFieldsService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Validation" in captured.out or "jq-validate-fields" in captured.out

def test_jq_watch_changes_service_runs(capsys):
    from pytrace_features.jq_watch_changes.service import JqWatchChangesService
    service = JqWatchChangesService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Snapshot" in captured.out or "jq-watch-changes" in captured.out


# --- DAG Engine ---

def test_dag_engine_dry_run_valid_dag(capsys):
    from pytrace_features.dag_engine.service import DagEngineService
    service = DagEngineService()
    service.run("auth: get_user:auth get_catalog:auth create_order:get_user,get_catalog", None, dry=True, max_workers=2)
    captured = capsys.readouterr()
    assert "valid" in captured.out.lower() or "DAG" in captured.out

def test_dag_engine_detects_cycle(capsys):
    from pytrace_features.dag_engine.service import DagEngineService
    import pytest
    service = DagEngineService()
    with pytest.raises(SystemExit):
        service.run("a:b b:a", None, dry=True, max_workers=2)
    captured = capsys.readouterr()
    assert "CYCLE" in captured.err or "CYCLE" in captured.out

def test_dag_engine_runs_levels(capsys):
    from pytrace_features.dag_engine.service import DagEngineService
    service = DagEngineService()
    service.run("auth: step_a:auth step_b:auth final:step_a,step_b", None, dry=False, max_workers=4)
    captured = capsys.readouterr()
    assert "completed" in captured.out.lower() or "Level" in captured.out

def test_dag_engine_empty_dag_exits(capsys):
    from pytrace_features.dag_engine.service import DagEngineService
    import pytest
    service = DagEngineService()
    with pytest.raises(SystemExit):
        service.run("", None, dry=False, max_workers=2)

def test_dag_engine_status_empty(capsys):
    from pytrace_features.dag_engine.service import DagEngineService
    service = DagEngineService()
    service.status()
    captured = capsys.readouterr()
    assert "No DAG" in captured.out or "STATUS" in captured.out


# --- Saga Orchestrator ---

def test_saga_run_all_succeed(capsys, tmp_path):
    from pytrace_features.saga_orchestrator.service import SagaOrchestratorService
    log = str(tmp_path / "saga.log")
    service = SagaOrchestratorService()
    service.run("auth,create_order,reserve_inventory", fail_at=None, log_file=log)
    captured = capsys.readouterr()
    assert "committed" in captured.out.lower() or "✓" in captured.out

def test_saga_run_rollback_on_failure(capsys, tmp_path):
    from pytrace_features.saga_orchestrator.service import SagaOrchestratorService
    log = str(tmp_path / "saga.log")
    service = SagaOrchestratorService()
    service.run("auth,create_order,reserve_inventory", fail_at="create_order", log_file=log)
    captured = capsys.readouterr()
    assert "rolled back" in captured.out.lower() or "FAILED" in captured.out

def test_saga_log_display(capsys, tmp_path):
    from pytrace_features.saga_orchestrator.service import SagaOrchestratorService
    log = str(tmp_path / "saga.log")
    service = SagaOrchestratorService()
    service.run("auth,create_order", fail_at=None, log_file=log)
    service.show_log(log)
    captured = capsys.readouterr()
    assert "SAGA" in captured.out or "auth" in captured.out

def test_saga_replay(capsys, tmp_path):
    from pytrace_features.saga_orchestrator.service import SagaOrchestratorService
    log = str(tmp_path / "saga.log")
    service = SagaOrchestratorService()
    service.run("auth,payment", fail_at=None, log_file=log)
    service.replay(log)
    captured = capsys.readouterr()
    assert "Replaying" in captured.out or "committed" in captured.out.lower()

def test_saga_log_missing_file(capsys):
    from pytrace_features.saga_orchestrator.service import SagaOrchestratorService
    service = SagaOrchestratorService()
    service.show_log("/tmp/nonexistent_pylow_saga_xyz.log")
    captured = capsys.readouterr()
    assert "No log" in captured.out

def test_net_tcp(capsys):
    from pytrace_features.net_tcp.service import NetTcpService
    service = NetTcpService()
    service.trace(1234, "https://api.example.com")
    captured = capsys.readouterr()
    assert "TCP" in captured.out

def test_chaos_run(capsys):
    from pytrace_features.chaos_run.service import ChaosRunService
    service = ChaosRunService()
    service.run("https://api.example.com", failure_rate=50)
    captured = capsys.readouterr()
    assert "CHAOS" in captured.out or "succeeded" in captured.out

def test_contract_test(capsys):
    from pytrace_features.contract_test.service import ContractTestService
    service = ContractTestService()
    service.run(1234)
    captured = capsys.readouterr()
    assert "Contract" in captured.out or "CONTRACT" in captured.out

def test_rate_limit_check(capsys):
    from pytrace_features.rate_limit_check.service import RateLimitCheckService
    service = RateLimitCheckService()
    service.trace(1234)
    captured = capsys.readouterr()
    assert "Token" in captured.out or "RateLimit" in captured.out

def test_shadow_compare(capsys):
    from pytrace_features.shadow_compare.service import ShadowCompareService
    service = ShadowCompareService()
    service.compare()
    captured = capsys.readouterr()
    assert "Shadow" in captured.out or "mismatch" in captured.out or "IDENTICAL" in captured.out

def test_load_gen(capsys):
    from pytrace_features.load_gen.service import LoadGenService
    service = LoadGenService()
    service.run("https://api.example.com", rps=2, duration=2)
    captured = capsys.readouterr()
    assert "Report" in captured.out or "Load" in captured.out

def test_webhook_mock(capsys):
    from pytrace_features.webhook_mock.service import WebhookMockService
    service = WebhookMockService()
    service.listen(port=9001, secret="whsec_abc123")
    captured = capsys.readouterr()
    assert "webhook" in captured.out.lower() or "signature" in captured.out.lower()

def test_behavior_fingerprint(capsys):
    from pytrace_features.behavior_fingerprint.service import BehaviorFingerprintService
    service = BehaviorFingerprintService()
    service.probe("https://api.example.com")
    captured = capsys.readouterr()
    assert "Fingerprint" in captured.out or "Edge Case" in captured.out

def test_mtls_diagnose(capsys):
    from pytrace_features.mtls_diagnose.service import MtlsDiagnoseService
    service = MtlsDiagnoseService()
    service.run()
    captured = capsys.readouterr()
    assert "mutual TLS" in captured.out or "mTLS" in captured.out

def test_grpc_proto(capsys):
    from pytrace_features.grpc_proto.service import GrpcProtoService
    service = GrpcProtoService()
    service.run("PaymentsService/GetPayment", "test_id")
    captured = capsys.readouterr()
    assert "Protobuf" in captured.out or "gRPC" in captured.out

def test_graphql_nplus1(capsys):
    from pytrace_features.graphql_nplus1.service import GraphqlNplus1Service
    service = GraphqlNplus1Service()
    service.run("https://api.example.com/graphql")
    captured = capsys.readouterr()
    assert "GraphQL" in captured.out or "N+1" in captured.out

def test_ws_handshake(capsys):
    from pytrace_features.ws_handshake.service import WsHandshakeService
    service = WsHandshakeService()
    service.run("wss://api.example.com/ws")
    captured = capsys.readouterr()
    assert "WebSocket" in captured.out or "handshake" in captured.out

def test_infra_fingerprint(capsys):
    from pytrace_features.infra_fingerprint.service import InfraFingerprintService
    service = InfraFingerprintService()
    service.run("https://api.example.com")
    captured = capsys.readouterr()
    assert "Fingerprint" in captured.out or "CDN" in captured.out

def test_diff_fuzz(capsys):
    from pytrace_features.diff_fuzz.service import DiffFuzzService
    service = DiffFuzzService()
    service.run("https://a.example.com", "https://b.example.com")
    captured = capsys.readouterr()
    assert "Fuzzing" in captured.out or "Divergences" in captured.out

def test_jq_reduce(capsys):
    from pytrace_features.jq_reduce.service import JqReduceService
    service = JqReduceService()
    service.run(1234)
    captured = capsys.readouterr()
    assert "reduce" in captured.out or "Totals" in captured.out

def test_jq_early_exit(capsys):
    from pytrace_features.jq_early_exit.service import JqEarlyExitService
    service = JqEarlyExitService()
    service.run(1234, 100.0)
    captured = capsys.readouterr()
    assert "exit" in captured.out.lower() or "scanned" in captured.out.lower()

def test_jq_path_find(capsys):
    from pytrace_features.jq_path_find.service import JqPathFindService
    service = JqPathFindService()
    service.run(1234, "null")
    captured = capsys.readouterr()
    assert "Paths" in captured.out or "Dotted" in captured.out

def test_jq_stream_filter(capsys):
    from pytrace_features.jq_stream_filter.service import JqStreamFilterService
    service = JqStreamFilterService()
    service.run(1234)
    captured = capsys.readouterr()
    assert "fromstream" in captured.out or "Reconstruction" in captured.out

def test_jq_flat_map(capsys):
    from pytrace_features.jq_flat_map.service import JqFlatMapService
    service = JqFlatMapService()
    service.run(1234)
    captured = capsys.readouterr()
    assert "Flat" in captured.out or "Nested" in captured.out

def test_jq_format_matrix(capsys):
    from pytrace_features.jq_format_matrix.service import JqFormatMatrixService
    service = JqFormatMatrixService()
    service.run(1234, "csv")
    captured = capsys.readouterr()
    assert "csv" in captured.out or "tsv" in captured.out or "id" in captured.out

def test_wire_grep(capsys):
    from pytrace_features.wire_grep.service import WireGrepService
    service = WireGrepService()
    service.run('{"payment_id": "pay_982"}', '"payment_id"\\s*:\\s*"([^"]+)"')
    captured = capsys.readouterr()
    assert "Match" in captured.out or "Results" in captured.out

def test_jq_foreach(capsys):
    from pytrace_features.jq_foreach.service import JqForeachService
    service = JqForeachService()
    service.run(1234)
    captured = capsys.readouterr()
    assert "foreach" in captured.out or "running_avg" in captured.out

def test_jq_custom_stdlib(capsys):
    from pytrace_features.jq_custom_stdlib.service import JqCustomStdlibService
    service = JqCustomStdlibService()
    service.run("percentile", "10,20,30,40,50")
    captured = capsys.readouterr()
    assert "Percentile" in captured.out or "Result" in captured.out

def test_pipeline_etl(capsys):
    from pytrace_features.pipeline_etl.service import PipelineEtlService
    service = PipelineEtlService()
    service.run()
    captured = capsys.readouterr()
    assert "ETL" in captured.out or "Normalize" in captured.out

def test_grep_jq_interleave(capsys):
    from pytrace_features.grep_jq_interleave.service import GrepJqInterleaveService
    service = GrepJqInterleaveService()
    service.run(10)
    captured = capsys.readouterr()
    assert "Benchmarking" in captured.out or "speedup" in captured.out

def test_jq_sql_export(capsys):
    from pytrace_features.jq_sql_export.service import JqSqlExportService
    service = JqSqlExportService()
    service.run(1234, "payments")
    captured = capsys.readouterr()
    assert "INSERT" in captured.out or "SQL" in captured.out













