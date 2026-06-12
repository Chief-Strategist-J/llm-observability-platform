# Go Debugging & Breakpoint Guide

This guide details how to locate target code, set breakpoints, trigger them, and inspect variables in Go using Delve (`dlv`) and `pylow`.

---

## 1. How to Find Targets for Breakpoints
In Go, you can set breakpoints by referencing either a **file line** or a **fully qualified function path**:

1. **Locate the File and Line:** Open your file (e.g., `main.go`) and choose a line (e.g., inside the `helloHandler`, line 8).
2. **Find the Function Name:** Identify the function signature (e.g., `func helloHandler`). In Go, it is fully qualified as `<package>.<function_name>` (e.g., `main.helloHandler`).

---

## 2. How to Set Breakpoints

### Method A: Using `pylow` (Recommended)
Pre-configure breakpoints using `pylow` command line parameters:
* **By File Line:**
  ```bash
  pylow debug-steps main.go --break main.go:8
  ```
* **By Function Name:**
  ```bash
  pylow debug-steps main.go --break main.helloHandler
  ```

### Method B: Using Native Delve (`dlv`)
Inside an interactive Delve shell:
* **Set at line number:**
  ```text
  break main.go:8
  ```
* **Set at function name:**
  ```text
  break main.helloHandler
  ```

---

## 3. How to Trigger the Breakpoint
For a web service, trigger the endpoint using `curl` or opening it in your browser:

```bash
# Reaches main.go:8 (helloHandler)
curl "http://localhost:8080/"
```

---

## 4. How to Watch & Inspect State

### In Native Delve (`dlv`):
When the breakpoint is hit, the debugger pauses execution:
* **Print Local Variables:**
  ```text
  locals
  ```
* **Print Function Arguments:**
  ```text
  args
  ```
* **Print Specific Variable:**
  ```text
  print w
  ```
* **Resume Execution:**
  ```text
  continue
  ```

### In `pylow debug-steps`:
Use `--watch` to capture targeted variables on every step:
```bash
pylow debug-steps main.go \
  --break main.go:8 \
  --watch r.Method \
  --watch r.RemoteAddr \
  --out gosteps
```
Captured states will be recorded inside `gosteps/step_00X.txt`.
