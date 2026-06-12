# Angular Debugging & Breakpoint Guide

This guide details how to locate component code, set breakpoints, trigger them, and inspect component states using Node inspector and `pylow`.

---

## 1. How to Find Targets for Breakpoints
In Angular applications, components are defined inside source files (e.g., `src/main.ts` or individual component TS files):

1. **Locate the File:** Open the component file (e.g., `src/main.ts`).
2. **Find the Line Number:** Choose the line inside the component class where functions or event handlers are defined (e.g., inside `increment()`, line 15).

---

## 2. How to Set Breakpoints

### Method A: Using `pylow` (Recommended)
Set breakpoints directly on TypeScript source files:
* **By File Line:**
  ```bash
  pylow debug-steps src/main.ts --break src/main.ts:15
  ```

### Method B: Using Native Node CLI Debugger
Start Angular CLI with debugger hooks:
```bash
node --inspect-brk node_modules/.bin/ng serve
```
Inside the interactive debugger shell:
* **Set at line number:**
  ```text
  sb("src/main.ts", 15)
  ```

---

## 3. How to Trigger the Breakpoint
For Angular apps, breakpoints are triggered by user actions on the DOM:
* Open the browser and navigate to the application URL (e.g., `http://localhost:4200`).
* Click the component button **"count is 0"** on the page. This executes the `increment()` method, triggering the breakpoint on line 15.

---

## 4. How to Watch & Inspect State

### In Node Inspector:
* **Evaluate Variable:**
  ```text
  exec("this.count")
  ```
* **Add Watch Expression:**
  ```text
  watch("this.count")
  ```
* **Resume Execution:**
  ```text
  cont
  ```

### In `pylow debug-steps`:
Automatically snapshot properties via `--watch`:
```bash
pylow debug-steps src/main.ts \
  --break src/main.ts:15 \
  --watch "this.count" \
  --out angsteps
```
Snapshots are recorded inside `angsteps/step_00X.txt`.
