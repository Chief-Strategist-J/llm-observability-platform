# SonarQube Project Addition Guide

This guide explains how to add SonarQube analysis to new projects following the established pattern with SRP, coupling taxonomy, and DRY principles.

## Overview

Each project has its own isolated SonarQube configuration with focused, single-responsibility scripts. This approach ensures:
- Single SonarQube server for all projects (cost-effective)
- Project-specific configuration in project directory
- No modifications to central infrastructure
- Easy to add new projects by copying the pattern

## Architectural Principles

**SRP (Single Responsibility Principle):**
- Each script has one responsibility
- Thin orchestrator coordinates focused modules
- No script spans multiple concerns

**Coupling Taxonomy:**
- Scripts depend on configuration (CoN/CoT - coldest coupling)
- Avoid shared mutable state (CoV)
- Avoid timing dependencies (CoT)

**DRY (Don't Repeat Yourself):**
- Single source of truth in sonar-config.json
- Reusable utilities in utils.sh
- No duplicated logic

## Project Structure Template

```
your-project/
├── [project-specific files]
├── sonar-config.json                 # Single source of truth
├── Makefile                          # Project-specific targets
└── scripts/sonar/
    ├── orchestrator.sh               # Thin coordinator
    ├── server_manager.sh             # Server lifecycle (SRP)
    ├── coverage_generator.sh         # Coverage generation (SRP)
    ├── sonar_scanner.sh              # SonarQube scanning (SRP)
    ├── config_loader.sh              # Configuration loading (SRP)
    └── utils.sh                      # Reusable utilities (DRY)
```

## Step-by-Step Guide

### 1. Create sonar-config.json

Copy the template and adapt for your project:

```json
{
  "projectKey": "your-project-key",
  "projectName": "Your Project Name",
  "projectVersion": "1.0.0",
  "language": "python|go|rust|java",
  "sourceDirs": ["src", "lib"],
  "testDirs": ["tests", "test"],
  "exclusions": [
    "target/**",
    "node_modules/**",
    "dist/**",
    "build/**"
  ],
  "sonarHostUrl": "http://localhost:9000",
  "sonarToken": "",
  "coverage": {
    "tool": "coverage-tool-name",
    "outputFormat": "xml|json",
    "outputDir": "coverage"
  }
}
```

### 2. Copy Scripts Directory

Copy the entire `scripts/sonar/` directory from DTAE:

```bash
cp -r infrastructure/observability/distributedTraceAnalysisEngine/scripts/sonar your-project/scripts/
```

### 3. Adapt coverage_generator.sh

Modify `coverage_generator.sh` for your language:

**Python:**
```bash
generate_coverage() {
  cd "$PROJECT_ROOT"
  ensure_dir "$COVERAGE_OUTPUT_DIR"
  pytest --cov=. --cov-report=xml --cov-report=html
}
```

**Go:**
```bash
generate_coverage() {
  cd "$PROJECT_ROOT"
  ensure_dir "$COVERAGE_OUTPUT_DIR"
  go test -coverprofile=coverage.out ./...
  go tool cover -xml=coverage.out -o "$COVERAGE_OUTPUT_DIR/coverage.xml"
}
```

**Rust:** (already implemented in DTAE)
```bash
generate_coverage() {
  cargo tarpaulin --out Xml --output-dir "$coverage_dir"
}
```

### 4. Create Project-Specific Makefile

Create a Makefile in your project root:

```makefile
.PHONY: sonar-analyze sonar-setup sonar-coverage sonar-start sonar-stop

SCRIPTS_DIR := scripts/sonar

sonar-analyze:
	@bash $(SCRIPTS_DIR)/orchestrator.sh

sonar-setup:
	@# Install language-specific coverage tool
	@echo "Dependencies installed"

sonar-coverage:
	@bash $(SCRIPTS_DIR)/coverage_generator.sh

sonar-start:
	@bash $(SCRIPTS_DIR)/server_manager.sh start_server

sonar-stop:
	@bash $(SCRIPTS_DIR)/server_manager.sh stop_server
```

### 5. Make Scripts Executable

```bash
chmod +x your-project/scripts/sonar/*.sh
```

### 6. Set SonarQube Token

Edit `sonar-config.json` and add your SonarQube token:

```json
{
  "sonarToken": "your-sonarqube-token-here"
}
```

Or set as environment variable:

```bash
export SONAR_TOKEN="your-token"
```

## Usage

### Run Full Analysis

```bash
cd your-project
make sonar-analyze
```

### Individual Steps

```bash
make sonar-start       # Start SonarQube server
make sonar-coverage    # Generate coverage
make sonar-scan         # Run SonarQube scan
make sonar-stop        # Stop SonarQube server
```

## Language-Specific Coverage Tools

| Language | Coverage Tool | Installation |
|----------|--------------|-------------|
| Python   | pytest-cov   | `pip install pytest pytest-cov` |
| Go       | go test      | Built-in |
| Rust     | cargo-tarpaulin | `cargo install cargo-tarpaulin` |
| Java     | JaCoCo       | Maven/Gradle plugin |

## Troubleshooting

### SonarQube Server Not Starting

Check Docker Compose file path in `server_manager.sh`:
```bash
# Adjust this path to your infrastructure location
DOCKER_COMPOSE_FILE="$INFRASTRUCTURE_DIR/deployment/docker/docker-compose.optimized.yml"
```

### Coverage Tool Not Found

Install the appropriate coverage tool for your language (see table above).

### sonar-scanner Not Found

Install sonar-scanner:
```bash
# Linux/Mac
brew install sonar-scanner

# Or download from: https://docs.sonarqube.org/latest/analysis/scan/sonarscanner/
```

## CI/CD Integration

To add CI/CD later, simply call the same script from your GitHub Actions:

```yaml
- name: Run SonarQube Analysis
  run: |
    cd your-project
    make sonar-analyze
  env:
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

## Checklist

- [ ] Created sonar-config.json with project-specific settings
- [ ] Copied scripts/sonar/ directory
- [ ] Adapted coverage_generator.sh for language
- [ ] Created project-specific Makefile
- [ ] Made scripts executable
- [ ] Set SonarQube token
- [ ] Tested `make sonar-analyze` locally
- [ ] Verified results in SonarQube dashboard
