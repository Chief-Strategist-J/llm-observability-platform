# Java/Spring Boot Debugging & Breakpoint Guide

This guide details how to locate target code, set breakpoints, trigger them, and inspect variables using the native Java Debugger (`jdb`) and `pylow`.

---

## 1. How to Find Targets for Breakpoints
To set a breakpoint in Java, you need to identify the **fully qualified class name** and the **line number** or **method signature**:

1. **Locate the Class:** Open the file (e.g., `AlgorithmController.java`). Note the `package` name at the top (`package com.example.controller;`) and the class name (`AlgorithmController`).
2. **Construct the Fully Qualified Name:** Combine them: `com.example.controller.AlgorithmController`.
3. **Find the Line Number:** Open the source file and choose a line (e.g., inside the `partition` method, line 57).

---

## 2. How to Set Breakpoints

### Method A: Using `pylow` (Recommended)
You can specify breakpoints directly as CLI arguments. `pylow` will compile, run, and pre-configure the breakpoints for you:
* **By Class & Line:**
  ```bash
  pylow debug-steps src/main/java/com/example/DemoApplication.java --break AlgorithmController:57
  ```
  *(Or use the fully qualified class name for precision: `com.example.controller.AlgorithmController:57`)*
* **By Method Name:**
  ```bash
  pylow debug-steps src/main/java/com/example/DemoApplication.java --break com.example.controller.AlgorithmController.partition
  ```

### Method B: Using Native `jdb`
If running native `jdb` interactively:
* **Set at line number:**
  ```text
  stop at com.example.controller.AlgorithmController:57
  ```
* **Set inside a method:**
  ```text
  stop in com.example.controller.AlgorithmController.partition
  ```

---

## 3. How to Trigger the Breakpoint
Because this is a Spring Boot web application, breakpoints inside controllers are bound to HTTP routes. 
To hit the breakpoint, trigger the endpoint from your browser or another terminal window:

```bash
# Triggers the QuickSort endpoint, reaching AlgorithmController:57
curl "http://localhost:8080/sort?items=5,2,9,1"
```

---

## 4. How to Watch & Inspect State

### In Native `jdb`:
When the breakpoint is hit, the execution pauses. You can run:
* **Print Local Variables:**
  ```text
  locals
  ```
* **Print Specific Variable or Object:**
  ```text
  print pivot
  print arr[0]
  ```
* **Show Stack Trace:**
  ```text
  where
  ```
* **Resume Execution:**
  ```text
  cont
  ```

### In `pylow debug-steps`:
Use the `--watch` parameter to automatically capture variables at every step/hit without manual typing:
```bash
pylow debug-steps src/main/java/com/example/DemoApplication.java \
  --break AlgorithmController:57 \
  --watch pivot \
  --watch "arr[low]" \
  --out qsteps
```
All snapshots will be written directly to `qsteps/step_00X.txt` for your review.
