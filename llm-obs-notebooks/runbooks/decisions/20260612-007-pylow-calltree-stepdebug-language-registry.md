# ADR-007 — pylow Exact Call Trees, Step Debugging, and the Declarative Language Registry

| Field       | Value                                                             |
|-------------|-------------------------------------------------------------------|
| **ID**      | 007                                                               |
| **Date**    | 2026-06-12                                                        |
| **Status**  | accepted                                                          |
| **Deciders**| LLM Observability Platform Team                                   |
| **Package** | `packages/python/pylow`                                           |

---

## Context

After ADR-006 added per-language tracing, two deeper needs emerged plus one architectural requirement:
1. **Exact call trees** — what the code does internally, every function with its `file:line`, noise removed, for Python/Go/Rust/Java/TS.
2. **Pure terminal debugging with per-step value snapshots** — set breakpoints, stop, inspect, and persist each stop's variable values as text files.
3. **No language conditionals** — adding a language must be a registry entry, never an engine edit (declarative-code rule: "checking WHAT something is → Registry").

---

## Decision

- **Single declarative language registry** (`src/shared/lang/`): every language is one `LanguageSpec` — detection (extensions/markers), toolchain `StageRule`s (rules-as-data with named predicates: `is_dir`, `has:<marker>`, `tool:<bin>`, `ext:<suffix>`), `TracerBackend`/`CallTreeBackend` priority chains, and a `DebuggerSpec` (break/run/locals/continue/quit templates, stop markers). `uni`, `lang_trace`, `call_tree`, and `step_debug` were all rewritten to interpret specs through registries (`LanguageRegistry`, `PredicateRegistry`, `TracerStrategies`, `CallTreeStrategies`, `StageStrategies`, `InteractiveStyles`). The 195-test suite pinned behavior through the refactor.
- **call_tree backends are native tools, never re-implementations**: Python = stdlib trace bootstrap (exact + per-call ms); Go = `dlv trace`; Java = `jdb` method trace (exact entry/exit) or JFR for attach; Rust = uftrace/perf; TS = `node --cpu-prof` parsed from `.cpuprofile` JSON. Sampled backends are labeled as sampled. Output is always `function  file:line` lines, project-frames only, printed and saved to a text file.
- **step_debug is one generic engine over DebuggerSpecs**: it builds the command script from templates, runs the native debugger, splits the transcript on the spec's `hit_marker`, truncates at `end_marker` (pdb restarts programs after exit — without truncation steps would be phantom re-runs), and writes `step_NNN.txt` + `summary.txt` + `transcript.txt`.
- **Marker-paced stdin driver** (`shared/utils/paced_process.py`): blind piping fails for jdb (it consumes queued commands while the VM runs — "Nothing suspended"). The driver sends the per-stop batch only after the stop marker appears in output, making one engine reliable across pdb/dlv/gdb/jdb/node-inspect.

---

## Failure-First System Building (FFSB) Analysis

### Mode 1: Debugger consumes commands while the program is running
- **Symptom**: jdb "Nothing suspended"; value dumps lost; empty snapshots.
- **Prevention**: marker-paced driver — per-stop commands are sent only after `hit_marker` is observed; verified live against jdb (2 stops, `a = 2, b = 3` captured).

### Mode 2: Debugger restarts the program after exit (pdb)
- **Symptom**: snapshot count inflated by phantom re-runs of the same breakpoints.
- **Prevention**: declarative `end_marker` per spec truncates the transcript at program exit before splitting; integration test asserts exactly 2 stops for 2 calls.

### Mode 3: Prompt text glued to stop lines breaks detection
- **Symptom**: `(Pdb) > file(2)fn()` — `^`-anchored markers never match; zero steps.
- **Prevention**: prompt-tolerant unanchored markers per spec; unit tests include the glued-prompt form.

### Mode 4: Hung debugger or never-hit breakpoint blocks forever
- **Prevention**: driver deadline (300s default), per-read 2s polls with liveness checks, forced kill on shutdown; "no breakpoint hit" exits rc=1 with the full transcript saved for inspection.

### Mode 5: Registry spec drift (language added with missing fields)
- **Prevention**: unit test asserts every registered language declares debugger essentials (tools, argv, hit/cont/quit); unknown predicates evaluate to never-pass instead of crashing; `zig-test` registration test proves the add-a-language path works end to end.

### Mode 6: Relative-path targets produce empty Python trees
- **Symptom**: `co_filename` relative → project filter mismatch → "(no project-level calls captured)".
- **Prevention**: bootstrap normalizes frame paths through an abspath cache; caught in live smoke and fixed before ship.
