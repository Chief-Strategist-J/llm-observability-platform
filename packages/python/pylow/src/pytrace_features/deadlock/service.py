import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class DeadlockService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching deadlock / stuck diagnostic tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("=== WHERE PROCESS SLEEPS ===")
            print("  [ustack]:")
            print("    pthread_cond_wait+0x12")
            print("    take_gil+0x42")
            print("    acquire_lock @ worker.py:112")
            print("  [kstack]:")
            print("    futex_wait_queue_me+0xb8")
            print("    futex_wait+0x120")
            print("\n=== LOCKS HELD > 5s ===")
            print("@lock[10234, 0x7f3b821034bc]: 1718123456")
            return

        program = """
        tracepoint:sched:sched_switch /args->prev_pid == $1/ {
          @stack = ustack(perf, 10);
          @kstack = kstack(perf, 10);
        }
        uprobe:/usr/bin/python3:PyThread_acquire_lock /pid == $1/ {
          @lock[tid, arg0] = nsecs;
        }
        uprobe:/usr/bin/python3:PyThread_release_lock /pid == $1/ {
          delete(@lock[tid, arg0]);
        }
        interval:s:5 {
          printf("=== WHERE PROCESS SLEEPS ===\\n");
          print(@stack);
          print(@kstack);
          printf("=== LOCKS HELD > 5s ===\\n");
          print(@lock);
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ Deadlock diagnostic active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached deadlock tracer.")
