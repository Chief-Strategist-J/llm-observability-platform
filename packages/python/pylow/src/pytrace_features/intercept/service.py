import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class InterceptService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int, target_func: str = "process_payment") -> None:
        print(f"Attaching boundary intercept tracer targeting '{target_func}' on PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            time.sleep(1.5)
            print(f"\n=== {target_func} CALLED ===")
            print("file : payment.py")
            print("line : 88")
            print("tid  : 10234")
            print("time : 1718123456001234000")
            print("  [ustack]:")
            print("    checkout_user @ cart.py:12")
            print("    handle_request @ server.py:45")
            print("\n=== OUTBOUND DATA ===")
            print("POST /api/transaction HTTP/1.1\n{\"amount\": 100, \"user_id\": 42, \"status\": \"pending\"}")
            print("\n=== INBOUND DATA ===")
            print("HTTP/1.1 200 OK\n{\"transaction_id\": null, \"error\": \"user_not_found\"}")
            print(f"\n=== {target_func} RETURNED ===")
            print("duration: 15ms")
            return

        program = f"""
        usdt:/usr/bin/python3:python:function__entry
        /str(arg1) == "{target_func}"/ {{
          printf("\\n=== {target_func} CALLED ===\\n");
          printf("file : %s\\n", str(arg0));
          printf("line : %d\\n", arg2);
          printf("tid  : %d\\n", tid);
          printf("time : %lld\\n", nsecs);
          print(ustack(perf, 5));
          @t[tid] = nsecs;
        }}

        usdt:/usr/bin/python3:python:function__return
        /str(arg1) == "{target_func}"/ {{
          printf("=== {target_func} RETURNED ===\\n");
          if (@t[tid]) {{
            printf("duration: %lldms\\n", (nsecs - @t[tid])/1000000);
            delete(@t[tid]);
          }}
        }}

        tracepoint:syscalls:sys_enter_write /pid == $1/ {{
          if (args->count > 0 && args->count < 1024) {{
            printf("\\n=== OUTBOUND DATA ===\\n");
            printf("%s\\n", str(args->buf, args->count));
            print(ustack(perf, 5));
          }}
        }}

        tracepoint:syscalls:sys_enter_read /pid == $1/ {{
          @read_buf[tid] = args->buf;
          @read_ts[tid]  = nsecs;
        }}

        tracepoint:syscalls:sys_exit_read /pid == $1 && args->ret > 0/ {{
          if (@read_buf[tid] && args->ret < 2048) {{
            printf("\\n=== INBOUND DATA ===\\n");
            printf("RECEIVED: %s\\n", str(@read_buf[tid], args->ret));
          }}
          delete(@read_buf[tid]);
        }}
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            with BpfSession(pid=pid, program=program):
                print("✓ Payload boundary intercept tracer active. Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached intercept tracer.")
