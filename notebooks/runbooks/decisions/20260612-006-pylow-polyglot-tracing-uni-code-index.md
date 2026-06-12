# ADR-006 — pylow Polyglot Tracing, Universal `uni` Tool, and Code Index

| Field       | Value                                                             |
|-------------|-------------------------------------------------------------------|
| **ID**      | 006                                                               |
| **Date**    | 2026-06-12                                                        |
| **Status**  | accepted                                                          |
| **Deciders**| LLM Observability Platform Team                                   |
| **Package** | `packages/python/pylow`                                           |

---

## Context

pylow's runtime tracing covered Python only, while daily work spans Go, Rust, Java, and TypeScript services. Three needs were raised:
1. Tracing parity for Go / Rust / Java / TypeScript without writing tracers from scratch.
2. One universal command that compiles, runs, debugs, and traces any target and shows exactly where the code breaks — no per-language muscle memory.
3. A persistent code index so symbol lookups never rescan the whole codebase.

---

## Decision

- **Orchestrate, never re-implement (per critical rule "use existing library/tools")**: the new `lang_trace` feature shells out to each ecosystem's native tooling with runtime backend selection — Go: `dlv trace` → `perf` → `strace`; Rust: `perf` → `strace`; Java: `jcmd Thread.print` + JFR → `jstack`; Node/TS: SIGUSR1 V8 inspector + `perf`/`strace`. Every external command is echoed before execution; when no tooling exists the service prints a simulated sample (consistent with the existing `pycall` fallback pattern).
- **`uni` as a thin façade**: language detection (extension map + project markers) routes to native toolchains (`go`, `cargo`, `javac`/`mvn`/`gradle`, `tsc`/`tsx`/`ts-node`, `node`, `python3`) for build/run/debug, and delegates tracing to `lang_trace` **via its feature index only** (feature-dependency rule). Compiler/runtime errors of all languages are normalized by pure regex parsers into one `file:line  message` issue list.
- **Code index on SQLite, ctags-preferred**: `.pylow_index.db` at the indexed root; incremental by file mtime with deleted-file pruning. Universal-ctags is used when installed; otherwise built-in pure-regex extractors (unit-testable, no IO) cover Python/Go/Rust/Java/TS/JS. Search ranks exact > prefix > substring.
- **Feature anatomy & contracts-first**: each feature ships `contracts/v1.yaml` + `changelog.md` written before code, an `index.py` public surface, pure logic split into `detect.py`/`extractors.py`/`types.py` for IO-free unit tests, and registration in both CLI (`controller.py`) and MCP (`server.py`). A `feature-registry.yaml` was introduced for pylow (features added from 2026-06-12 onward).

---

## Failure-First System Building (FFSB) Analysis

### Mode 1: Required native tool missing on the host
- **Symptom**: `dlv`/`perf`/`jcmd` absent → tracing silently does nothing.
- **Prevention**: priority-ordered backend fallback chains, `uni doctor` reports installed/missing toolchains per language, and an explicit simulated-output fallback labeled as simulated.

### Mode 2: Attaching tracers disturbs or kills the target process
- **Prevention**: attach paths are read-only (perf sampling, strace -c, jcmd diagnostics). The only signal ever sent is SIGUSR1 to Node (documented inspector activation); PermissionError and ProcessLookupError are caught and reported instead of raised.

### Mode 3: Hung external commands block the CLI/MCP server forever
- **Prevention**: all capture-mode invocations carry timeouts (5–30s); sampling windows are bounded by `--duration`; strace is detached via SIGINT after the window.

### Mode 4: Index corruption or staleness misleads navigation
- **Prevention**: mtime-based incremental rebuilds with deleted-file pruning; `--force` full reindex escape hatch; the DB is a per-machine artifact excluded from git (`.pylow_index.db` in `.gitignore`).

### Mode 5: Error-format drift across compiler versions
- **Prevention**: error normalization is pure (`uni/detect.py:parse_issues`) with one regex per format and unit tests per language; raw tool output is always printed in full above the normalized issue list, so nothing is hidden if a regex misses.
