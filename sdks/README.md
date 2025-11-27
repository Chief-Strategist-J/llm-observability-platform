# Observability SDK - Development & Publishing

## Quick Start (Local Development)

### Python
```bash
cd sdks/python
./scripts/dev-install.sh
```

### Node.js
```bash
cd sdks/nodejs
./scripts/link.sh
```

### Go
Add to microservice `go.mod`:
```go
replace github.com/yourcompany/observability-sdk-go => ../../sdks/go
```

## Publishing

### Python to PyPI
```bash
cd sdks/python
./scripts/publish.sh
```

### Node.js to npm
```bash
cd sdks/nodejs
./scripts/publish.sh
```

### Go (Git tags)
```bash
cd sdks/go
./scripts/publish.sh v1.0.0
```

## Workflow

1. **Develop Locally**: Use editable/linked installs
2. **Test**: Test in microservices with local SDK
3. **Commit**: `git commit -m "feat: new feature"`
4. **Publish**: Run publish script
5. **Update Microservices**: `pip install --upgrade` / `npm update`

## CI/CD (Optional)

Add `.github/workflows/publish.yml`:

```yaml
name: Publish SDK
on:
  push:
    tags: ['v*']
jobs:
  publish-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: cd sdks/python && ./scripts/publish.sh
```

## Structure

```
sdks/
├── python/          # Python SDK
├── nodejs/          # Node.js SDK
└── go/              # Go SDK
```

Each has:
- `scripts/build.sh`
- `scripts/publish.sh`
- `scripts/dev-install.sh` or `link.sh`
