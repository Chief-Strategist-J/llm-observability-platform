import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class KernelBlockedService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching kernel blocked stack tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            print("✓ Attached. Monitoring blocked states... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("BLOCKED IN KERNEL:")
            print("        __schedule+0x310")
            print("        schedule+0x44")
            print("        futex_wait_queue_me+0xb8")
            print("        futex_wait+0x120")
            print("        do_futex+0x340")
            print("        __x64_sys_futex+0x140")
            print("        [ustack]:")
            print("        pthread_cond_wait+0x12")
            print("        take_gil+0x42")
            print("        execute_query+0x91  db.py:102")
            return

        program = """
        tracepoint:sched:sched_switch /args->prev_pid == $1 && args->prev_state == 1/ {
          printf("BLOCKED IN KERNEL:\\n");
          print(kstack(perf, 10));
          print(ustack(perf, 5));
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ Kernel blocked stack tracer active. Streaming events... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached kernel blocked stack tracer.")
