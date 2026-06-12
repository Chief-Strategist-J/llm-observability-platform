"""Pure-terminal, code-level debugging for every registered language.

One generic engine drives the native debugger (pdb / dlv / rust-gdb / jdb /
node inspect) from the declarative DebuggerSpec in shared/lang/languages.py:

  debug        interactive session with breakpoints pre-set
  debug_steps  run to every breakpoint, capture variable values, save each
               stop as <out>/step_NNN.txt + summary.txt

No per-language conditionals anywhere — adding a language is a DebuggerSpec.
"""
import os
import subprocess
import sys
import tempfile

from pytrace_features.step_debug.script import (
    InteractiveStyles, break_commands, split_steps, step_dump_commands,
)
from pytrace_features.step_debug.types import DebugRequest
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter
from shared.lang import languages  # noqa: F401 — registers every LanguageSpec
from shared.lang.registry import LanguageRegistry, PredicateRegistry, StageContext, format_argv, pick_tool
from shared.utils.paced_process import PacedPlan, run_paced


class StepDebugService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    # ── resolution ────────────────────────────────────────────────────────

    def _resolve(self, request: DebugRequest):
        """Returns (spec, debugger_spec, tool, argv) or None with an explanation."""
        lang = request.lang or LanguageRegistry.lang_for_extension(request.target)
        spec = LanguageRegistry.get(lang) if lang else None
        if spec and spec.trace_as:
            spec = LanguageRegistry.get(spec.trace_as)
        if spec is None or spec.debugger is None:
            print(f"✗ No debugger registered for {request.target!r} — pass --lang "
                  f"(supported: {', '.join(LanguageRegistry.names())})")
            return None
        debugger = spec.debugger
        tool = pick_tool(debugger.tools)
        if tool is None:
            print(f"✗ None of {', '.join(debugger.tools)} found on PATH — install one first.")
            return None
        mapping = {
            "tool": tool,
            "target": request.target,
            "target_stem": os.path.splitext(os.path.basename(request.target))[0],
        }
        argv = format_argv(debugger.argv, mapping)
        if debugger.note:
            print(f"note: {debugger.note}")
        self._prepare(debugger, request.target, mapping)
        return spec, debugger, tool, argv

    def _prepare(self, debugger, target: str, mapping: dict) -> None:
        ctx = StageContext(target=target, is_dir=os.path.isdir(target))
        for rule in debugger.prepare:
            if PredicateRegistry.passes(rule.when, ctx):
                self._exec_inline(format_argv(rule.argv, mapping))

    def _exec_inline(self, argv: list) -> None:
        print(f"→ exec: {' '.join(argv)}")
        subprocess.run(argv)

    # ── interactive debugging ─────────────────────────────────────────────

    def debug(self, request: DebugRequest) -> int:
        resolved = self._resolve(request)
        if resolved is None:
            return 1
        spec, debugger, tool, argv = resolved
        bp_cmds, skipped = break_commands(debugger, request.breaks)
        self._warn_skipped(skipped)
        final_argv, paste = InteractiveStyles.build(
            debugger.interactive_style, argv, (*debugger.prelude, *bp_cmds))
        final_argv = self._materialize_init_file(final_argv, paste, debugger)
        print(f"[debug] {spec.name} via {tool}")
        if paste and debugger.interactive_style == "manual" and bp_cmds:
            print("Paste these once the debugger prompt appears:")
            for cmd in paste:
                print(f"    {cmd}")
        if not sys.stdin.isatty():
            print(f"Interactive debugger (run in a terminal): {' '.join(final_argv)}")
            return 0
        print(f"→ exec: {' '.join(final_argv)}")
        return subprocess.call(final_argv)

    def _materialize_init_file(self, argv: list, commands: tuple, debugger) -> list:
        if "{init_file}" not in argv:
            return argv
        path = os.path.join(tempfile.gettempdir(), "pylow_debug_init")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(commands) + "\n")
        return [token.replace("{init_file}", path) for token in argv]

    def _warn_skipped(self, skipped: tuple) -> None:
        for bp in skipped:
            print(f"  ⚠ breakpoint {bp.get('func') or bp} not supported by this debugger — skipped")

    # ── step snapshots ────────────────────────────────────────────────────

    def debug_steps(self, request: DebugRequest) -> int:
        resolved = self._resolve(request)
        if resolved is None:
            return 1
        spec, debugger, tool, argv = resolved
        if not request.breaks:
            print("✗ debug-steps needs at least one --break (file:line or function)")
            return 1
        bp_cmds, skipped = break_commands(debugger, request.breaks)
        self._warn_skipped(skipped)
        setup = (*debugger.prelude, *bp_cmds, debugger.run)
        per_stop = (*step_dump_commands(debugger, request.watches), debugger.cont)
        print(f"[debug-steps] {spec.name} via {tool} — script:")
        for cmd in setup:
            print(f"    {cmd}")
        print(f"    at each stop: {' | '.join(per_stop)}  (× max {request.max_steps}, then {debugger.quit})")
        print(f"→ exec: {' '.join(argv)}  (commands paced on the debugger's stop markers)")
        output = run_paced(argv, PacedPlan(
            setup=setup, per_stop=per_stop,
            hit_marker=debugger.hit_marker, end_marker=debugger.end_marker,
            quit_cmd=debugger.quit, skip_initial_stop=debugger.skip_initial_stop,
            max_steps=request.max_steps))
        steps = split_steps(output, debugger.hit_marker,
                            debugger.skip_initial_stop, debugger.end_marker)
        return self._write_steps(steps, output, request)

    def _write_steps(self, steps: list, raw_output: str, request: DebugRequest) -> int:
        os.makedirs(request.out, exist_ok=True)
        with open(os.path.join(request.out, "transcript.txt"), "w", encoding="utf-8") as fh:
            fh.write(raw_output)
        if not steps:
            print("\n✗ No breakpoint was hit — check file paths/line numbers.")
            print(f"  Full debugger transcript: {request.out}/transcript.txt")
            return 1
        summary = []
        for n, chunk in enumerate(steps, start=1):
            location = chunk.splitlines()[0].strip()
            path = os.path.join(request.out, f"step_{n:03d}.txt")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(f"# step {n} — {location}\n\n{chunk}\n")
            summary.append(f"step {n:03d}  {location}")
        with open(os.path.join(request.out, "summary.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(summary) + "\n")
        print(f"\n✓ {len(steps)} stop(s) captured → {request.out}/")
        for line in summary:
            print(f"  {line}")
        print(f"  values per stop: {request.out}/step_NNN.txt | full log: {request.out}/transcript.txt")
        return 0
