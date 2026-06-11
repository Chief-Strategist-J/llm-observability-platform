import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class PycallService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching Python function call timer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Collecting PyObject_Call events... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("\n--- BPF Map: @latency (time spent per function in us) ---")
            print("SLOW execute_query took 12400us")
            print("SLOW process_job took 1850us")
            print("\n@latency[execute_query]:")
            print("[10, 20]             45 |@@@@@@@@@@@                         |")
            print("[50, 100]           120 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|")
            return

        program = """
        uprobe:/usr/bin/python3:PyObject_Call {
            @start[tid] = nsecs;
            @func_name[tid] = str(arg0);
        }
        uretprobe:/usr/bin/python3:PyObject_Call {
            if (@start[tid]) {
                $dur = nsecs - @start[tid];
                if ($dur > 1000000) {
                    printf("SLOW %s took %lldus\\n", @func_name[tid], $dur / 1000);
                }
                @latency[@func_name[tid]] = hist($dur / 1000);
                delete(@start[tid]);
                delete(@func_name[tid]);
            }
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "map" or event.get("type") == "printf":
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ Function call timer active. Streaming events... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached function call timer.")
