# Observability Module Git Hooks

These Git hooks are specifically designed to enforce quality and consistency within the **infrastructure/observability** module.

## Hooks Overview

- **pre-commit**: Runs `flake8` linting on the `infrastructure/observability` directory.
- **commit-msg**: Enforces the `[OBSERVABILITY]` tag in the commit message if files in this module are changed.
- **pre-push**: Blocks pushes if `TODO` or `FIXME` exist in the observability module.
- **prepare-commit-msg**: Automatically prefixes commit messages with `[OBSERVABILITY]` for changes within this module.

## Scoping Logic

Each hook includes a path-based check:
```bash
git diff --cached --name-only | grep -q "^infrastructure/observability/"
```
This ensures that the hooks **only** execute their logic if files within the `infrastructure/observability/` directory are being modified. Changes to other parts of the repository will not trigger these module-specific checks.

## Installation

Run the installation script from the module root:
```bash
./setup/hooks/install_hooks.sh
```

## Adding More Modules

If you want to add hooks for other modules in the future, you can either:
1. Append more path checks to these scripts.
2. Use a centralized hook orchestrator (like a root-level `pre-commit` tool).
