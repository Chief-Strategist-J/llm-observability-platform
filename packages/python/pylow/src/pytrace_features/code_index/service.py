"""Persistent incremental symbol index — never scan the codebase from scratch again.

`index-build` walks the tree once, extracts symbols (universal-ctags when
installed, built-in extractors otherwise) and stores them in SQLite at
<root>/.pylow_index.db. Re-runs only touch files whose mtime changed.
`index-search` answers symbol lookups instantly from the index.
"""
import json
import os
import shutil
import sqlite3
import subprocess

from pytrace_features.code_index.extractors import (
    SKIP_DIRS, Symbol, extract_symbols, lang_for_file, rank_matches,
)
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

DB_NAME = ".pylow_index.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS files(
    path TEXT PRIMARY KEY, lang TEXT, mtime REAL, symbol_count INTEGER);
CREATE TABLE IF NOT EXISTS symbols(
    id INTEGER PRIMARY KEY, name TEXT, kind TEXT, lang TEXT,
    path TEXT, line INTEGER, signature TEXT);
CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
CREATE INDEX IF NOT EXISTS idx_symbols_path ON symbols(path);
"""


class CodeIndexService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    # ── storage ───────────────────────────────────────────────────────────

    def _connect(self, root: str) -> sqlite3.Connection:
        conn = sqlite3.connect(os.path.join(root, DB_NAME))
        conn.executescript(_SCHEMA)
        return conn

    # ── build ─────────────────────────────────────────────────────────────

    def build(self, path: str = ".", force: bool = False) -> None:
        root = os.path.abspath(path)
        if not os.path.isdir(root):
            print(f"✗ Not a directory: {root}")
            return
        conn = self._connect(root)
        known = dict(conn.execute("SELECT path, mtime FROM files"))
        seen, changed = set(), []
        for filepath, lang, mtime in self._walk(root):
            rel = os.path.relpath(filepath, root)
            seen.add(rel)
            if not force and known.get(rel) == mtime:
                continue
            changed.append((rel, filepath, lang, mtime))
        deleted = set(known) - seen
        backend = "ctags" if shutil.which("ctags") and self._ctags_has_json() else "builtin"
        print(f"Indexing {root}")
        print(f"  backend: {backend} | changed: {len(changed)} | unchanged: {len(seen) - len(changed)} | deleted: {len(deleted)}")
        for rel in deleted:
            conn.execute("DELETE FROM symbols WHERE path = ?", (rel,))
            conn.execute("DELETE FROM files WHERE path = ?", (rel,))
        total = 0
        for rel, filepath, lang, mtime in changed:
            symbols = self._extract(filepath, lang, backend)
            conn.execute("DELETE FROM symbols WHERE path = ?", (rel,))
            conn.executemany(
                "INSERT INTO symbols(name, kind, lang, path, line, signature) VALUES(?,?,?,?,?,?)",
                [(s.name, s.kind, lang, rel, s.line, s.signature) for s in symbols])
            conn.execute("INSERT OR REPLACE INTO files(path, lang, mtime, symbol_count) VALUES(?,?,?,?)",
                         (rel, lang, mtime, len(symbols)))
            total += len(symbols)
        conn.commit()
        files, syms = conn.execute("SELECT COUNT(*), (SELECT COUNT(*) FROM symbols) FROM files").fetchone()
        conn.close()
        print(f"✓ Index ready: {files} files, {syms} symbols ({total} added/updated) → {os.path.join(root, DB_NAME)}")

    def _walk(self, root: str):
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".egg-info")]
            for fname in filenames:
                lang = lang_for_file(fname)
                if not lang:
                    continue
                filepath = os.path.join(dirpath, fname)
                try:
                    yield filepath, lang, os.stat(filepath).st_mtime
                except OSError:
                    continue

    def _ctags_has_json(self) -> bool:
        try:
            out = subprocess.run(["ctags", "--version"], capture_output=True, text=True, timeout=5)
            return "Universal Ctags" in out.stdout
        except Exception:
            return False

    def _extract(self, filepath: str, lang: str, backend: str) -> list[Symbol]:
        if backend == "ctags":
            symbols = self._extract_ctags(filepath)
            if symbols is not None:
                return symbols
        try:
            with open(filepath, encoding="utf-8", errors="replace") as fh:
                return extract_symbols(fh.read(), lang)
        except OSError:
            return []

    def _extract_ctags(self, filepath: str) -> list[Symbol] | None:
        try:
            out = subprocess.run(
                ["ctags", "--output-format=json", "--fields=+n", "-f", "-", filepath],
                capture_output=True, text=True, timeout=30)
        except Exception:
            return None
        if out.returncode != 0:
            return None
        symbols = []
        for line in out.stdout.splitlines():
            try:
                tag = json.loads(line)
            except json.JSONDecodeError:
                continue
            if tag.get("_type") == "tag" and tag.get("name") and tag.get("line"):
                symbols.append(Symbol(tag["name"], tag.get("kind", "symbol"),
                                      int(tag["line"]), tag.get("pattern", "")[:120]))
        return symbols

    # ── search / stats ────────────────────────────────────────────────────

    def search(self, query: str, path: str = ".", filters: dict | None = None) -> None:
        root = os.path.abspath(path)
        db = os.path.join(root, DB_NAME)
        if not os.path.exists(db):
            print(f"✗ No index at {db} — run `pylow index-build {path}` first.")
            return
        filters = filters or {}
        sql = "SELECT name, kind, lang, path, line, signature FROM symbols WHERE name LIKE ?"
        params: list = [f"%{query}%"]
        for col in ("lang", "kind"):
            if filters.get(col):
                sql += f" AND {col} = ?"
                params.append(filters[col])
        conn = sqlite3.connect(db)
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        limit = int(filters.get("limit") or 25)
        order = rank_matches(query, [r[0] for r in rows])[:limit]
        if not order:
            print(f"No symbols matching '{query}'.")
            return
        print(f"{len(order)} match(es) for '{query}' (of {len(rows)} candidates):\n")
        for i in order:
            name, kind, lang, rel, line, _sig = rows[i]
            print(f"  {name:<32} {kind:<10} {lang:<7} {rel}:{line}")

    def stats(self, path: str = ".") -> None:
        root = os.path.abspath(path)
        db = os.path.join(root, DB_NAME)
        if not os.path.exists(db):
            print(f"✗ No index at {db} — run `pylow index-build {path}` first.")
            return
        conn = sqlite3.connect(db)
        files, syms = conn.execute("SELECT COUNT(*), (SELECT COUNT(*) FROM symbols) FROM files").fetchone()
        print(f"Index: {db}\n  files: {files} | symbols: {syms}\n\n  per language:")
        for lang, n_files, n_syms in conn.execute(
                "SELECT lang, COUNT(*), SUM(symbol_count) FROM files GROUP BY lang ORDER BY 3 DESC"):
            print(f"    {lang:<8} {n_files:>5} files  {n_syms or 0:>7} symbols")
        print("\n  per kind:")
        for kind, n in conn.execute("SELECT kind, COUNT(*) FROM symbols GROUP BY kind ORDER BY 2 DESC"):
            print(f"    {kind:<10} {n:>7}")
        conn.close()
