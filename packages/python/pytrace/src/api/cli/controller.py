import argparse
import sys
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
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

def main() -> None:
    parser = argparse.ArgumentParser(
        description="pytrace CLI — Full system flow visibility for Python services"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Attach CLI
    attach_parser = subparsers.add_parser("attach", help="Attach to a running Python process")
    attach_parser.add_argument("pid", type=int, help="Target process PID")

    # Flow CLI
    flow_parser = subparsers.add_parser("flow", help="Render execution flow tree")
    flow_parser.add_argument("--last", action="store_true", help="Render last collected trace")

    # Stitch CLI
    stitch_parser = subparsers.add_parser("stitch", help="Stitch distributed traces")
    stitch_parser.add_argument("--services", type=str, required=True, help="Comma-separated list of services")

    # Slow CLI
    slow_parser = subparsers.add_parser("slow", help="Monitor and surface slow paths")
    slow_parser.add_argument("--threshold", type=str, default="200ms", help="Latency threshold (e.g. 200ms)")
    slow_parser.add_argument("--watch", action="store_true", help="Watch continuously in background")

    # Diff CLI
    diff_parser = subparsers.add_parser("diff", help="Compare execution flow regressions")
    diff_parser.add_argument("--before", type=str, required=True, help="Baseline release/trace ID")
    diff_parser.add_argument("--after", type=str, required=True, help="Target release/trace ID")

    # Syscall CLI
    syscall_parser = subparsers.add_parser("syscall", help="Trace syscall counts and latency")
    syscall_parser.add_argument("pid", type=int, help="Target process PID")

    # Malloc CLI
    malloc_parser = subparsers.add_parser("malloc", help="Trace memory allocation sizes and callers")
    malloc_parser.add_argument("pid", type=int, help="Target process PID")

    # TCP CLI
    tcp_parser = subparsers.add_parser("tcp", help="Trace TCP sendmsg latency")
    tcp_parser.add_argument("pid", type=int, help="Target process PID")

    # IO CLI
    io_parser = subparsers.add_parser("io", help="Trace File I/O latency histogram")
    io_parser.add_argument("pid", type=int, help="Target process PID")

    # Flame CLI
    flame_parser = subparsers.add_parser("flame", help="Generate user/kernel stack flame graphs")
    flame_parser.add_argument("pid", type=int, help="Target process PID")
    flame_parser.add_argument("--duration", type=int, default=5, help="Sampling duration in seconds")

    # Sched CLI
    sched_parser = subparsers.add_parser("sched", help="Trace runqueue scheduler latency")
    sched_parser.add_argument("pid", type=int, help="Target process PID")

    # Pycall CLI
    pycall_parser = subparsers.add_parser("pycall", help="Trace Python PyObject_Call function latencies")
    pycall_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyframe CLI
    pyframe_parser = subparsers.add_parser("pyframe", help="Trace exact Python frames (file + line + func)")
    pyframe_parser.add_argument("pid", type=int, help="Target process PID")

    # Pycpu CLI
    pycpu_parser = subparsers.add_parser("pycpu", help="Profile CPU hotspots with stack trace resolving")
    pycpu_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyexcept CLI
    pyexcept_parser = subparsers.add_parser("pyexcept", help="Trace raised and caught Python exceptions")
    pyexcept_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyiowait CLI
    pyiowait_parser = subparsers.add_parser("pyiowait", help="Trace blocking I/O wait calls in Python code")
    pyiowait_parser.add_argument("pid", type=int, help="Target process PID")

    # Pygil CLI
    pygil_parser = subparsers.add_parser("pygil", help="Trace GIL lock wait contention profiles")
    pygil_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyleak CLI
    pyleak_parser = subparsers.add_parser("pyleak", help="Profile heap memory leak patterns")
    pyleak_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyreq CLI
    pyreq_parser = subparsers.add_parser("pyreq", help="Measure end-to-end request lifecycle breakdown")
    pyreq_parser.add_argument("pid", type=int, help="Target process PID")

    # Timeline CLI
    timeline_parser = subparsers.add_parser("timeline", help="Trace absolute chronological timeline call graph")
    timeline_parser.add_argument("pid", type=int, help="Target process PID")
    timeline_parser.add_argument("--duration", type=float, default=5.0, help="Sampling duration in seconds")
    timeline_parser.add_argument("--threshold", type=float, default=None, help="Show only functions slower than this threshold in ms")

    # Pythread CLI
    pythread_parser = subparsers.add_parser("pythread", help="Trace thread-aware function call timelines with self-time")
    pythread_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyasync CLI
    pyasync_parser = subparsers.add_parser("pyasync", help="Trace async await coroutine metrics")
    pyasync_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyargs CLI
    pyargs_parser = subparsers.add_parser("pyargs", help="Profile Python Vectorcall argument layouts")
    pyargs_parser.add_argument("pid", type=int, help="Target process PID")

    # Pysyscall CLI
    pysyscall_parser = subparsers.add_parser("pysyscall", help="Profile syscalls attributed directly to Python code")
    pysyscall_parser.add_argument("pid", type=int, help="Target process PID")

    # Pynplus1 CLI
    pynplus1_parser = subparsers.add_parser("pynplus1", help="Profile ORM queries to detect loop-driven N+1 queries")
    pynplus1_parser.add_argument("pid", type=int, help="Target process PID")

    # Pygraph CLI
    pygraph_parser = subparsers.add_parser("pygraph", help="Trace hierarchical call relationship graph")
    pygraph_parser.add_argument("pid", type=int, help="Target process PID")

    # Pyanomaly CLI
    pyanomaly_parser = subparsers.add_parser("pyanomaly", help="Profile statistical baselines to catch slow anomalies")
    pyanomaly_parser.add_argument("pid", type=int, help="Target process PID")

    # Pydash CLI
    pydash_parser = subparsers.add_parser("pydash", help="Stream traces directly to live curses dashboard")
    pydash_parser.add_argument("pid", type=int, help="Target process PID")

    # Pysingle CLI
    pysingle_parser = subparsers.add_parser("pysingle", help="Trace single request / execution call tree with self time")
    pysingle_parser.add_argument("pid", type=int, help="Target process PID")
    pysingle_parser.add_argument("target_func", type=str, help="Name of entry point function to trace")
    pysingle_parser.add_argument("--tid", type=int, default=None, help="Trace only target thread ID")

    args = parser.parse_args()

    # DI container wiring / dependency selection
    collector = RealTraceCollectorAdapter()
    
    if args.command == "attach":
        service = AttachService(collector)
        sys.exit(service.attach_and_collect(args.pid))
        
    elif args.command == "flow":
        service = FlowService()
        events = collector.get_events()
        service.render_tree(events)
        sys.exit(0)

    elif args.command == "stitch":
        service = StitchService()
        services = [s.strip() for s in args.services.split(",")]
        service.stitch_traces(services)
        sys.exit(0)

    elif args.command == "slow":
        service = SlowService()
        threshold_ms = 200
        if args.threshold.endswith("ms"):
            try:
                threshold_ms = int(args.threshold[:-2])
            except ValueError:
                pass
        service.monitor(threshold_ms, args.watch)
        sys.exit(0)

    elif args.command == "diff":
        service = DiffService()
        service.compare(args.before, args.after)
        sys.exit(0)

    elif args.command == "syscall":
        service = SyscallService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "malloc":
        service = MallocService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "tcp":
        service = TcpService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "io":
        service = IoService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "flame":
        service = FlameService(collector)
        service.trace(args.pid, args.duration)
        sys.exit(0)

    elif args.command == "sched":
        service = SchedService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pycall":
        service = PycallService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pyframe":
        service = PyframeService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pycpu":
        service = PycpuService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pyexcept":
        service = PyexceptService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pyiowait":
        service = PyiowaitService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pygil":
        service = PygilService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pyleak":
        service = PyleakService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pyreq":
        service = PyreqService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "timeline":
        service = TimelineService(collector)
        service.trace(args.pid, args.duration, args.threshold)
        sys.exit(0)

    elif args.command == "pythread":
        service = PythreadService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pyasync":
        service = PyasyncService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pyargs":
        service = PyargsService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pysyscall":
        service = PysyscallService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pynplus1":
        service = Pynplus1Service(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pygraph":
        service = PygraphService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pyanomaly":
        service = PyanomalyService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pydash":
        service = PydashService(collector)
        service.trace(args.pid)
        sys.exit(0)

    elif args.command == "pysingle":
        service = PysingleService(collector)
        service.trace(args.pid, args.target_func, args.tid)
        sys.exit(0)

if __name__ == "__main__":
    main()
