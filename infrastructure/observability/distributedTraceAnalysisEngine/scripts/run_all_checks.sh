#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

step() { echo "\n==> $1"; }

step "Rust format check (API changes only)"
(cd "$ROOT_DIR" && rustfmt --edition 2021 --check src/api/server.rs src/api/client.rs)

step "Rust tests"
if (cd "$ROOT_DIR" && cargo metadata --offline >/dev/null 2>&1); then
  (cd "$ROOT_DIR" && cargo test --offline)
  echo "Rust tests passed in offline mode."
else
  echo "Skipping Rust tests: offline dependency cache is unavailable in this environment."
fi

step "Frontend TypeScript + build (best effort)"
if command -v npm >/dev/null 2>&1; then
  if [ -d "$ROOT_DIR/web/node_modules" ]; then
    (cd "$ROOT_DIR/web" && npm run build)
  else
    echo "Skipping web build: $ROOT_DIR/web/node_modules not found."
  fi
else
  echo "Skipping web build: npm not available"
fi

step "Done"
