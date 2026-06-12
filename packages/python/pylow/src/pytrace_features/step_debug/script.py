"""Pure command-script builders for the generic debugger engine (no IO).

Given a DebuggerSpec (declarative, from shared/lang/languages.py) these
functions build the exact command sequence piped to the native debugger and
split its transcript back into per-breakpoint steps. The engine never
contains per-language conditionals — the spec is the behavior.
"""
import re


def parse_breakpoints(breaks: tuple) -> list:
    """'file:line' → {'kind': 'line', 'file', 'line'}; anything else → function."""
    parsed = []
    for raw in breaks:
        head, _, tail = raw.rpartition(":")
        if head and tail.isdigit():
            parsed.append({"kind": "line", "file": head, "line": int(tail)})
        else:
            parsed.append({"kind": "func", "func": raw})
    return parsed


def break_commands(spec, breaks: tuple) -> tuple:
    """Returns (commands, skipped) — skipped lists breakpoints the spec
    has no template for (e.g. function breaks under node inspect)."""
    templates = {"line": spec.break_line, "func": spec.break_func}
    commands, skipped = [], []
    for bp in parse_breakpoints(breaks):
        template = templates[bp["kind"]]
        if not template:
            skipped.append(bp)
            continue
        commands.append(template.format(**bp))
    return tuple(commands), tuple(skipped)


def step_dump_commands(spec, watches: tuple) -> tuple:
    watch_cmds = tuple(spec.watch_cmd.format(expr=expr) for expr in watches if spec.watch_cmd)
    return (*spec.locals_cmds, *spec.post_dump_cmds, *watch_cmds)


def build_commands(spec, breaks: tuple, watches: tuple, max_steps: int) -> list:
    """Full non-interactive script: prelude → breakpoints → run →
    (dump values, continue) × max_steps → quit."""
    bp_cmds, _ = break_commands(spec, breaks)
    per_stop = step_dump_commands(spec, watches)
    commands = [*spec.prelude, *bp_cmds, spec.run]
    for _ in range(max_steps):
        commands.extend((*per_stop, spec.cont))
    commands.append(spec.quit)
    return [c for c in commands if c]


def split_steps(output: str, hit_marker: str, skip_initial: bool = False,
                end_marker: str = "") -> list:
    """Cut the debugger transcript into chunks, one per breakpoint stop.
    Transcript is truncated at end_marker first (pdb restarts the program
    after exit; without truncation later chunks would be phantom re-runs)."""
    if not hit_marker:
        return []
    if end_marker:
        output = output.split(end_marker)[0]
    marker = re.compile(hit_marker, re.MULTILINE)
    starts = [m.start() for m in marker.finditer(output)]
    chunks = [output[s:e].rstrip() for s, e in zip(starts, [*starts[1:], len(output)])]
    return chunks[1:] if skip_initial and chunks else chunks


class InteractiveStyles:
    """How each debugger accepts pre-set commands (declarative guide rule 1)."""
    _styles: dict = {}

    @classmethod
    def register(cls, name):
        def decorator(fn):
            cls._styles[name] = fn
            return fn
        return decorator

    @classmethod
    def build(cls, style: str, argv: list, commands: tuple):
        """Returns (argv, paste_commands). paste_commands non-empty means the
        user must enter them manually after the debugger starts."""
        name, _, flag = style.partition(":")
        return cls._styles.get(name, cls._styles["manual"])(argv, commands, flag)


@InteractiveStyles.register("flag")
def _(argv, commands, flag):
    flags = [token for cmd in commands for token in (flag, cmd)]
    return [*argv[:-1], *flags, argv[-1]], ()


@InteractiveStyles.register("init_file")
def _(argv, commands, flag):
    # the service writes the init file and substitutes its path
    return [*argv, flag, "{init_file}"], commands


@InteractiveStyles.register("manual")
def _(argv, commands, flag):
    return list(argv), commands
