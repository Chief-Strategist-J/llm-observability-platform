# React TypeScript Example Project

This is a Vite-powered React and TypeScript project designed to test front-end compiler outputs, tsconfig/package configs, and runtime performance analyzer integrations.

## Project Scaffolding (How to Create From Scratch)
To bootstrap this default React TypeScript (Vite) project structure from the command line, run:
```bash
# Generate the Vite + React TS project structure
npx create-vite@latest react-typescript --template react-ts
```

## How to Run, Debug, and Code


### How to Run
* **Native Toolchain:**
  ```bash
  npm install
  npm run dev
  ```
* **Via pylow:**
  ```bash
  pylow uni run src/main.tsx
  ```

### How to Debug
* **Native Toolchain:** Open browser devtools (`F12`), or inspect Node.js processes via inspect flags:
  ```bash
  node --inspect-brk node_modules/.bin/vite
  ```
* **Via pylow (Interactive):** Launch node inspect debugging:
  ```bash
  pylow uni debug src/main.tsx
  ```
* **Via pylow (Step Debugging):** Capture step snapshots:
  ```bash
  pylow debug-steps src/main.tsx --break App.tsx:6 --watch count --out reactsteps
  ```

### How to Code
* Main interface logic is in [App.tsx](file:///home/btpl-lap-22/live/obs/packages/python/pylow/examples/react-typescript/src/App.tsx).
* Bootstrapping entrypoint is in [main.tsx](file:///home/btpl-lap-22/live/obs/packages/python/pylow/examples/react-typescript/src/main.tsx).
* App configuration is in [vite.config.ts](file:///home/btpl-lap-22/live/obs/packages/python/pylow/examples/react-typescript/vite.config.ts).

## Step-by-Step Tracing & Debugging Guide

### 1. Launch-Mode Calltree Tracing
Run Node and sample the React component CPU profiles automatically:
```bash
pylow calltree src/main.tsx
```

### 2. Live Process Sampling (via PID)
If you have a running Node application (e.g. running Vite development server):
```bash
# 1. Get process PID
pgrep node

# 2. Run calltree trace on the PID for 30 seconds
pylow calltree src/main.tsx --pid <PID> --duration 30
```

### 3. Step Debugging with Watchers
Pace the V8 debugger to snapshot state variables on line hits:
```bash
pylow debug-steps src/main.tsx --break src/App.tsx:6 --watch count --out reactsteps
```
Read the step snapshots:
```bash
cat reactsteps/step_001.txt
```

---


## 35+ Critical Daily React / TypeScript Commands

### NPM & Package Management
1. `npm install` - Install project dependencies
2. `npm install <pkg>` - Install package and save to dependencies
3. `npm install -D <pkg>` - Install package to devDependencies
4. `npm uninstall <pkg>` - Remove a package
5. `npm update` - Update packages in package.json
6. `npm audit` - Check for security vulnerabilities in dependencies
7. `npm audit fix` - Automatically resolve dependency issues
8. `npm outdated` - Check for outdated packages
9. `npm ci` - Clean install dependencies (deterministic, uses lockfile)
10. `npm run build` - Compile the React app for production
11. `npm run dev` - Run Vite development server
12. `npm run preview` - Serve production build locally

### TypeScript & Linting
13. `npx tsc` - Run TypeScript compiler check
14. `npx tsc --noEmit` - Type-check code without generating files
15. `npx tsc --watch` - Run compiler in watch mode
16. `npx eslint .` - Lint JavaScript/TypeScript files
17. `npx eslint . --fix` - Automatically fix lint warnings
18. `npx prettier --write .` - Format code styling with Prettier
19. `npx tsc-files <file>` - Type-check specific files on git-stage

### Unified Dev commands (`pylow`)
20. `pylow uni doctor` - View toolchain diagnoses (node, tsc, tsc-node)
21. `pylow uni detect .` - Auto-detect package.json & tsconfig specs
22. `pylow uni build package.json` - Compile Vite assets and catch errors
23. `pylow uni run src/main.tsx` - Start dev/runtime services
24. `pylow uni debug src/main.tsx` - Attach Node inspector session
25. `pylow uni trace . --pid <PID>` - Inspect network requests / process events
26. `pylow uni all src/main.tsx --trace` - Full build-run-trace flow

### Performance & Symbol Search
27. `pylow calltree src/main.tsx` - Sample and render component call-tree
28. `pylow calltree package.json --depth 3` - Inspect app dependencies execution
29. `pylow debug-steps src/App.tsx --break App.tsx:6` - Track hook and state changes
30. `pylow index-build .` - Index components, types, interfaces, hooks
31. `pylow index-search App` - Instantly locate React components in filesystem
32. `npm run lint && npm run build` - Pre-flight staging verification
33. `npx vite optimize` - Force pre-bundling of dependencies
34. `npx depcheck` - Find unused dependencies in package.json
35. `npm list --depth=0` - View high-level installed packages
