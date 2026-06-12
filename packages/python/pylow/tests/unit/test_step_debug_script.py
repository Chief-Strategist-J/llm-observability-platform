from shared.lang import languages  # noqa: F401 — registers every LanguageSpec
from shared.lang.registry import LanguageRegistry
from pytrace_features.step_debug.script import (
    InteractiveStyles, break_commands, build_commands, parse_breakpoints, split_steps,
)


def _debugger(lang: str):
    return LanguageRegistry.get(lang).debugger


def test_parse_breakpoints_line_and_func():
    parsed = parse_breakpoints(("svc.py:12", "process_payment", "a/b/main.go:7"))
    assert parsed[0] == {"kind": "line", "file": "svc.py", "line": 12}
    assert parsed[1] == {"kind": "func", "func": "process_payment"}
    assert parsed[2] == {"kind": "line", "file": "a/b/main.go", "line": 7}


def test_break_commands_python():
    cmds, skipped = break_commands(_debugger("python"), ("svc.py:12", "handler"))
    assert cmds == ("break svc.py:12", "break handler")
    assert skipped == ()


def test_break_commands_node_skips_function_breaks():
    cmds, skipped = break_commands(_debugger("ts"), ("app.ts:3", "handler"))
    assert cmds == ("setBreakpoint('app.ts', 3)",)
    assert len(skipped) == 1


def test_build_commands_python_shape():
    spec = _debugger("python")
    cmds = build_commands(spec, ("svc.py:12",), ("total",), max_steps=2)
    assert cmds[0] == "break svc.py:12"
    assert cmds[1] == "continue"                  # run to first stop
    assert "p total" in cmds                      # watch expression captured
    assert cmds[-1] == "quit"
    assert cmds.count("continue") == 3            # run + 2 steps


def test_build_commands_gdb_includes_prelude():
    spec = _debugger("rust")
    cmds = build_commands(spec, ("main.rs:5",), (), max_steps=1)
    assert cmds[0] == "set confirm off"
    assert "break main.rs:5" in cmds
    assert "info locals" in cmds


def test_split_steps_with_real_pdb_marker_and_inline_prompt():
    marker = _debugger("python").hit_marker
    out = "header\n(Pdb) > /tmp/d.py(3)add()\nvals A\n(Pdb) > /tmp/d.py(3)add()\nvals B\n"
    steps = split_steps(out, marker)
    assert len(steps) == 2
    assert "vals A" in steps[0] and "vals B" in steps[1]


def test_split_steps_skip_initial_drops_entry_pause():
    marker = _debugger("python").hit_marker
    out = "> /tmp/d.py(1)<module>()\nsetup\n> /tmp/d.py(3)add()\nvals\n"
    steps = split_steps(out, marker, skip_initial=True)
    assert len(steps) == 1 and "vals" in steps[0]


def test_split_steps_truncates_at_end_marker():
    spec = _debugger("python")
    out = ("> /tmp/d.py(1)<module>()\nsetup\n"
           "> /tmp/d.py(3)add()\nreal stop\n"
           "The program finished and will be restarted\n"
           "> /tmp/d.py(3)add()\nphantom re-run\n")
    steps = split_steps(out, spec.hit_marker, skip_initial=True, end_marker=spec.end_marker)
    assert len(steps) == 1 and "real stop" in steps[0]


def test_split_steps_no_marker_or_no_hits():
    assert split_steps("nothing here", r"> .+\(\d+\)") == []
    assert split_steps("anything", "") == []


def test_interactive_styles_flag_inserts_before_target():
    argv, paste = InteractiveStyles.build("flag:-c", ["python3", "-m", "pdb", "svc.py"],
                                          ("break svc.py:3",))
    assert argv == ["python3", "-m", "pdb", "-c", "break svc.py:3", "svc.py"]
    assert paste == ()


def test_interactive_styles_init_file_placeholder():
    argv, paste = InteractiveStyles.build("init_file:--init", ["dlv", "debug", "m.go"],
                                          ("break m.go:3",))
    assert argv[-2:] == ["--init", "{init_file}"]
    assert paste == ("break m.go:3",)


def test_interactive_styles_manual_returns_paste_commands():
    argv, paste = InteractiveStyles.build("manual", ["jdb", "Demo"], ("stop at Demo:3",))
    assert argv == ["jdb", "Demo"]
    assert paste == ("stop at Demo:3",)
