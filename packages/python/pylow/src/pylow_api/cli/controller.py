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



if __name__ == "__main__":
    main()
