"""uni — one front door for every language: detect, build, run, debug, trace.

Nothing is re-implemented; uni shells out to each ecosystem's own toolchain
(go/cargo/javac/mvn/gradle/tsc/node/python, dlv/gdb/jdb/pdb, perf/strace)
and unifies three things on top:

  1. language + toolchain detection from the target file/directory
  2. a single command surface: uni <detect|doctor|build|run|debug|trace|all>
  3. compiler/runtime errors from every language parsed into one
     "file:line  message" issue list, so the broken spot is always explicit

Every external command is echoed before it runs.
"""
import os
import shutil
import subprocess
import sys

from pytrace_features.lang_trace.index import LangTraceService, LangTraceRequest
from pytrace_features.uni.detect import MARKERS, lang_from_extension, lang_from_markers, parse_issues
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

TOOLCHAIN = {
    "python": {"build": ["python3"], "run": ["python3"], "debug": ["python3"], "trace": ["bpftrace", "strace"]},
    "go":     {"build": ["go"], "run": ["go"], "debug": ["dlv"], "trace": ["dlv", "perf", "strace"]},
    "rust":   {"build": ["cargo", "rustc"], "run": ["cargo"], "debug": ["rust-gdb", "gdb", "lldb"], "trace": ["perf", "strace"]},
    "java":   {"build": ["javac", "mvn", "gradle"], "run": ["java"], "debug": ["jdb"], "trace": ["jcmd", "jstack"]},
    "ts":     {"build": ["tsc"], "run": ["tsx", "ts-node", "node"], "debug": ["node"], "trace": ["node", "perf", "strace"]},
    "js":     {"build": [], "run": ["node"], "debug": ["node"], "trace": ["node", "perf", "strace"]},
}


class UniService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()
        self.lang_trace = LangTraceService(self.collector)

    # ── detection ─────────────────────────────────────────────────────────

    def detect_lang(self, target: str) -> str | None:
        if os.path.isdir(target):
            return lang_from_markers(os.listdir(target))
        return lang_from_extension(target)

    def detect(self, target: str) -> str | None:
        lang = self.detect_lang(target)
        if not lang:
            print(f"✗ Could not detect language for {target}")
            print(f"  (directories need one of: {', '.join(m for m, _ in MARKERS)})")
            return None
        kind = "project" if os.path.isdir(target) else "file"
        print(f"✓ {target}: {lang} {kind}")
        for stage in ("build", "run", "debug", "trace"):
            tools = TOOLCHAIN[lang][stage]
            avail = [f"{t}{'' if shutil.which(t) else ' (missing)'}" for t in tools] or ["(no build step)"]
            print(f"  {stage:<6} → {', '.join(avail)}")
        return lang

    def doctor(self) -> None:
        print("uni toolchain doctor — what's installed on this machine:\n")
        seen: dict[str, bool] = {}
        for lang, stages in TOOLCHAIN.items():
            tools = sorted({t for ts in stages.values() for t in ts})
            status = []
            for t in tools:
                if t not in seen:
                    seen[t] = shutil.which(t) is not None
                status.append(f"{'✓' if seen[t] else '✗'} {t}")
            print(f"  {lang:<8} {'  '.join(status)}")
        missing = sorted(t for t, ok in seen.items() if not ok)
        if missing:
            print(f"\nMissing (install for full coverage): {', '.join(missing)}")
        else:
            print("\nAll toolchains present.")

    # ── execution helpers ─────────────────────────────────────────────────

    def _exec(self, argv: list[str], cwd: str | None = None) -> int:
        print(f"→ exec: {' '.join(argv)}" + (f"  (cwd: {cwd})" if cwd else ""))
        try:
            proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
        except FileNotFoundError:
            print(f"  ✗ {argv[0]} not found on PATH")
            return 127
        if proc.stdout:
            print(proc.stdout, end="")
        if proc.stderr:
            print(proc.stderr, end="", file=sys.stderr)
        if proc.returncode != 0:
            self._print_issues(proc.stdout + "\n" + proc.stderr)
        return proc.returncode

    def _print_issues(self, output: str) -> None:
        issues = parse_issues(output)
        if issues:
            print("\n── issues ──────────────────────────────────────")
            for issue in issues:
                print(f"  ✗ {issue}")

    # ── stages ────────────────────────────────────────────────────────────

    def build(self, target: str, extra_args: list[str] | None = None) -> int:
        lang = self.detect_lang(target)
        if not lang:
            print(f"✗ Could not detect language for {target}")
            return 1
        extra = extra_args or []
        cwd = target if os.path.isdir(target) else None
        print(f"[uni] build ({lang})")
        if lang == "python":
            return self._exec(["python3", "-m", "compileall", "-q", target] if cwd
                              else ["python3", "-m", "py_compile", target])
        if lang == "go":
            return self._exec(["go", "build", *extra, *(["./..."] if cwd else [target])], cwd=cwd)
        if lang == "rust":
            if cwd or os.path.exists("Cargo.toml"):
                return self._exec(["cargo", "build", *extra], cwd=cwd)
            return self._exec(["rustc", *extra, target])
        if lang == "java":
            return self._build_java(target, extra, cwd)
        if lang == "ts":
            return self._exec(["tsc", *extra] if cwd else ["tsc", "--noEmit", *extra, target], cwd=cwd)
        if lang == "js":
            print("  (no compile step for JavaScript — running a syntax check)")
            return self._exec(["node", "--check", target]) if not cwd else 0
        return 1

    def _build_java(self, target: str, extra: list[str], cwd: str | None) -> int:
        if cwd and os.path.exists(os.path.join(cwd, "pom.xml")):
            return self._exec(["mvn", "-q", "compile", *extra], cwd=cwd)
        if cwd and any(os.path.exists(os.path.join(cwd, g)) for g in ("build.gradle", "build.gradle.kts")):
            return self._exec(["gradle", "compileJava", *extra], cwd=cwd)
        return self._exec(["javac", *extra, target])

    def run(self, target: str, prog_args: list[str] | None = None) -> int:
        lang = self.detect_lang(target)
        if not lang:
            print(f"✗ Could not detect language for {target}")
            return 1
        args = prog_args or []
        cwd = target if os.path.isdir(target) else None
        print(f"[uni] run ({lang})")
        if lang == "python":
            return self._exec(["python3", target, *args])
        if lang == "go":
            return self._exec(["go", "run", "./..." if cwd else target, *args], cwd=cwd)
        if lang == "rust":
            if cwd or os.path.exists("Cargo.toml"):
                return self._exec(["cargo", "run", *(["--", *args] if args else [])], cwd=cwd)
            rc = self._exec(["rustc", target, "-o", "/tmp/pylow_uni_rust"])
            return rc if rc != 0 else self._exec(["/tmp/pylow_uni_rust", *args])
        if lang == "java":
            return self._exec(["java", target, *args], cwd=cwd)  # JEP 330 single-file launch
        if lang == "ts":
            return self._run_ts(target, args, cwd)
        if lang == "js":
            return self._exec(["node", target, *args])
        return 1

    def _run_ts(self, target: str, args: list[str], cwd: str | None) -> int:
        runner = next((r for r in ("tsx", "ts-node") if shutil.which(r)), None)
        if runner:
            return self._exec([runner, target, *args], cwd=cwd)
        print("  tsx/ts-node not found — compiling with tsc then running node")
        rc = self._exec(["tsc", "--outDir", "/tmp/pylow_uni_ts", target])
        if rc != 0:
            return rc
        js = os.path.join("/tmp/pylow_uni_ts", os.path.basename(target).rsplit(".", 1)[0] + ".js")
        return self._exec(["node", js, *args])

    def debug(self, target: str) -> int:
        lang = self.detect_lang(target)
        if not lang:
            print(f"✗ Could not detect language for {target}")
            return 1
        debugger_cmd = {
            "python": ["python3", "-m", "pdb", target],
            "go": ["dlv", "debug"] if os.path.isdir(target) else ["dlv", "debug", target],
            "rust": [next((d for d in ("rust-gdb", "gdb", "lldb") if shutil.which(d)), "gdb"), target],
            "java": ["jdb", os.path.splitext(os.path.basename(target))[0]],
            "ts": ["node", "inspect", "--require", "ts-node/register", target] if shutil.which("ts-node")
                  else ["node", "inspect", target],
            "js": ["node", "inspect", target],
        }[lang]
        print(f"[uni] debug ({lang})")
        if not sys.stdin.isatty():
            print(f"Interactive debugger (run in a terminal): {' '.join(debugger_cmd)}")
            return 0
        print(f"→ exec: {' '.join(debugger_cmd)}")
        return subprocess.call(debugger_cmd, cwd=target if os.path.isdir(target) else None)

    def trace(self, target: str, pid: int = 0, duration: float = 10.0) -> int:
        lang = self.detect_lang(target) if target else None
        print(f"[uni] trace ({lang or 'unknown'})")
        if lang == "python":
            return self._trace_python(target, pid)
        if lang in ("go", "rust", "java", "ts", "js"):
            mapped = "ts" if lang == "js" else lang
            launch = None if pid else self._launch_cmd(lang, target)
            self.lang_trace.trace(LangTraceRequest(lang=mapped, pid=pid, duration=duration, cmd=launch))
            return 0
        print(f"✗ Could not detect language for {target}")
        return 1

    def _trace_python(self, target: str, pid: int) -> int:
        if pid:
            print(f"Python target — use pylow's native tracers: pylow pycall {pid} / pylow timeline {pid}")
            return 0
        if shutil.which("strace"):
            return self._exec(["strace", "-c", "-f", "python3", target])
        return self._exec(["python3", "-X", "importtime", target])

    def _launch_cmd(self, lang: str, target: str) -> str:
        return {"go": f"go run {target}", "rust": "cargo run", "java": f"java {target}",
                "ts": f"node {target}", "js": f"node {target}"}[lang]

    def all(self, target: str, prog_args: list[str] | None = None, do_trace: bool = False) -> int:
        """The daily-driver: detect → build → run (→ trace), stopping at the first failure."""
        lang = self.detect(target)
        if not lang:
            return 1
        if TOOLCHAIN[lang]["build"]:
            rc = self.build(target)
            if rc != 0:
                print(f"\n[uni] build failed (exit {rc}) — fix the issues above before running.")
                return rc
        rc = self.run(target, prog_args)
        if rc != 0:
            print(f"\n[uni] run failed (exit {rc}).")
            return rc
        if do_trace:
            self.trace(target)
        print("\n[uni] ✓ all stages passed")
        return 0
