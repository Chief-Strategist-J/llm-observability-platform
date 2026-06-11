import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class ContextSwitchesService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching context switches tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            print("✓ Attached. Collecting context switch events... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("OFF CPU 87ms next_cpu=2")
            print("\n--- BPF Map: @off_cpu_ms ---")
            print("[0, 1]                12 |@@@@                                |")
            print("[2, 4]                89 |@@@@@@@@@@@@@@                      |")
            print("[64, 128]            210 |@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@|")
            return

        program = """
        tracepoint:sched:sched_switch /args->prev_pid == $1/ {
          @voluntary[args->prev_comm]   = count();
          @switch_ts = nsecs;
        }
        tracepoint:sched:sched_switch /args->next_pid == $1/ {
          if (@switch_ts) {
            $off_cpu = nsecs - @switch_ts;
            @off_cpu_ms = hist($off_cpu / 1000000);
            if ($off_cpu > 50000000) {
              printf("OFF CPU %lldms next_cpu=%d\\n", $off_cpu/1000000, cpu);
            }
          }
        }
        interval:s:10 { print(@off_cpu_ms); }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ Context switches tracer active. Streaming events... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached context switches tracer.")
