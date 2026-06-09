import argparse
import sys
from pytrace_features.attach.index import AttachService
from pytrace_features.flow.index import FlowService
from pytrace_features.stitch.index import StitchService
from pytrace_features.slow.index import SlowService
from pytrace_features.diff.index import DiffService
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

    args = parser.parse_args()

    # DI container wiring / dependency selection
    collector = RealTraceCollectorAdapter()
    
    if args.command == "attach":
        service = AttachService(collector)
        sys.exit(service.attach_and_collect(args.pid))
        
    elif args.command == "flow":
        service = FlowService()
        # Fetch events from our collector
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

if __name__ == "__main__":
    main()
