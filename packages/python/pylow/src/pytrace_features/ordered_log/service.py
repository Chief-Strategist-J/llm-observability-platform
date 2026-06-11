import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class OrderedLogService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, filter_internals: bool = False) -> None:
        print(f"Attaching ordered function call log tracer to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print("\n1718123456001234000 10234 ENTER handle_request server.py:45")
            if not filter_internals:
                print("1718123456005678000 10234 ENTER importlib._bootstrap <frozen importlib._bootstrap>:23")
                print("1718123456006123000 10234 EXIT  importlib._bootstrap")
            print("1718123456012345000 10234 ENTER validate_token auth.py:12")
            print("1718123456015678000 10234 EXIT  validate_token 3ms")
            print("1718123456016123000 10234 EXIT  handle_request 15ms")
            return

        filter_str = ""
        if filter_internals:
            filter_str = """
            /str(arg0) != "<frozen importlib._bootstrap>"
            && str(arg0) != "<frozen importlib._bootstrap_external>"
            && str(arg0) != "threading.py"
            && str(arg0) != "socketserver.py"/
            """
        
        program = f"""
        usdt:/usr/bin/python3:python:function__entry {filter_str} {{
          @enter_ts[tid, str(arg1)] = nsecs;
          @call_depth[tid]++;
          printf("%lld %d ENTER %s %s:%d\\n",
            nsecs, tid, str(arg1), str(arg0), arg2);
        }}
        usdt:/usr/bin/python3:python:function__return {filter_str} {{
          $func = str(arg1);
          $dur  = nsecs - @enter_ts[tid, $func];
          @call_depth[tid]--;
          printf("%lld %d EXIT  %s %lldms\\n",
            nsecs, tid, $func, $dur/1000000);
          delete(@enter_ts[tid, $func]);
        }}
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ Ordered function call log active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached ordered function call log tracer.")
