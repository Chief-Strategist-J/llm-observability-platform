import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class AnomalyTriggerService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, target_func: str = "validate_payment") -> None:
        print(f"Attaching anomaly trigger tracer on PID {pid} targeting '{target_func}'...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n!!! EXCEPTION DURING PAYMENT !!!")
            print("type : ValueError")
            print("after: 9ms")
            print("  [ustack]:")
            print("    validate_payment @ payment.py:34")
            print("    process_payment @ payment.py:88")
            print("\n!!! SUSPICIOUSLY FAST RETURN !!!")
            print("returned in 23us — early return / branch issue?")
            print("  [ustack]:")
            print("    get_transaction_status @ payment.py:102")
            return

        program = f"""
        usdt:/usr/bin/python3:python:function__entry
        /str(arg1) == "{target_func}"/ {{
          @watch[tid] = 1;
          @watch_start[tid] = nsecs;
        }}

        usdt:/usr/bin/python3:python:function__entry /@watch[tid]/ {{
          printf("%lld ENTER %s %s:%d\\n",
            nsecs, str(arg1), str(arg0), arg2);
        }}

        usdt:/usr/bin/python3:python:function__return /@watch[tid]/ {{
          printf("%lld EXIT  %s\\n", nsecs, str(arg1));
        }}

        usdt:/usr/bin/python3:python:raise__exception /@watch[tid]/ {{
          printf("\\n!!! EXCEPTION DURING PAYMENT !!!\\n");
          printf("type : %s\\n", str(arg0));
          printf("after: %lldms\\n", (nsecs-@watch_start[tid])/1000000);
          print(ustack(perf, 15));
          @watch[tid] = 0;
          exit();
        }}

        usdt:/usr/bin/python3:python:function__entry
        /str(arg1) == "get_transaction_status"/ {{
          @tx_start[tid] = nsecs;
          @tx_stack[tid] = ustack(perf, 8);
        }}

        usdt:/usr/bin/python3:python:function__return
        /str(arg1) == "get_transaction_status"/ {{
          $dur = nsecs - @tx_start[tid];
          if ($dur < 100000) {{
            printf("\\n!!! SUSPICIOUSLY FAST RETURN !!!\\n");
            printf("returned in %ldus — early return / branch issue?\\n", $dur/1000);
            print(@tx_stack[tid]);
          }}
          delete(@tx_start[tid]);
          delete(@tx_stack[tid]);
        }}
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ Anomaly trigger active. Monitoring execution... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached anomaly trigger.")
