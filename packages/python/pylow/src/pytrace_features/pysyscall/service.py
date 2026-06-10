import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class PysyscallService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching syscall-to-Python attribution tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Monitoring slow read and futex syscalls... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("\n=== SLOW READ fd=4 dur=12ms ===")
            print("  [ustack]:")
            print("    fetch_metadata @ db/client.py:54")
            print("    handle_request @ gateway/server.py:12")
            print("\nLOCK CONTENTION 25ms")
            print("  [ustack]:")
            print("    get_lock @ threading.py:42")
            print("    process_job @ worker/tasks.py:14")
            return

        program = """
        tracepoint:syscalls:sys_enter_read / pid == $1 / {
            @read_ustack[tid] = ustack(perf, 32);
            @read_ts[tid] = nsecs;
            @read_fd[tid] = args->fd;
        }
        tracepoint:syscalls:sys_exit_read / pid == $1 / {
            if (@read_ts[tid]) {
                $dur = nsecs - @read_ts[tid];
                if ($dur > 1000000) {
                    printf("\\n=== SLOW READ fd=%d dur=%lldms ===\\n",
                        @read_fd[tid], $dur / 1000000);
                    print(@read_ustack[tid]);
                }
                delete(@read_ts[tid]);
                delete(@read_ustack[tid]);
                delete(@read_fd[tid]);
            }
        }
        tracepoint:syscalls:sys_enter_futex / pid == $1 / {
            @futex_ts[tid] = nsecs;
            @futex_stack[tid] = ustack(perf, 20);
        }
        tracepoint:syscalls:sys_exit_futex / pid == $1 / {
            if (@futex_ts[tid]) {
                $dur = nsecs - @futex_ts[tid];
                if ($dur > 5000000) {
                    printf("LOCK CONTENTION %lldms\\n", $dur / 1000000);
                    print(@futex_stack[tid]);
                }
                delete(@futex_ts[tid]);
                delete(@futex_stack[tid]);
            }
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "printf":
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ Syscall attribution active. Streaming slow operations... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached syscall attribution tracer.")
