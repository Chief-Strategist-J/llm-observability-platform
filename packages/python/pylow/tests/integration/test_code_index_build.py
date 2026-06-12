"""Integration: CodeIndexService against a real (tmp) filesystem and SQLite."""
import os
import sqlite3
import time
from unittest.mock import MagicMock

from pytrace_features.code_index.index import CodeIndexService
from pytrace_features.code_index.service import DB_NAME


def _make_repo(root):
    (root / "svc.py").write_text("def process_payment():\n    pass\n")
    (root / "main.go").write_text("func HandleOrder() {}\n")
    sub = root / "node_modules"
    sub.mkdir()
    (sub / "skip.js").write_text("function skipped() {}\n")


def _service() -> CodeIndexService:
    svc = CodeIndexService(MagicMock())
    svc._ctags_has_json = lambda: False  # force builtin extractors for determinism
    return svc


def test_build_search_and_stats(tmp_path, capsys):
    _make_repo(tmp_path)
    svc = _service()
    svc.build(str(tmp_path))
    assert os.path.exists(tmp_path / DB_NAME)
    out = capsys.readouterr().out
    assert "2 files" in out and "skip" not in out

    svc.search("process_payment", str(tmp_path))
    out = capsys.readouterr().out
    assert "svc.py:1" in out

    svc.stats(str(tmp_path))
    out = capsys.readouterr().out
    assert "python" in out and "go" in out


def test_incremental_build_skips_unchanged(tmp_path, capsys):
    _make_repo(tmp_path)
    svc = _service()
    svc.build(str(tmp_path))
    capsys.readouterr()
    svc.build(str(tmp_path))
    assert "changed: 0" in capsys.readouterr().out


def test_rebuild_picks_up_modified_and_deleted_files(tmp_path, capsys):
    _make_repo(tmp_path)
    svc = _service()
    svc.build(str(tmp_path))
    capsys.readouterr()

    (tmp_path / "svc.py").write_text("def process_payment():\n    pass\n\ndef refund_payment():\n    pass\n")
    os.utime(tmp_path / "svc.py", (time.time() + 5, time.time() + 5))
    (tmp_path / "main.go").unlink()
    svc.build(str(tmp_path))
    out = capsys.readouterr().out
    assert "changed: 1" in out and "deleted: 1" in out

    conn = sqlite3.connect(tmp_path / DB_NAME)
    names = {r[0] for r in conn.execute("SELECT name FROM symbols")}
    conn.close()
    assert names == {"process_payment", "refund_payment"}


def test_search_without_index_explains(tmp_path, capsys):
    _service().search("anything", str(tmp_path))
    assert "index-build" in capsys.readouterr().out
