"""Exact, noise-filtered execution call trees for any registered language.

Backends are declared per language in shared/lang/languages.py
(CallTreeBackend entries, priority-ordered); behaviors are registered below.
The engine resolves spec → backend → strategy and never branches on language
names. Every tree is printed AND saved to a text file with one
"function  file:line" node per line so you can jump straight to the code.
"""
import glob
import json
import os
import subprocess
import tempfile

from pytrace_features.call_tree.render import PY_BOOTSTRAP, indent_jdb_trace, parse_cpuprofile
from pytrace_features.call_tree.types import CallTreeRequest
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter
from shared.lang import languages  # noqa: F401 — registers every LanguageSpec
from shared.lang.registry import LanguageRegistry, pick_tool
from shared.utils.paced_process import PacedPlan, run_paced


class CallTreeStrategies:
    _strategies: dict = {}

    @classmethod
    def register(cls, name):
        def decorator(fn):
            cls._strategies[name] = fn
            return fn
        return decorator

    @classmethod
    def run(cls, name, service, request):
        return cls._strategies[name](service, request)


class CallTreeService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    # ── engine ────────────────────────────────────────────────────────────

    def trace(self, request: CallTreeRequest) -> None:
        lang = request.lang or self._detect(request.target)
        spec = LanguageRegistry.get(lang) if lang else None
        if spec is None:
            print(f"✗ Could not detect language for {request.target!r} — pass --lang")
            return
        spec = LanguageRegistry.get(spec.trace_as) if spec.trace_as else spec
        mode = "attach" if request.pid else "launch"
        backend = next(
            (b for b in spec.calltree
             if b.mode in (mode, "both") and (not b.tool or pick_tool((b.tool,)))),
            None,
        )
        if backend is None:
            self._unavailable(spec, mode)
            return
        request.lang = spec.name
        print(f"[calltree] {spec.name} via {backend.strategy} ({mode})")
        CallTreeStrategies.run(backend.strategy, self, request)

    def _detect(self, target: str) -> str | None:
        if os.path.isdir(target):
            return LanguageRegistry.lang_for_markers(os.listdir(target))
        return LanguageRegistry.lang_for_extension(target)

    def _unavailable(self, spec, mode: str) -> None:
        tools = sorted({b.tool for b in spec.calltree if b.tool})
        print(f"✗ No {mode}-mode call-tree backend installed for {spec.name}.")
        print(f"  Install one of: {', '.join(tools) or '(none registered)'}")

    # ── shared helpers used by strategies ─────────────────────────────────

    def _exec_capture(self, argv: list, options: dict | None = None) -> str:
        options = options or {}
        print(f"→ exec: {' '.join(argv)}")
        try:
            proc = subprocess.run(argv, capture_output=True, text=True, **options)
            return (proc.stdout or "") + (proc.stderr or "")
        except subprocess.TimeoutExpired as exc:
            return (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) \
                else (exc.stdout or "")
        except FileNotFoundError:
            return f"✗ {argv[0]} not found on PATH"

    def _save(self, lines: list, out_file: str, header: str) -> None:
        body = "\n".join(lines) if lines else "(no frames captured — check the filter)"
        print(f"\n── {header} ──")
        print(body)
        with open(out_file, "w", encoding="utf-8") as fh:
            fh.write(f"# {header}\n{body}\n")
        print(f"\n✓ call tree saved to {out_file}")


# ── strategies ─────────────────────────────────────────────────────────────

@CallTreeStrategies.register("python_settrace")
def _(service, request):
    bootstrap = os.path.join(tempfile.gettempdir(), "pylow_calltree_bootstrap.py")
    with open(bootstrap, "w", encoding="utf-8") as fh:
        fh.write(PY_BOOTSTRAP)
    env = {
        **os.environ,
        "PYLOW_CALLTREE_OUT": request.out_file("python"),
        "PYLOW_CALLTREE_FILTER": request.filter,
        "PYLOW_CALLTREE_DEPTH": str(request.depth),
    }
    argv = ["python3", bootstrap, request.target, *request.arg_list()]
    print(f"→ exec: {' '.join(argv)}")
    subprocess.run(argv, env=env)


@CallTreeStrategies.register("dlv_calltree")
def _(service, request):
    regex = request.filter or "main\\..*"
    if request.pid:
        out = service._exec_capture(["dlv", "trace", "-p", str(request.pid), regex],
                                    {"timeout": request.duration})
    else:
        cwd = request.target if os.path.isdir(request.target) else os.path.dirname(os.path.abspath(request.target))
        out = service._exec_capture(["dlv", "trace", regex], {"cwd": cwd, "timeout": 60})
    service._save(out.splitlines(), request.out_file("go"),
                  f"go call trace via delve (exact, pattern: {regex})")


@CallTreeStrategies.register("uftrace_tree")
def _(service, request):
    out = service._exec_capture(
        ["uftrace", "live", "-D", str(request.depth), request.target, *request.arg_list()],
        {"timeout": 120})
    service._save(out.splitlines(), request.out_file(request.lang),
                  f"{request.lang} call tree via uftrace (exact; build with -pg)")


@CallTreeStrategies.register("perf_tree")
def _(service, request):
    data = os.path.join(tempfile.gettempdir(), "pylow_calltree_perf.data")
    if request.pid:
        service._exec_capture(["perf", "record", "-F", "99", "-g", "-p", str(request.pid),
                               "-o", data, "--", "sleep", str(request.duration)])
    else:
        service._exec_capture(["perf", "record", "-F", "99", "-g", "-o", data, "--",
                               request.target, *request.arg_list()])
    out = service._exec_capture(["perf", "report", "--stdio", "--max-stack", str(request.depth),
                                 "-i", data])
    service._save(out.splitlines(), request.out_file(request.lang),
                  f"{request.lang} call tree via perf (SAMPLED on-CPU stacks, not exact)")


@CallTreeStrategies.register("jdb_method_trace")
def _(service, request):
    stem = os.path.splitext(os.path.basename(request.target))[0]
    cwd = os.path.dirname(os.path.abspath(request.target)) or "."
    if request.target.endswith(".java"):
        service._exec_capture(["javac", "-g", request.target])
    print(f"→ exec: jdb {stem}  (paced: stop in {stem}.main | run | trace go methods | cont)")
    out = run_paced(["jdb", stem], PacedPlan(
        setup=(f"stop in {stem}.main", "run"),
        per_stop=("trace go methods", "cont"),
        hit_marker=r"Breakpoint hit:",
        end_marker="The application exited",
        quit_cmd="quit", max_steps=1, timeout=90, cwd=cwd))
    tree = indent_jdb_trace(out, request.filter)
    service._save(tree, request.out_file("java"),
                  f"java call tree via jdb method trace (exact{', filter: ' + request.filter if request.filter else ''})")


@CallTreeStrategies.register("jfr_delegate")
def _(service, request):
    from pytrace_features.lang_trace.index import LangTraceService
    print("Attach-mode java tree uses Java Flight Recorder execution samples:")
    LangTraceService(service.collector).trace_java(request.pid, request.duration)


@CallTreeStrategies.register("node_cpuprofile")
def _(service, request):
    prof_dir = os.path.join(tempfile.gettempdir(), "pylow_calltree_cpuprof")
    os.makedirs(prof_dir, exist_ok=True)
    for stale in glob.glob(os.path.join(prof_dir, "*.cpuprofile")):
        os.unlink(stale)
    service._exec_capture(["node", "--cpu-prof", "--cpu-prof-dir", prof_dir,
                           request.target, *request.arg_list()], {"timeout": 120})
    profiles = sorted(glob.glob(os.path.join(prof_dir, "*.cpuprofile")))
    if not profiles:
        print("✗ node produced no .cpuprofile — did the program crash before exit?")
        return
    with open(profiles[-1], encoding="utf-8") as fh:
        profile = json.load(fh)
    tree = parse_cpuprofile(profile, keep=request.filter)
    service._save(tree, request.out_file("ts"),
                  "ts/node call tree via V8 .cpuprofile (sampled; node:internal filtered)")


@CallTreeStrategies.register("unavailable")
def _(service, request):
    spec = LanguageRegistry.get(request.lang)
    service._unavailable(spec, "attach" if request.pid else "launch")
