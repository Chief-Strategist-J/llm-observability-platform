"""Pure call-tree builders and renderers (no IO — unit-testable)."""
import re

# Bootstrap injected around a Python target: exact call/return tracing via
# stdlib sys.settrace, keeping only project frames (noise-free), with per-call
# durations. Configured through PYLOW_CALLTREE_* env vars.
PY_BOOTSTRAP = r'''
import os, runpy, sys, time

OUT = os.environ.get("PYLOW_CALLTREE_OUT", "pylow_calltree_python.txt")
BASE = os.environ.get("PYLOW_CALLTREE_FILTER", "")
MAX_DEPTH = int(os.environ.get("PYLOW_CALLTREE_DEPTH", "25"))

target = sys.argv[1]
sys.argv = sys.argv[1:]
base = BASE or os.path.dirname(os.path.abspath(target)) or os.getcwd()

events = []   # [depth, qualname, file, line, duration_ms]
stack = []    # (kept, t0, event_index)
depth = 0
_abs_cache = {}


def _abs(fname):
    cached = _abs_cache.get(fname)
    if cached is None:
        cached = fname if fname.startswith("<") else os.path.abspath(fname)
        _abs_cache[fname] = cached
    return cached


def tracer(frame, event, arg):
    global depth
    if event == "call":
        code = frame.f_code
        fname = _abs(code.co_filename)
        kept = fname.startswith(base) and depth < MAX_DEPTH
        idx = -1
        if kept:
            name = getattr(code, "co_qualname", code.co_name)
            idx = len(events)
            events.append([depth, name, fname, frame.f_lineno, None])
            depth += 1
        stack.append((kept, time.perf_counter(), idx))
        return tracer
    if event == "return" and stack:
        kept, t0, idx = stack.pop()
        if kept:
            depth -= 1
            if idx >= 0:
                events[idx][4] = (time.perf_counter() - t0) * 1000
    return tracer


sys.settrace(tracer)
try:
    runpy.run_path(target, run_name="__main__")
finally:
    sys.settrace(None)
    lines = []
    for d, name, fname, line, ms in events:
        try:
            rel = os.path.relpath(fname)
        except ValueError:
            rel = fname
        tail = "  [%.2fms]" % ms if ms is not None else ""
        lines.append("%s└─ %s  %s:%s%s" % ("  " * d, name, rel, line, tail))
    body = "\n".join(lines) if lines else "(no project-level calls captured)"
    print("\n── call tree (exact, project frames only) ──")
    print(body)
    with open(OUT, "w") as fh:
        fh.write(body + "\n")
    print("\n✓ call tree saved to %s" % OUT)
'''

NOISE_URL_PARTS = ("node:", "node_modules")


def _keep_frame(url: str, keep: str) -> bool:
    if not url or any(part in url for part in NOISE_URL_PARTS):
        return False
    return keep in url if keep else True


def parse_cpuprofile(profile: dict, keep: str = "") -> list:
    """Render a V8 .cpuprofile JSON dict into noise-filtered tree lines:
    '└─ functionName  path:line  [N samples]'. Internal/node_modules frames
    are removed; their children are promoted to the parent depth."""
    nodes = {n["id"]: n for n in profile.get("nodes", [])}
    children = {n["id"]: tuple(n.get("children", ())) for n in profile.get("nodes", [])}
    child_ids = {c for ids in children.values() for c in ids}
    lines: list = []

    def visit(node_id: int, depth: int) -> None:
        frame = nodes[node_id].get("callFrame", {})
        url = frame.get("url", "")
        kept = _keep_frame(url, keep)
        if kept:
            name = frame.get("functionName") or "(anonymous)"
            path = url[7:] if url.startswith("file://") else url
            line = frame.get("lineNumber", -1) + 1
            hits = nodes[node_id].get("hitCount", 0)
            suffix = f"  [{hits} samples]" if hits else ""
            lines.append(f"{'  ' * depth}└─ {name}  {path}:{line}{suffix}")
        for child in children.get(node_id, ()):
            visit(child, depth + 1 if kept else depth)

    for root in sorted(set(nodes) - child_ids):
        visit(root, 0)
    return lines


_JDB_THREAD_PREFIX = re.compile(r'^"?thread=[^",]*",?\s*')


def indent_jdb_trace(output: str, pkg_filter: str = "") -> list:
    """Turn jdb `trace go methods` entry/exit events into an indented tree."""
    lines: list = []
    depth = 0
    for raw in output.splitlines():
        stripped = raw.strip()
        if "Method exited:" in stripped:
            depth = max(depth - 1, 0)
            continue
        if "Method entered:" not in stripped:
            continue
        detail = stripped.split("Method entered:", 1)[1].strip()
        detail = _JDB_THREAD_PREFIX.sub("", detail.lstrip('"').strip())
        if pkg_filter and pkg_filter not in detail:
            continue
        lines.append(f"{'  ' * depth}└─ {detail}")
        depth += 1
    return lines
