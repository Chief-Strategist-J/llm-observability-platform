"""Multi-language runtime tracing — Go, Rust, Java, TypeScript/Node.

Registry-driven: which backends a language has (and their priority) is
declared in shared/lang/languages.py as TracerBackend entries; backend
behaviors are registered in strategies.py. This engine never branches on
language names — supporting a new language is a registry entry.

    Go        delve (dlv), perf, strace
    Rust      perf, strace
    Java      jcmd (JFR + Thread.print), jstack
    TS/Node   V8 inspector (SIGUSR1), perf, strace

Every external command is printed before it executes, so the output always
shows exactly what ran.
"""
import dataclasses
import os
import shutil
import signal
import subprocess
import tempfile
import time

from pytrace_features.lang_trace.strategies import TracerStrategies
from pytrace_features.lang_trace.types import LangTraceRequest, SUPPORTED_LANGS
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter
from shared.lang import languages  # noqa: F401 — registers every LanguageSpec
from shared.lang.registry import LanguageRegistry

_SIMULATED_SAMPLES = {
    "go": [
        "goroutine 42 [running]  main.handlePayment +0x4f      11.2ms",
        "goroutine 18 [chan recv] main.(*Worker).consume +0x88  9.8ms",
        "SLOW main.queryOrders took 142ms (database/sql.(*DB).QueryContext)",
    ],
    "rust": [
        "12.4%  payment_svc`core::ops::function::FnOnce::call_once",
        " 9.1%  payment_svc`payment_svc::db::fetch_orders",
        "SLOW payment_svc::db::fetch_orders took 98ms",
    ],
    "java": [
        '"http-nio-8080-exec-3" #42 RUNNABLE  com.acme.OrderService.findAll(OrderService.java:88)',
        '"pool-2-thread-1"     #51 BLOCKED   com.acme.CacheLock.acquire(CacheLock.java:31)',
        "SLOW OrderService.findAll took 210ms (JDBC executeQuery)",
    ],
    "ts": [
        "ticks  total  name",
        " 412  38.1%  LazyCompile: *processOrder /app/src/orders.ts:42",
        " 188  17.4%  LazyCompile: ~stringify node:internal/json",
        "SLOW processOrder took 87ms (event loop blocked)",
    ],
}


class LangTraceService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    # ── shared helpers ────────────────────────────────────────────────────

    def _pick(self, candidates: list) -> str | None:
        return next((tool for tool in candidates if shutil.which(tool)), None)

    def _exec(self, argv: list, timeout: float | None = None) -> int:
        print(f"→ exec: {' '.join(argv)}")
        try:
            return subprocess.run(argv, timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            print(f"  (stopped after {timeout}s sampling window)")
            return 0
        except FileNotFoundError:
            print(f"  ✗ {argv[0]} not found on PATH")
            return 127

    def _exec_capture(self, argv: list, timeout: float | None = None) -> tuple:
        print(f"→ exec: {' '.join(argv)}")
        try:
            proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
            return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
        except subprocess.TimeoutExpired as exc:
            out = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            return 0, out
        except FileNotFoundError:
            return 127, f"{argv[0]} not found on PATH"

    def _strace_summary(self, pid: int, duration: float) -> None:
        argv = ["strace", "-c", "-f", "-p", str(pid)]
        print(f"→ exec: {' '.join(argv)}  (for {duration}s)")
        proc = subprocess.Popen(argv)
        try:
            time.sleep(duration)
        finally:
            proc.send_signal(signal.SIGINT)
            proc.wait()

    def _perf_profile(self, pid: int, duration: float) -> None:
        out = os.path.join(tempfile.gettempdir(), f"pylow_perf_{pid}.data")
        rc = self._exec(["perf", "record", "-F", "99", "-g", "-p", str(pid), "-o", out,
                         "--", "sleep", str(duration)])
        if rc == 0 and os.path.exists(out):
            self._exec(["perf", "report", "--stdio", "--max-stack", "8", "-i", out])
            print(f"\nRaw perf data kept at {out} (open with `perf report -i {out}`)")

    def _simulated(self, lang: str) -> None:
        print(f"✓ Attached (simulated — no {lang} tooling found on PATH). Sampling...\n")
        time.sleep(1.0)
        for line in _SIMULATED_SAMPLES.get(lang, _SIMULATED_SAMPLES["go"]):
            print(line)

    # ── traced launches (instead of attaching) ────────────────────────────

    def _launch_traced(self, cmd: list, lang: str) -> None:
        launchers = {
            "node_cpu_prof": self._launch_node_cpu_prof,
            "perf": self._launch_perf,
            "strace": self._launch_counted,
            "ltrace": self._launch_counted,
        }
        launchers.get(self._launch_strategy(cmd, lang), self._launch_untraced)(cmd)

    def _launch_strategy(self, cmd: list, lang: str) -> str:
        if lang == "ts" and cmd and os.path.basename(cmd[0]) == "node":
            return "node_cpu_prof"
        return self._pick(["perf", "strace", "ltrace"]) or "untraced"

    def _launch_node_cpu_prof(self, cmd: list) -> None:
        prof_dir = os.path.join(tempfile.gettempdir(), "pylow_cpuprof")
        os.makedirs(prof_dir, exist_ok=True)
        self._exec([cmd[0], "--cpu-prof", "--cpu-prof-dir", prof_dir, *cmd[1:]])
        print(f"\nV8 CPU profile written to {prof_dir}/*.cpuprofile (open in Chrome DevTools → Performance)")

    def _launch_perf(self, cmd: list) -> None:
        self._exec(["perf", "record", "-F", "99", "-g", "--", *cmd])
        self._exec(["perf", "report", "--stdio", "--max-stack", "8"])

    def _launch_counted(self, cmd: list) -> None:
        tracer = self._pick(["strace", "ltrace"])
        self._exec([tracer, "-c", "-f", *cmd])

    def _launch_untraced(self, cmd: list) -> None:
        print("No tracer (perf/strace/ltrace) found — running untraced:")
        self._exec(cmd)

    # ── dispatch ──────────────────────────────────────────────────────────

    def trace(self, request: LangTraceRequest) -> None:
        lang = request.normalized_lang()
        if lang not in SUPPORTED_LANGS:
            print(f"Unsupported language '{request.lang}'. Supported: {', '.join(SUPPORTED_LANGS)}")
            return
        if request.cmd:
            print(f"Launching {lang} command under tracer: {request.cmd}")
            self._launch_traced(request.cmd.split(), lang)
            return
        getattr(self, f"trace_{lang}")(request.pid, request.duration, request.func_regex)

    def _run_backends(self, lang: str, request: LangTraceRequest) -> None:
        spec = LanguageRegistry.get(lang)
        backend = next(
            (b for b in spec.tracers if not b.tool or self._pick([b.tool])),
            None,
        )
        if backend is None:
            self._simulated(lang)
            return
        TracerStrategies.run(backend.strategy, self, dataclasses.replace(request, lang=lang))

    # ── per-language entry points (thin wrappers over the registry) ───────

    def trace_go(self, pid: int, duration: float = 10.0, func_regex: str | None = None) -> None:
        print(f"Attaching Go tracer to PID {pid}...")
        self._run_backends("go", LangTraceRequest("go", pid, duration, func_regex))

    def trace_rust(self, pid: int, duration: float = 10.0, func_regex: str | None = None) -> None:
        print(f"Attaching Rust tracer to PID {pid}...")
        self._run_backends("rust", LangTraceRequest("rust", pid, duration, func_regex))

    def trace_java(self, pid: int, duration: float = 10.0, func_regex: str | None = None) -> None:
        print(f"Attaching Java tracer to PID {pid}...")
        self._run_backends("java", LangTraceRequest("java", pid, duration, func_regex))

    def trace_ts(self, pid: int, duration: float = 10.0, func_regex: str | None = None) -> None:
        print(f"Attaching TypeScript/Node tracer to PID {pid}...")
        self._run_backends("ts", LangTraceRequest("ts", pid, duration, func_regex))

    # ── java/node helpers used by strategies ──────────────────────────────

    def _java_thread_snapshot(self, pid: int) -> None:
        rc, out = self._exec_capture(["jcmd", str(pid), "Thread.print"], timeout=10)
        if rc == 0:
            lines = [l for l in out.splitlines()
                     if l.strip().startswith('"') or "java.lang.Thread.State" in l]
            print("\n--- Thread snapshot (jcmd Thread.print) ---")
            print("\n".join(lines[:40]) or out[:2000])

    def _java_flight_recording(self, pid: int, duration: float) -> None:
        jfr_file = os.path.join(tempfile.gettempdir(), f"pylow_{pid}.jfr")
        rc, out = self._exec_capture(
            ["jcmd", str(pid), "JFR.start", f"duration={int(duration)}s", f"filename={jfr_file}"],
            timeout=10)
        print(out.strip())
        if rc != 0 or "Started recording" not in out:
            return
        print(f"Waiting {duration}s for the flight recording to finish...")
        time.sleep(duration + 1)
        if shutil.which("jfr"):
            _, out = self._exec_capture(["jfr", "print", "--events", "jdk.ExecutionSample", jfr_file],
                                        timeout=30)
            print(out[:4000] or "(no execution samples)")
        else:
            print(f"Recording saved to {jfr_file} — open with JDK Mission Control or `jfr print`.")

    def _open_node_inspector(self, pid: int) -> bool | None:
        try:
            os.kill(pid, signal.SIGUSR1)
        except ProcessLookupError:
            print(f"✗ No process with PID {pid}")
            return None
        except PermissionError:
            print("✗ Not permitted to signal that PID (different user?) — skipping inspector activation")
            return False
        print(f"→ sent SIGUSR1 to PID {pid}: V8 inspector now listening on ws://127.0.0.1:9229")
        print("  Connect with chrome://inspect, VS Code attach, or `node inspect -p <pid>` for live debugging.")
        return True
