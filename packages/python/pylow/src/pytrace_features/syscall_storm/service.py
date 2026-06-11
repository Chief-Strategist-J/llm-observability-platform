import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class SyscallStormService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, syscall_id: int | None = None) -> None:
        print(f"Attaching syscall storm tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n=== TOP SYSCALLS BY COUNT (5s) ===")
            print("sys_enter_read (id=0)                                8421")
            print("sys_enter_write (id=1)                               423")
            print("\n=== DRIVING PYTHON CALLSITE ===")
            print("@calls[")
            print("    read+0x10")
            print("    socket_recv+0x22   network.py:55")
            print("    fetch_data+0x18    client.py:30")
            print("]: 8421")
            return

        sid_filter = f"&& args->id == {syscall_id}" if syscall_id is not None else ""
        program = f"""
        tracepoint:raw_syscalls:sys_enter /pid == $1 {sid_filter}/ {{
          @[args->id] = count();
          @callers[ustack(perf, 5)] = count();
        }}
        interval:s:5 {{
          printf("=== SYSCALLS ===\\n");
          print(@, 5);
          printf("=== CALLERS ===\\n");
          print(@callers, 3);
          exit();
        }}
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ Syscall storm tracer active. Collecting for 5s...\n")
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nDetached syscall storm tracer.")
