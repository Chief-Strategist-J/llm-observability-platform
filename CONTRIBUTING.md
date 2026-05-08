# Contributing to LLM Observability Platform

Thank you for your interest in contributing to **LLM Observability Platform**.

This project is a Python-based observability platform for LLM applications, with a Streamlit interface, Docker-based orchestration, and observability components such as logging, metrics, and tracing. Contributions that improve reliability, maintainability, documentation, and developer experience are welcome.

## Table of Contents

* [Ways to Contribute](#ways-to-contribute)
* [Getting Started](#getting-started)
* [Development Environment](#development-environment)
* [Branching](#branching)
* [Commit Messages](#commit-messages)
* [Code Style](#code-style)
* [Testing](#testing)
* [Pull Requests](#pull-requests)
* [Issue Reports](#issue-reports)
* [Security](#security)
* [License](#license)

## Ways to Contribute

You can contribute by:

* Fixing bugs
* Improving observability features
* Enhancing Streamlit UI components
* Extending infrastructure or orchestration workflows
* Improving documentation
* Adding tests
* Refining deployment and configuration examples

## Getting Started

1. Fork the repository.
2. Clone your fork locally.
3. Create a feature branch.
4. Make your changes.
5. Run the relevant checks.
6. Open a pull request.

```bash
git clone https://github.com/<your-username>/llm-observability-platform.git
cd llm-observability-platform
git checkout -b feature/your-change
```

## Development Environment

The repository README indicates the project uses Python 3.10+, Docker, Docker Compose, MongoDB, Streamlit, Temporal, and observability services such as Loki, Prometheus, Grafana, and OpenTelemetry.

A typical local setup looks like this:

```bash
cp .env.template .env
python infrastructure/orchestrator/trigger/setup/start_mongodb.py
python infrastructure/orchestrator/workers/service_setup_worker.py
cd service/llm_chat_app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py --server.port 8501
```

If your change touches infrastructure, use the relevant Docker Compose or orchestration commands in the repository documentation.

## Branching

Use clear branch names that describe the change:

```text
feature/add-tracing-correlation
fix/mongodb-startup-error
docs/improve-setup-guide
refactor/streamlit-state-management
```

Keep branches focused on a single concern.

## Commit Messages

Use conventional, readable commit messages.

Format:

```text
type(scope): short description
```

Examples:

```text
feat(tracing): add request correlation IDs
fix(mongodb): handle missing network creation
docs(readme): clarify local setup steps
refactor(ui): simplify chat state handling
```

Common types:

* `feat`
* `fix`
* `docs`
* `refactor`
* `test`
* `chore`
* `perf`

## Code Style

Follow the style already used in the repository.

General expectations:

* Write clear, maintainable code
* Prefer small, focused functions
* Keep changes consistent with the existing architecture
* Avoid unrelated refactors in the same pull request
* Add comments only where the code is not self-explanatory

If formatting or linting tools are configured in the repository, run them before submitting your changes.

## Testing

Before opening a pull request:

* Run the relevant application and infrastructure checks
* Verify the Streamlit app starts correctly if your changes affect the UI
* Verify orchestration or deployment scripts if your changes affect infrastructure
* Add or update tests when behavior changes
* Confirm existing behavior still works

Example commands:

```bash
python -m compileall .
```

```bash
pytest
```

Use the test command that matches the component you changed.

## Pull Requests

A good pull request should include:

* A short summary of the change
* Why the change is needed
* What was tested
* Screenshots or recordings for UI changes, when relevant
* Any environment or setup changes reviewers need to know

Before submitting:

* Rebase or merge the latest `main`
* Keep the pull request narrowly scoped
* Update documentation if needed
* Remove debug code and temporary logging

## Issue Reports

When opening an issue, include:

* What you expected to happen
* What actually happened
* Steps to reproduce
* Relevant logs or screenshots
* Your environment details

A reproducible example is especially helpful for infrastructure and observability issues.

## Security

Do not open public issues for sensitive security findings.

For security-related concerns, use the repository’s private disclosure process or contact the maintainers directly.

Do not commit secrets, API keys, tokens, passwords, or environment files.

## License

By contributing to this project, you agree that your contributions will be licensed under the repository’s license.
