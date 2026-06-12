# Angular Project Example

This is a clean, workspace-configured Angular application designed to verify angular.json/tsconfig detection, component compiling, and runtime inspection tools in `pylow`.

## Project Scaffolding (How to Create From Scratch)
To bootstrap this default Angular project structure from the command line, run:
```bash
# Generate the Angular workspace and application
npx @angular/cli new angular-project --defaults --routing=false --style=css --skip-git
```

## How to Run, Debug, and Code


### How to Run
* **Native Toolchain:**
  ```bash
  npm install
  npm run start
  # Or: npx ng serve
  ```
* **Via pylow:**
  ```bash
  pylow uni run src/main.ts
  ```

### How to Debug
* **Native Toolchain:** Run Angular dev server with debugging enabled:
  ```bash
  npx ng serve --source-map
  ```
* **Via pylow (Interactive):** Launch node debugger hooked to the build workspace:
  ```bash
  pylow uni debug src/main.ts
  ```
* **Via pylow (Step Debugging):** Capture step snapshots:
  ```bash
  pylow debug-steps src/main.ts --break src/main.ts:15 --watch count --out angsteps
  ```

### How to Code
* Open [main.ts](file:///home/btpl-lap-22/live/obs/packages/python/pylow/examples/angular-project/src/main.ts) to edit the main component class (`AppComponent`) and bootstrap configs.
* Open [index.html](file:///home/btpl-lap-22/live/obs/packages/python/pylow/examples/angular-project/src/index.html) to edit global shell.
* Configure Angular settings inside [angular.json](file:///home/btpl-lap-22/live/obs/packages/python/pylow/examples/angular-project/angular.json).

---

## 35+ Critical Daily Angular Commands

### Angular CLI Development & Generation
1. `ng serve` - Run development server
2. `ng serve --port 4201` - Run development server on different port
3. `ng serve --open` - Run server and open in default browser
4. `ng build` - Build application inside `dist/` directory
5. `ng build --configuration production` - Build with optimization configurations
6. `ng test` - Run unit tests
7. `ng test --code-coverage` - Run tests and produce coverage files
8. `ng lint` - Run code linting tools
9. `ng add <collection>` - Add npm library support to project
10. `ng generate component <name>` - Generate Component file template
11. `ng generate service <name>` - Generate Injectable Service template
12. `ng generate directive <name>` - Generate Directive template
13. `ng generate pipe <name>` - Generate Pipe template
14. `ng generate guard <name>` - Generate Route Guard template
15. `ng generate module <name>` - Generate NgModule template
16. `ng generate class <name>` - Generate general TypeScript class
17. `ng generate interface <name>` - Generate custom TypeScript interface

### Workspace Configurations & Maintenance
18. `ng config` - Set or get configuration variables
19. `ng update` - Update packages and configurations
20. `ng update @angular/core @angular/cli` - Update Core and CLI packages
21. `ng version` - Output current version information
22. `ng cache clean` - Clean persistent disk cache
23. `ng cache stats` - Show cache statistics
24. `ng deploy` - Deploy application using configured provider

### Unified Dev commands (`pylow`)
25. `pylow uni doctor` - Check Node and framework compilers
26. `pylow uni detect .` - Auto-detect Angular projects specs
27. `pylow uni build angular.json` - Compile Angular app and format errors
28. `pylow uni run src/main.ts` - Start dev/server runtime services
29. `pylow uni debug src/main.ts` - Attach Node inspector session
30. `pylow uni trace . --pid <PID>` - Inspect requests and network events
31. `pylow uni all src/main.ts --trace` - Full pipeline execution

### Performance & Symbol Indexing
32. `pylow calltree src/main.ts` - Render component hierarchy trace
33. `pylow calltree angular.json --depth 4` - Inspect build steps and execution
34. `pylow debug-steps src/main.ts --break main.ts:15` - Monitor lifecycle methods
35. `pylow index-build .` - Index components, models, and decorators
36. `pylow index-search AppComponent` - Find target component path instantly
