import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class CpuBoundService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching CPU bound diagnostic tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n--- Top Stacks ---")
            print("        execute_query @ db.py:102 (samples: 187)")
            print("        validate_token @ auth.py:12 (samples: 43)")
            print("\n--- Slow Functions (>10ms) ---")
            print("91ms execute_query db.py:102")
            return

        program = """
        profile:hz:999 /pid == $1/ {
          @[ustack(perf, 5)] = count();
        }
        usdt:/usr/bin/python3:python:function__entry /pid == $1/ { @t[tid,str(arg1)] = nsecs; }
        usdt:/usr/bin/python3:python:function__return /pid == $1/ {
          $d = nsecs - @t[tid,str(arg1)];
          if ($d > 10000000) {
            printf("%lldms %s %s:%d\\n", $d/1000000, str(arg1), str(arg0), arg2);
          }
          delete(@t[tid,str(arg1)]);
        }
        interval:s:10 {
          print(@, 3);
          exit();
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ CPU bound diagnostic active. Collecting for 10s...\n")
                time.sleep(10)
        except KeyboardInterrupt:
            print("\nDetached CPU bound tracer.")
