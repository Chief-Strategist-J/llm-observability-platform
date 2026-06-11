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






