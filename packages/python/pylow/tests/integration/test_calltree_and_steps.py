"""Integration: real call-tree capture and real pdb step-snapshots on a tmp script."""
from unittest.mock import MagicMock

from pytrace_features.call_tree.index import CallTreeService, CallTreeRequest
from pytrace_features.step_debug.index import StepDebugService, DebugRequest

DEMO = """\
def add(a, b):
    total = a + b
    return total

def main():
    x = add(2, 3)
    y = add(10, 20)
    print(x + y)

main()
"""


def _write_demo(tmp_path):
    script = tmp_path / "demo.py"
    script.write_text(DEMO)
    return script


def test_python_calltree_exact_tree_with_file_line(tmp_path, capsys):
    script = _write_demo(tmp_path)
    out_file = tmp_path / "tree.txt"
    CallTreeService(MagicMock()).trace(
        CallTreeRequest(target=str(script), out=str(out_file)))
    printed = capsys.readouterr().out
    assert "python via python_settrace" in printed
    tree = out_file.read_text()
    assert "main" in tree and "add" in tree
    assert "demo.py:1" in tree                       # exact file:line for add()
    assert "ms]" in tree                             # durations captured
    # noise-free: nothing from the stdlib/runpy machinery
    assert "runpy" not in tree


def test_python_debug_steps_saves_values_per_stop(tmp_path, capsys):
    script = _write_demo(tmp_path)
    out_dir = tmp_path / "steps"
    rc = StepDebugService(MagicMock()).debug_steps(DebugRequest(
        target=str(script),
        breaks=(f"{script}:2",),                     # inside add()
        watches=("a", "b"),
        out=str(out_dir),
        max_steps=10,
    ))
    assert rc == 0
    printed = capsys.readouterr().out
    assert "2 stop(s) captured" in printed           # add() called twice — not phantom restarts
    step1 = (out_dir / "step_001.txt").read_text()
    step2 = (out_dir / "step_002.txt").read_text()
    assert "demo.py(2)add()" in step1
    assert "a = 2" in step1 and "b = 3" in step1     # exact values at stop 1
    assert "a = 10" in step2 and "b = 20" in step2   # exact values at stop 2
    assert (out_dir / "summary.txt").exists()
    assert (out_dir / "transcript.txt").exists()


def test_debug_steps_without_breakpoints_fails_clearly(tmp_path, capsys):
    script = _write_demo(tmp_path)
    rc = StepDebugService(MagicMock()).debug_steps(DebugRequest(target=str(script)))
    assert rc == 1
    assert "--break" in capsys.readouterr().out


def test_debug_steps_breakpoint_never_hit(tmp_path, capsys):
    script = _write_demo(tmp_path)
    out_dir = tmp_path / "steps"
    rc = StepDebugService(MagicMock()).debug_steps(DebugRequest(
        target=str(script), breaks=("nonexistent_function",), out=str(out_dir), max_steps=3))
    assert rc == 1
    assert "No breakpoint was hit" in capsys.readouterr().out
    assert (out_dir / "transcript.txt").exists()


def test_debug_non_tty_prints_ready_command(tmp_path, capsys):
    script = _write_demo(tmp_path)
    rc = StepDebugService(MagicMock()).debug(DebugRequest(
        target=str(script), breaks=(f"{script}:2",)))
    assert rc == 0
    printed = capsys.readouterr().out
    assert "-m pdb -c" in printed and f"break {script}:2" in printed
