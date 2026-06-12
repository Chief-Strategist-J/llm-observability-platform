"""Declarative spec types for the language registry (pure data, no IO).

Everything a language needs — detection, toolchain stage rules, tracer
backends, call-tree backends, debugger behavior — is described as data.
Engines interpret these specs; they never branch on language names.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class StageRule:
    """Rules-as-data for a toolchain stage. First rule whose predicates all
    pass wins (declaration order = priority). Placeholders: {target} {args}
    {extra} {tool}. `strategy` names a StageStrategies entry for compound
    behavior instead of a single argv."""
    when: tuple = ()                 # predicate names, e.g. ("is_dir",), ("tool:tsx",), ("has:Cargo.toml",)
    argv: tuple = ()
    strategy: str = ""
    cwd_is_target: bool = False      # run with cwd=<target> (directory targets)
    note: str = ""                   # printed before exec when the rule fires


@dataclass(frozen=True)
class TracerBackend:
    """One runtime-tracing backend. tool='' means always available."""
    tool: str
    strategy: str
    params: tuple = ()               # ((key, value), ...) — kept hashable/frozen


@dataclass(frozen=True)
class CallTreeBackend:
    """One call-tree backend. tool='' means always available."""
    tool: str
    strategy: str
    mode: str = "launch"             # launch | attach | both
    params: tuple = ()


@dataclass(frozen=True)
class DebuggerSpec:
    """Everything the generic step-debug engine needs to drive a native
    terminal debugger. Command templates use {file} {line} {func} {expr}."""
    tools: tuple                     # priority-ordered binaries, first installed wins
    argv: tuple                      # ("{tool}", "--nx", "-q", "{target}")
    prelude: tuple = ()              # commands sent before breakpoints
    break_line: str = ""             # "break {file}:{line}"
    break_func: str = ""             # "break {func}"
    run: str = ""                    # command that starts/continues to the first stop
    locals_cmds: tuple = ()          # commands that dump variables at a stop
    watch_cmd: str = ""              # "print {expr}"
    cont: str = ""                   # continue to next stop
    quit: str = ""                   # exit the debugger
    hit_marker: str = ""             # regex marking "stopped at a breakpoint" lines
    end_marker: str = ""             # literal line fragment marking program exit (truncates transcript)
    skip_initial_stop: bool = False  # debugger pauses on entry before any breakpoint (pdb, node)
    prepare: tuple = ()              # StageRules run before debugging (e.g. javac -g)
    interactive_style: str = "manual"  # flag:-c | flag:-ex | init_file:--init | manual
    note: str = ""                   # caveat shown to the user (e.g. node value inspection)


@dataclass(frozen=True)
class LanguageSpec:
    """One language = one of these. Register it and every engine
    (uni, lang_trace, call_tree, step_debug) supports the language."""
    name: str
    aliases: tuple = ()
    extensions: tuple = ()
    markers: tuple = ()              # project marker filenames
    stages: tuple = ()               # ((stage_name, (StageRule, ...)), ...)
    tracers: tuple = ()              # (TracerBackend, ...) priority-ordered
    calltree: tuple = ()             # (CallTreeBackend, ...) priority-ordered
    debugger: DebuggerSpec | None = None
    launch_cmd: str = ""             # how `trace` launches this language: "go run {target}"
    trace_as: str = ""               # delegate tracing to another spec (js -> ts)
    error_patterns: tuple = ()       # regex strings -> unified file:line issues

    def stage_rules(self, stage: str) -> tuple:
        return dict(self.stages).get(stage, ())
