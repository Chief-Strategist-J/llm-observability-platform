from unittest.mock import MagicMock, patch

from pytrace_features.lang_trace.index import LangTraceService, LangTraceRequest, SUPPORTED_LANGS
from pytrace_features.lang_trace.types import LANG_ALIASES


def _service() -> LangTraceService:
    return LangTraceService(MagicMock())


def test_supported_langs_cover_request():
    assert set(SUPPORTED_LANGS) == {"go", "rust", "java", "ts"}


def test_aliases_normalize_to_supported_langs():
    for alias, lang in LANG_ALIASES.items():
        assert LangTraceRequest(lang=alias).normalized_lang() == lang
        assert lang in SUPPORTED_LANGS


def test_trace_rejects_unsupported_language(capsys):
    _service().trace(LangTraceRequest(lang="cobol", pid=1))
    assert "Unsupported language" in capsys.readouterr().out


def test_trace_dispatches_to_language_method():
    svc = _service()
    svc.trace_go = MagicMock()
    svc.trace(LangTraceRequest(lang="golang", pid=42, duration=3.0))
    svc.trace_go.assert_called_once_with(42, 3.0, None)


def test_trace_with_cmd_launches_instead_of_attaching():
    svc = _service()
    svc._launch_traced = MagicMock()
    svc.trace(LangTraceRequest(lang="rust", cmd="cargo run"))
    svc._launch_traced.assert_called_once_with(["cargo", "run"], "rust")


def test_pick_returns_first_available_tool():
    svc = _service()
    with patch("pytrace_features.lang_trace.service.shutil.which",
               side_effect=lambda t: "/usr/bin/perf" if t == "perf" else None):
        assert svc._pick(["dlv", "perf", "strace"]) == "perf"
        assert svc._pick(["dlv"]) is None


def test_trace_go_prefers_delve():
    svc = _service()
    svc._exec = MagicMock(return_value=0)
    with patch("pytrace_features.lang_trace.service.shutil.which",
               side_effect=lambda t: "/usr/bin/dlv" if t == "dlv" else None):
        svc.trace_go(99, duration=5.0)
    argv = svc._exec.call_args[0][0]
    assert argv[:4] == ["dlv", "trace", "-p", "99"]


def test_trace_go_falls_back_to_simulated_when_no_tools(capsys):
    svc = _service()
    with patch("pytrace_features.lang_trace.service.shutil.which", return_value=None), \
         patch("pytrace_features.lang_trace.service.time.sleep"):
        svc.trace_go(99)
    assert "simulated" in capsys.readouterr().out


def test_trace_java_uses_jcmd_snapshot_and_jfr():
    svc = _service()
    svc._java_thread_snapshot = MagicMock()
    svc._java_flight_recording = MagicMock()
    with patch("pytrace_features.lang_trace.service.shutil.which",
               side_effect=lambda t: "/usr/bin/jcmd" if t == "jcmd" else None):
        svc.trace_java(7, duration=2.0)
    svc._java_thread_snapshot.assert_called_once_with(7)
    svc._java_flight_recording.assert_called_once_with(7, 2.0)


def test_trace_ts_reports_missing_pid(capsys):
    svc = _service()
    with patch("pytrace_features.lang_trace.service.os.kill", side_effect=ProcessLookupError):
        svc.trace_ts(424242)
    assert "No process with PID" in capsys.readouterr().out


def test_launch_traced_node_adds_cpu_prof_flag():
    svc = _service()
    svc._exec = MagicMock(return_value=0)
    with patch("pytrace_features.lang_trace.service.os.makedirs"):
        svc._launch_traced(["node", "app.js"], "ts")
    argv = svc._exec.call_args[0][0]
    assert argv[0] == "node" and "--cpu-prof" in argv and argv[-1] == "app.js"
