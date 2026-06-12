Workspace Root Files

project/                              ← Bazel workspace root
├── MODULE.bazel                      ← Bzlmod module definition (modern Bazel)
│                                       declares the module name and dependencies
├── WORKSPACE.bazel                   ← Legacy workspace file (kept for compatibility)
│                                       use MODULE.bazel for all new dependency declarations
├── .bazelrc                          ← Bazel flags and configuration
│                                       common, build, test, run sections
├── .bazelversion                     ← Pinned Bazel version string
│                                       ensures every engineer uses the same version
├── .bazelignore                      ← Paths Bazel should not crawl
├── BUILD.bazel                       ← Root build file — workspace-level targets only
└── tools/
    └── bazel/
        ├── python.bzl               ← shared Python rule macros
        ├── node.bzl                 ← shared Node/TS rule macros
        ├── go.bzl                   ← shared Go rule macros
        ├── rust.bzl                 ← shared Rust rule macros
        ├── java.bzl                 ← shared Java rule macros
        ├── docker.bzl               ← shared container image macros
        └── deploy.bzl               ← shared deployment macros


Full Project Structure with Bazel

project/
├── MODULE.bazel
├── WORKSPACE.bazel
├── .bazelrc
├── .bazelversion
├── BUILD.bazel
├── tools/bazel/
│
├── shared/
│   └── BUILD.bazel                  ← exposes shared types as Bazel targets
│
├── packages/
│   │
│   ├── python/
│   │   └── {package-name}/
│   │       ├── BUILD.bazel          ← py_library, py_binary, py_test targets
│   │       ├── pyproject.toml       ← kept for editor tooling only, not for builds
│   │       └── src/
│   │
│   ├── node/
│   │   └── {package-name}/
│   │       ├── BUILD.bazel          ← js_library, ts_project, nodejs_binary targets
│   │       ├── package.json         ← kept for editor tooling and type declarations
│   │       └── src/
│   │
│   ├── go/
│   │   └── {package-name}/
│   │       ├── BUILD.bazel          ← go_binary, go_library, go_test targets
│   │       │                          generated and maintained by Gazelle
│   │       ├── go.mod               ← kept for Go toolchain compatibility
│   │       └── src/
│   │
│   ├── rust/
│   │   └── {package-name}/
│   │       ├── BUILD.bazel          ← rust_binary, rust_library, rust_test targets
│   │       ├── Cargo.toml           ← kept for cargo vendor and rust-analyzer
│   │       └── src/
│   │
│   ├── java/
│   │   └── {package-name}/
│   │       ├── BUILD.bazel          ← java_binary, java_library, java_test targets
│   │       ├── pom.xml              ← kept for IDE compatibility only
│   │       └── src/
│   │
│   └── apis/
│       └── BUILD.bazel
│
├── infra/
│   └── BUILD.bazel
│
└── runbooks/
    └── BUILD.bazel                  ← targets for running Ansible, scripts, notebooks


Per-Package BUILD.bazel Structure
Every package has one BUILD.bazel file. It declares what can be built, tested, run, and published from that package. Targets are the atomic units Bazel operates on.

{package}/BUILD.bazel — standard target set
│
├── {name}_lib       ← library target — all source files, importable by other targets
├── {name}_bin       ← binary target — the runnable application
├── {name}_test      ← test target — all test files, runs with bazel test
├── {name}_image     ← container image target — builds Docker image with bazel run
├── {name}_push      ← push target — pushes image to registry with bazel run
└── {name}_deploy    ← deploy target — deploys to target environment with bazel run

