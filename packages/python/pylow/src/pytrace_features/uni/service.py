"""uni — one front door for every language: detect, build, run, debug, trace.

Registry-driven: every language's toolchain is declared as StageRules in
shared/lang/languages.py (rules as data — first rule whose predicates pass
wins). This engine resolves rules and executes them; it never branches on
language names. Supporting a new language = registering a LanguageSpec.

Compiler/runtime errors from every language are normalized into one
"file:line  message" issue list. Every external command is echoed.
"""
import os
import shutil
import subprocess
import sys

from pytrace_features.lang_trace.index import LangTraceService, LangTraceRequest
from pytrace_features.uni.detect import MARKERS, parse_issues
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter
from shared.lang import languages  # noqa: F401 — registers every LanguageSpec
from shared.lang.registry import LanguageRegistry, StageContext, format_argv

PIPELINE_STAGES = ("build", "run")     # executed in order by `uni all`


class StageStrategies:
    """Compound stage behaviors that need more than a single argv."""
    _strategies: dict = {}

    @classmethod
    def register(cls, name):
        def decorator(fn):
            cls._strategies[name] = fn
            return fn
        return decorator

    @classmethod
    def run(cls, name, service, target, args):
        return cls._strategies[name](service, target, args)


@StageStrategies.register("noop")
def _(service, target, args):
    return 0


@StageStrategies.register("rustc_then_exec")
def _(service, target, args):
    binary = "/tmp/pylow_uni_rust"
    rc = service._exec(["rustc", target, "-o", binary])
    return rc if rc != 0 else service._exec([binary, *args])


@StageStrategies.register("tsc_then_node")
def _(service, target, args):
    out_dir = "/tmp/pylow_uni_ts"
    rc = service._exec(["tsc", "--outDir", out_dir, target])
    if rc != 0:
        return rc
    js = os.path.join(out_dir, os.path.basename(target).rsplit(".", 1)[0] + ".js")
    return service._exec(["node", js, *args])


class UniService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()
        self.lang_trace = LangTraceService(self.collector)

    # ── detection ─────────────────────────────────────────────────────────

    def detect_lang(self, target: str) -> str | None:
        if os.path.isdir(target):
            return LanguageRegistry.lang_for_markers(os.listdir(target))
        return LanguageRegistry.lang_for_extension(target)

    def detect(self, target: str) -> str | None:
        lang = self.detect_lang(target)
        if not lang:
            print(f"✗ Could not detect language for {target}")
            print(f"  (directories need one of: {', '.join(m for m, _ in MARKERS)})")
            return None
        spec = LanguageRegistry.get(lang)
        kind = "project" if os.path.isdir(target) else "file"
        print(f"✓ {target}: {lang} {kind}")
        for stage, tools in self._stage_tools(spec).items():
            avail = [f"{t}{'' if shutil.which(t) else ' (missing)'}" for t in tools] or ["(built-in)"]
            print(f"  {stage:<6} → {', '.join(avail)}")
        return lang

    def _stage_tools(self, spec) -> dict:
        rows = {
            stage: sorted({rule.argv[0] for rule in spec.stage_rules(stage) if rule.argv})
            for stage in ("build", "run", "debug")
        }
        rows["trace"] = sorted({b.tool for b in (*spec.tracers, *spec.calltree) if b.tool}) \
            or ["(native pylow tracers)"]
        return rows

    def doctor(self) -> None:
        print("uni toolchain doctor — what's installed on this machine:\n")
        seen: dict = {}
        for lang in LanguageRegistry.names():
            spec = LanguageRegistry.get(lang)
            tools = sorted({t for ts in self._stage_tools(spec).values() for t in ts if not t.startswith("(")})
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

    def _exec(self, argv: list, cwd: str | None = None) -> int:
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

    def _run_stage(self, stage: str, target: str, params: dict) -> int:
        lang = self.detect_lang(target)
        if not lang:
            print(f"✗ Could not detect language for {target}")
            return 1
        spec = LanguageRegistry.get(lang)
        ctx = StageContext(target=target, is_dir=os.path.isdir(target))
        rule = LanguageRegistry.resolve_stage(spec, stage, ctx)
        if rule is None:
            print(f"✗ No {stage} rule registered for {lang}")
            return 1
        print(f"[uni] {stage} ({lang})")
        if rule.note:
            print(f"  {rule.note}")
        if rule.strategy:
            return StageStrategies.run(rule.strategy, self, target, params.get("args", []))
        mapping = {"target": target, "target_stem": os.path.splitext(os.path.basename(target))[0], **params}
        argv = format_argv(rule.argv, mapping)
        return self._exec(argv, cwd=target if rule.cwd_is_target else None)

    # ── stages ────────────────────────────────────────────────────────────

    def build(self, target: str, extra_args: list | None = None) -> int:
        return self._run_stage("build", target, {"extra": extra_args or []})

    def run(self, target: str, prog_args: list | None = None) -> int:
        return self._run_stage("run", target, {"args": prog_args or []})

    def debug(self, target: str) -> int:
        lang = self.detect_lang(target)
        if not lang:
            print(f"✗ Could not detect language for {target}")
            return 1
        spec = LanguageRegistry.get(lang)
        ctx = StageContext(target=target, is_dir=os.path.isdir(target))
        rule = LanguageRegistry.resolve_stage(spec, "debug", ctx)
        mapping = {"target": target, "target_stem": os.path.splitext(os.path.basename(target))[0]}
        debugger_cmd = format_argv(rule.argv, mapping)
        print(f"[uni] debug ({lang})")
        if not sys.stdin.isatty():
            print(f"Interactive debugger (run in a terminal): {' '.join(debugger_cmd)}")
            return 0
        print(f"→ exec: {' '.join(debugger_cmd)}")
        return subprocess.call(debugger_cmd, cwd=target if rule.cwd_is_target else None)

    def trace(self, target: str, pid: int = 0, duration: float = 10.0) -> int:
        lang = self.detect_lang(target) if target else None
        spec = LanguageRegistry.get(lang) if lang else None
        print(f"[uni] trace ({lang or 'unknown'})")
        if spec is None:
            print(f"✗ Could not detect language for {target}")
            return 1
        mapped = spec.trace_as or spec.name
        if not LanguageRegistry.get(mapped).tracers:
            return self._trace_native(target, pid)
        launch = None if pid else spec.launch_cmd.format(target=target)
        self.lang_trace.trace(LangTraceRequest(lang=mapped, pid=pid, duration=duration, cmd=launch))
        return 0

    def _trace_native(self, target: str, pid: int) -> int:
        if pid:
            print(f"Python target — use pylow's native tracers: pylow pycall {pid} / pylow timeline {pid}")
            return 0
        if shutil.which("strace"):
            return self._exec(["strace", "-c", "-f", "python3", target])
        return self._exec(["python3", "-X", "importtime", target])

    def all(self, target: str, prog_args: list | None = None, do_trace: bool = False) -> int:
        """The daily-driver pipeline: detect → build → run (→ trace), stopping at the first failure."""
        lang = self.detect(target)
        if not lang:
            return 1
        runners = {"build": lambda: self.build(target), "run": lambda: self.run(target, prog_args)}
        for stage in PIPELINE_STAGES:
            rc = runners[stage]()
            if rc != 0:
                print(f"\n[uni] {stage} failed (exit {rc}) — fix the issues above.")
                return rc
        if do_trace:
            self.trace(target)
        print("\n[uni] ✓ all stages passed")
        return 0
