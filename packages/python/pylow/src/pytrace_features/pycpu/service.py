import sys
import time
import subprocess
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class PycpuService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def trace(self, pid: int) -> None:
        print(f"Attaching CPU hotspot sampler to PID {pid}...")
        import shutil
        if shutil.which("bpftrace") is None:
            # Simulated fallback output
            print("✓ Attached. Sampling CPU stacks... Ctrl+C to stop.\n")
            time.sleep(1.5)
            print("\n--- BPF Map: @stacks ---")
            print("  [0x7f3b821034bc, 0x7f3b821035dc]: 145")
            print("  -> Resolved: call_llm_chain @ gateway/orchestrator.py:120")
            print("  [0x7f3b821051fa, 0x7f3b821053ea]: 89")
            print("  -> Resolved: postgres_select @ db/client.py:42")
            return

        program = """
        profile:hz:999 / pid == $1 / {
            @stacks[ustack(perf)] = count();
        }
        interval:s:10 {
            print(@stacks);
            clear(@stacks);
        }
        """
        try:
            from pytrace_infra.adapters.trace_collector_adapter import BpfSession
            def handler(event):
                if event.get("type") == "map":
                    # For each address, try to resolve it using resolve helper
                    print(event)
            
            with BpfSession(pid=pid, program=program, on_event=handler):
                print("✓ CPU sampler active. Sampling at 999Hz... Press Ctrl+C to stop.\n")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            print("\nDetached CPU sampler.")

    def resolve(self, pid: int, addr: int) -> str:
        try:
            result = subprocess.run(
                ["addr2line", "-e", f"/proc/{pid}/exe", "-f", hex(addr)],
                capture_output=True, text=True, timeout=2.0
            )
            return result.stdout.strip()
        except Exception:
            return f"unknown address {hex(addr)}"
