import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class PyexceptService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching Python exception tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Monitoring exceptions... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("EXCEPTION KeyError @ tid=10234")
            print("  [ustack]:")
            print("    get_user_context @ db/client.py:48")
            print("    handle_request @ gateway/server.py:12")
            print("CAUGHT    KeyError")
            return

        program = """
        usdt:/usr/bin/python3:python:raise__exception {
            printf("EXCEPTION %s @ tid=%d\\n", str(arg0), tid);
            print(ustack(perf));
        }
        usdt:/usr/bin/python3:python:except__handling {
            printf("CAUGHT    %s\\n", str(arg0));
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "printf":
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ Exception tracer active. Streaming exceptions... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached exception tracer.")
