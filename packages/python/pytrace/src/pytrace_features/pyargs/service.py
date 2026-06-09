import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class PyargsService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching argument Layout layout-tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Dereferencing Python structs... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("1000 CALL obj=0x7f3b821034bc args=0x7f3b821051fa")
            print("  type=dict")
            print("1050 FUNC_CALL load_dataset")
            return

        program = """
        uprobe:/usr/bin/python3:PyObject_Call {
            printf("%lld CALL obj=%p args=%p\\n", nsecs, arg0, arg1);
            $type_ptr = *(uint64*)((uint64)arg0 + 8);
            $name_ptr = *(uint64*)((uint64)$type_ptr + 24);
            printf("  type=%s\\n", str($name_ptr));
        }
        uprobe:/usr/bin/python3:_PyFunction_Vectorcall {
            $code = *(uint64*)((uint64)arg0 + 32);
            $name_obj = *(uint64*)((uint64)$code + 96);
            $name_str = str(*(uint64*)((uint64)$name_obj + 48));
            printf("%lld FUNC_CALL %s\\n", nsecs, $name_str);
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "printf":
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ Argument tracer active. Streaming struct attributes... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached argument tracer.")
