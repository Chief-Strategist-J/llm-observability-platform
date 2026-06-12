# Rust Debugging & Breakpoint Guide

This guide details how to locate code, set breakpoints, trigger them, and inspect variables in Rust using GDB/LLDB and `pylow`.

---

## 1. How to Find Targets for Breakpoints
In Rust, compile-time metadata links source locations to binary symbol mappings:

1. **Locate the Source File:** Open the target file (e.g., `src/main.rs`).
2. **Find the Line Number:** Choose the line inside the function body (e.g., inside `main()`, line 2).

---

## 2. How to Set Breakpoints

### Method A: Using `pylow` (Recommended)
Set breakpoints directly via CLI arguments:
* **By File Line:**
  ```bash
  pylow debug-steps src/main.rs --break src/main.rs:2
  ```

### Method B: Using Native debugger (GDB / LLDB)
Inside GDB/rust-gdb:
* **Set at line number:**
  ```text
  break src/main.rs:2
  ```
* **Set at function name:**
  ```text
  break main
  ```

---

## 3. How to Trigger the Breakpoint
For CLI applications and services, compile the binary with debug symbols (`cargo build` or standard target build), launch the application under the debugger, and let execution hit the code paths:

* Run the debug steps engine:
  ```bash
  pylow debug-steps src/main.rs --break src/main.rs:2 --out ruststeps
  ```
  *(This compiles, starts execution automatically, and hits line 2 inside `main()` immediately.)*

---

## 4. How to Watch & Inspect State

### In Native Debugger (GDB):
Once paused at the breakpoint:
* **Print Local Variables:**
  ```text
  info locals
  ```
* **Print Specific Variable:**
  ```text
  print variable_name
  ```
* **Print Backtrace (Stack):**
  ```text
  backtrace
  ```
* **Resume Execution:**
  ```text
  continue
  ```

### In `pylow debug-steps`:
Add watcher arguments to log specific variables dynamically:
```bash
pylow debug-steps src/main.rs \
  --break src/main.rs:2 \
  --watch some_variable \
  --out ruststeps
```
View logs inside `ruststeps/step_00X.txt`.
