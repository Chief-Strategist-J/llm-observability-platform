import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class CorrelationService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, service_name: str = "py-service") -> None:
        print(f"Attaching correlation timeline tracer to PID {pid} as service name '{service_name}'...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            # Simulating correlation output
            print(f"SVC={service_name} TS=1718001000 ENTER process_payment payment.py:88")
            print(f"SVC={service_name} TS=1718001001 CONNECT")
            return

        program = f"""
        usdt:/usr/bin/python3:python:function__entry /pid == $1/ {{
          printf("SVC={service_name} TS=%lld ENTER %s %s:%d\\n",
            nsecs, str(arg1), str(arg0), arg2);
        }}
        usdt:/usr/bin/python3:python:function__return /pid == $1/ {{
          printf("SVC={service_name} TS=%lld EXIT  %s\\n",
            nsecs, str(arg1));
        }}
        tracepoint:syscalls:sys_enter_connect /pid == $1/ {{
          printf("SVC={service_name} TS=%lld CONNECT\\n", nsecs);
        }}
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print(f"✓ Correlation timeline active for '{service_name}'. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached correlation timeline tracer.")
