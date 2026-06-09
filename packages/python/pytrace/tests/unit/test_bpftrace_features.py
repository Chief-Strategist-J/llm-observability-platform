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
    assert "sys_enter_read" in captured.out or "Streaming events" in captured.out

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




