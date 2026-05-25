.bazelrc — Configuration File Structure

.bazelrc
│
├── common section                   ← flags that apply to every Bazel command
│   ├── --enable_bzlmod             ← use MODULE.bazel (modern dependency system)
│   └── --experimental_convenience_symlinks=normal
│
├── build section                    ← flags that apply to bazel build
│   ├── --remote_cache=...          ← remote cache endpoint
│   ├── --google_credentials=...    ← auth for remote cache
│   ├── --disk_cache=~/.bazel-cache ← local disk cache path
│   └── --verbose_failures          ← show full error on failure
│
├── test section                     ← flags that apply to bazel test
│   ├── --test_output=errors        ← only print output on failure
│   └── --test_timeout=120          ← max seconds per test
│
├── run section                      ← flags that apply to bazel run
│
├── ci config (--config=ci)          ← activated with --config=ci in CI pipelines
│   ├── --remote_upload_local_results ← upload results to remote cache
│   └── --bes_backend=...           ← build event service endpoint
│
└── local config (--config=local)    ← developer local overrides
    └── --disk_cache=~/.bazel-cache


MODULE.bazel — Dependency Declaration

MODULE.bazel — what goes here
│
├── module()                         ← declares this workspace as a Bazel module
│   ├── name
│   └── version
│
├── bazel_dep()                      ← one call per external ruleset or library
│   ├── rules_python                ← Python rules
│   ├── rules_js                    ← Node/TS rules
│   ├── rules_go                    ← Go rules
│   ├── rules_rust                  ← Rust rules
│   ├── rules_java (built-in)       ← Java rules
│   ├── rules_proto                 ← Proto/gRPC rules
│   ├── rules_oci                   ← Container image rules
│   ├── gazelle                     ← Go BUILD file generator
│   └── buildifier_prebuilt         ← BUILD file formatter
│
├── Python toolchain registration    ← declared via rules_python extension
│   └── python.toolchain(python_version = 3.12)
│
├── Node toolchain registration      ← declared via rules_js extension
│   └── node.toolchain(node_version = 20)
│
├── Go toolchain registration        ← declared via rules_go extension
│   └── go_sdk.download(version = 1.23)
│
├── Rust toolchain registration      ← declared via rules_rust extension
│   └── rust.toolchain(versions = [1.80.0])
│
└── npm / pip / cargo dependencies   ← declared per-language via their extensions


Target Label Conventions
Every Bazel target has a label. Labels are the addresses used in all Bazel commands. Following a consistent convention is required across all packages.

Target Purpose
Label Convention
Example
Library (all source)
//packages/{lang}/{name}:{name}_lib
//packages/python/auth:auth_lib
Binary (runnable)
//packages/{lang}/{name}:{name}
//packages/go/payments:payments
Tests
//packages/{lang}/{name}:{name}_test
//packages/rust/engine:engine_test
Container image
//packages/{lang}/{name}:{name}_image
//packages/java/core:core_image
Push to registry
//packages/{lang}/{name}:{name}_push
//packages/node/gateway:gateway_push
Deploy
//packages/{lang}/{name}:{name}_deploy
//packages/python/auth:auth_deploy
All targets in a package
//packages/{lang}/{name}/...
//packages/python/auth/...
All targets everywhere
//...
//...


Gazelle — Auto-Generating Go BUILD Files
Gazelle reads Go source files and generates or updates BUILD.bazel files automatically. It removes the need to maintain Go BUILD files by hand.

Gazelle setup in project
│
├── MODULE.bazel declares gazelle as a dependency
│
├── Root BUILD.bazel declares the gazelle target
│   └── gazelle target points to all Go packages
│
├── .bazelrc adds gazelle run shortcut
│
└── Commands
    ├── bazel run //:gazelle          ← generate or update all Go BUILD files
    └── bazel run //:gazelle-update-repos  ← sync go.mod deps into MODULE.bazel


Remote Cache Configuration
Remote caching means if a target was built by any engineer or CI run with the same inputs, the output is fetched from cache instead of rebuilt. This is the single biggest productivity gain Bazel provides.

Cache types and when to use each
│
├── Disk cache (--disk_cache)
│   ├── Local only — per-developer machine
│   ├── No setup required
│   └── Best for: local development speed
│
├── Remote HTTP cache (--remote_cache)
│   ├── Shared across all developers and CI
│   ├── Backends: Google Cloud Storage, S3, Nginx, Bazel Remote
│   └── Best for: team-wide sharing, CI acceleration
│
└── Remote Execution (--remote_executor)
    ├── Executes builds on remote workers — not just caches
    ├── Enables massive parallelism beyond a single machine
    ├── Backends: BuildBuddy, EngFlow, Google RBE
    └── Best for: large monorepos, slow build steps


CI/CD Integration with Bazel

.github/workflows/ci.yaml — with Bazel
│
├── Install Bazelisk                  ← Bazelisk reads .bazelversion and downloads correct Bazel
│
├── Restore disk cache               ← cache ~/.cache/bazel between runs
│
├── stage 1: lint and format
│   └── bazel run //:buildifier -- --mode=check -r .
│
├── stage 2: build all
│   └── bazel build --config=ci //...
│
├── stage 3: test all
│   └── bazel test --config=ci //...
│
├── stage 4: build container images
│   └── bazel run --config=ci //packages/{lang}/{name}:image
│
├── stage 5: push images (on merge to main only)
│   └── bazel run --config=ci //packages/{lang}/{name}:push
│
└── stage 6: deploy (on tag only)
    └── bazel run --config=ci //packages/{lang}/{name}:deploy -- --env=staging


Per-Language Dependency Management with Bazel

Language
Dependencies Declared In
How Bazel Consumes Them
Lock File
Python
requirements.txt or pyproject.toml
pip.parse() in MODULE.bazel extension generates a Bazel repo
requirements_lock.txt
Node/TS
package.json
npm_translate_lock() in MODULE.bazel reads package-lock.json
package-lock.json
Go
go.mod
gazelle-update-repos syncs go.mod into MODULE.bazel
go.sum
Rust
Cargo.toml
crates_repository() in MODULE.bazel reads Cargo.lock
Cargo.lock
Java
pom.xml or build.gradle
rules_jvm_external maven_install reads artifact list
maven_install.json
Proto
imported directly in .proto files
proto_library and grpc_library rules in BUILD.bazel
N/A

