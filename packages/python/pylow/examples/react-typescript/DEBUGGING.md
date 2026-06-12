# React TypeScript Debugging & Breakpoint Guide

This guide details how to locate code, set breakpoints, trigger them, and inspect component states using Node inspector and `pylow`.

---

## 1. How to Find Targets for Breakpoints
In React TypeScript (built via Vite/Node), targets are mapped to compile-time source paths:

1. **Locate the Component File:** Find the TS/TSX file (e.g., `src/App.tsx`).
2. **Find the Line Number:** Choose the line inside the component body where state modifications occur (e.g., inside the increment counter click handler, line 6).

---

## 2. How to Set Breakpoints

### Method A: Using `pylow` (Recommended)
Pre-configure breakpoints directly with the `pylow` debugger engine:
* **By File Line:**
  ```bash
  pylow debug-steps src/main.tsx --break src/App.tsx:6
  ```

### Method B: Using Native Node CLI Debugger
Start the project in inspect/debug mode:
```bash
node --inspect-brk node_modules/.bin/vite
```
In the inspector shell:
* **Set at line number:**
  ```text
  sb("src/App.tsx", 6)
  ```

---

## 3. How to Trigger the Breakpoint
For React client-side code, actions are usually triggered via user interaction or mock state transitions:
* Open the browser view at the development server URL (e.g., `http://localhost:5173`).
* Click the **"count is 0"** button on the UI page to trigger the click handler containing the breakpoint.

---

## 4. How to Watch & Inspect State

### In Node Inspector:
Once paused:
* **Evaluate expression/variable value:**
  ```text
  exec("count")
  ```
* **Add a Watch Expression:**
  ```text
  watch("count")
  ```
* **Step Over:**
  ```text
  next
  ```

### In `pylow debug-steps`:
Provide the `--watch` parameter to automatically log states to disk:
```bash
pylow debug-steps src/main.tsx \
  --break src/App.tsx:6 \
  --watch count \
  --out reactsteps
```
View the logs inside `reactsteps/step_00X.txt`.
