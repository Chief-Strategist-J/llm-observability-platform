from unittest.mock import MagicMock, patch

from pytrace_features.uni.index import UniService


def _service() -> UniService:
    return UniService(MagicMock())


def test_detect_lang_file_by_extension():
    svc = _service()
    with patch("pytrace_features.uni.service.os.path.isdir", return_value=False):
        assert svc.detect_lang("server.go") == "go"
        assert svc.detect_lang("unknown.xyz") is None


def test_detect_lang_directory_by_marker():
    svc = _service()
    with patch("pytrace_features.uni.service.os.path.isdir", return_value=True), \
         patch("pytrace_features.uni.service.os.listdir", return_value=["Cargo.toml", "src"]):
        assert svc.detect_lang("/proj") == "rust"


def test_build_unknown_language_fails(capsys):
    svc = _service()
    with patch("pytrace_features.uni.service.os.path.isdir", return_value=False):
        assert svc.build("notes.txt") == 1
    assert "Could not detect language" in capsys.readouterr().out


def test_build_go_file_invokes_go_build():
    svc = _service()
    svc._exec = MagicMock(return_value=0)
    with patch("pytrace_features.uni.service.os.path.isdir", return_value=False):
        assert svc.build("main.go") == 0
    assert svc._exec.call_args[0][0] == ["go", "build", "main.go"]


def test_run_python_invokes_python3():
    svc = _service()
    svc._exec = MagicMock(return_value=0)
    with patch("pytrace_features.uni.service.os.path.isdir", return_value=False):
        svc.run("svc.py", ["--port", "8000"])
    assert svc._exec.call_args[0][0] == ["python3", "svc.py", "--port", "8000"]


def test_debug_non_tty_prints_command_instead_of_launching(capsys):
    svc = _service()
    with patch("pytrace_features.uni.service.os.path.isdir", return_value=False), \
         patch("pytrace_features.uni.service.sys.stdin") as stdin, \
         patch("pytrace_features.uni.service.subprocess.call") as call:
        stdin.isatty.return_value = False
        assert svc.debug("svc.py") == 0
        call.assert_not_called()
    assert "python3 -m pdb svc.py" in capsys.readouterr().out


def test_trace_delegates_to_lang_trace_for_go_pid():
    svc = _service()
    svc.lang_trace = MagicMock()
    with patch("pytrace_features.uni.service.os.path.isdir", return_value=False):
        assert svc.trace("main.go", pid=77, duration=4.0) == 0
    request = svc.lang_trace.trace.call_args[0][0]
    assert (request.lang, request.pid, request.duration, request.cmd) == ("go", 77, 4.0, None)


def test_trace_without_pid_launches_target():
    svc = _service()
    svc.lang_trace = MagicMock()
    with patch("pytrace_features.uni.service.os.path.isdir", return_value=False):
        svc.trace("app.ts")
    request = svc.lang_trace.trace.call_args[0][0]
    assert request.cmd == "node app.ts"


def test_all_stops_on_build_failure():
    svc = _service()
    svc.detect = MagicMock(return_value="go")
    svc.build = MagicMock(return_value=2)
    svc.run = MagicMock()
    assert svc.all("main.go") == 2
    svc.run.assert_not_called()


def test_all_happy_path_runs_every_stage():
    svc = _service()
    svc.detect = MagicMock(return_value="go")
    svc.build = MagicMock(return_value=0)
    svc.run = MagicMock(return_value=0)
    svc.trace = MagicMock()
    assert svc.all("main.go", do_trace=True) == 0
    svc.trace.assert_called_once_with("main.go")
