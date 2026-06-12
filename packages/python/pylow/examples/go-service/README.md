# Go Service Example Project

This is a standalone Go service package designed for testing Go compiler diagnostics, symbol indexers, and tracing hooks inside `pylow`.

## Project Scaffolding (How to Create From Scratch)
To bootstrap this default Go module structure from the command line, run:
```bash
# Create directory and initialize module
mkdir go-service
cd go-service
go mod init go-service
```
Then create a simple `main.go` file with your handler logic.

## How to Run, Debug, and Code


### How to Run
* **Native Toolchain:**
  ```bash
  go run main.go
  ```
* **Via pylow:**
  ```bash
  pylow uni run main.go
  ```

### How to Debug
* **Native Toolchain:** Run delve debugger interactively:
  ```bash
  dlv debug main.go
  ```
* **Via pylow (Interactive):** Launch native debugger with pre-configured backend:
  ```bash
  pylow uni debug main.go
  ```
* **Via pylow (Step Debugging):** Capture step-by-step variable snapshots:
  ```bash
  pylow debug-steps main.go --break main.go:12 --watch r --out gosteps
  ```

### How to Code
* Open [main.go](file:///home/btpl-lap-22/live/obs/packages/python/pylow/examples/go-service/main.go) to change routing or handlers.
* Check dependencies in [go.mod](file:///home/btpl-lap-22/live/obs/packages/python/pylow/examples/go-service/go.mod).
* Format code with `go fmt ./...`.

---

## 35+ Critical Daily Go Commands

### Go Compiler & Modules
1. `go run main.go` - Compile and run main file
2. `go build` - Build the application binary
3. `go build -o app main.go` - Compile to a specific output name
4. `go test ./...` - Run all package unit tests
5. `go test -v ./...` - Run tests with verbose logs
6. `go test -bench=. ./...` - Run benchmark tests
7. `go clean` - Remove object files and cached archives
8. `go mod init <module_name>` - Initialize a new module
9. `go mod tidy` - Add missing and remove unused modules
10. `go mod verify` - Verify dependencies have expected content
11. `go mod vendor` - Create local copy of dependencies in vendor directory
12. `go get <pkg>` - Add a dependency to the current module
13. `go install <pkg>` - Compile and install packages/dependencies

### Code Quality & Analysis
14. `go fmt ./...` - Format source files
15. `go vet ./...` - Report likely mistakes in packages
16. `go doc <entity>` - Show documentation for a package or symbol
17. `go list -m all` - List main module and all dependencies
18. `go tool cover -html=coverage.out` - Visualize test coverage in browser
19. `golangci-lint run` - Run golangci linter

### Debugging & Profiling (Delve / pprof)
20. `dlv debug` - Compile and debug main package
21. `dlv test` - Compile and debug tests
22. `dlv attach <PID>` - Attach Delve to a running process
23. `go tool pprof -http=:8081 cpu.pprof` - Analyze CPU profile via Web UI
24. `go tool trace trace.out` - Start execution trace visualizer
25. `dlv exec ./binary` - Debug an already compiled binary

### Unified Dev commands (`pylow`)
26. `pylow uni doctor` - View compiler checkups (Go/Dlv/perf)
27. `pylow uni detect .` - Auto-detect Go configurations
28. `pylow uni build main.go` - Compile Go code and output parsed errors
29. `pylow uni run main.go` - Run project via Go runtime
30. `pylow uni debug main.go` - Run interactive debug session via Delve
31. `pylow uni trace . --pid <PID>` - Attach eBPF/uftrace to Go binary
32. `pylow uni all main.go --trace` - Run build/run/trace pipeline

### Calltree & Indexing
33. `pylow calltree main.go` - Dump exact Delve call-trace hierarchy
34. `pylow debug-steps main.go --break main.go:8` - Capture step local states
35. `pylow index-build .` - Index all Go structs, functions, and interfaces
36. `pylow index-search helloHandler` - Locate function symbols in codebase
