# Runbook 5: Configuration Management and JSON Structure

## Overview
This runbook covers SonarQube configuration management, JSON structure explanations, and how to create and customize the `sonar-config.json` file for different project types and requirements.

## Configuration Architecture

### Configuration Hierarchy
```
sonar-config.json (Single Source of Truth)
        ↓
scripts/sonar/config_loader.sh (Loads and validates)
        ↓
Environment Variables (Exported)
        ↓
sonar-project.properties (Generated for scanner)
        ↓
SonarScanner CLI (Uses properties)
```

### Configuration Flow
1. **JSON Config**: Human-readable configuration file
2. **Loader Script**: Validates and exports as environment variables
3. **Properties File**: Generated SonarQube scanner format
4. **Scanner Execution**: Uses generated properties

## sonar-config.json Structure

### Complete Configuration Schema
```json
{
  "projectKey": "distributed-trace-analysis-engine",
  "projectName": "Distributed Trace Analysis Engine",
  "projectVersion": "0.1.0",
  "language": "rust",
  "sourceDirs": ["src"],
  "testDirs": ["tests"],
  "exclusions": [
    "target/**",
    "web/**",
    "node_modules/**",
    "*.json",
    "*.yaml",
    "*.yml"
  ],
  "sonarHostUrl": "http://sonarqube:9000",
  "sonarToken": "squ_44characterlongtoken...",
  "coverage": {
    "tool": "cargo-tarpaulin",
    "outputFormat": "xml",
    "outputDir": "coverage",
    "additionalArgs": ["--skip-clean"]
  },
  "qualityGate": {
    "name": "Sonar way"
  },
  "customProperties": {
    "sonar.java.binaries": "target/classes",
    "sonar.python.coverage.reportPaths": "coverage/coverage.xml"
  }
}
```

### Field Explanations

#### Core Project Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `projectKey` | string | ✅ | Unique identifier (no spaces, special chars) |
| `projectName` | string | ✅ | Human-readable display name |
| `projectVersion` | string | ✅ | Current project version |
| `language` | string | ✅ | Programming language (rust, py, js, java, etc.) |

#### Source Configuration Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sourceDirs` | array | ✅ | Source code directories |
| `testDirs` | array | ❌ | Test directories (optional) |
| `exclusions` | array | ❌ | Files/directories to exclude |

#### Connection Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sonarHostUrl` | string | ✅ | SonarQube server URL |
| `sonarToken` | string | ✅ | 44-character authentication token |

#### Coverage Configuration
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `coverage.tool` | string | ✅ | Coverage tool name |
| `coverage.outputFormat` | string | ✅ | Output format (xml, lcov, cobertura) |
| `coverage.outputDir` | string | ✅ | Output directory path |
| `coverage.additionalArgs` | array | ❌ | Additional tool arguments |

## Language-Specific Configurations

### Rust Projects
```json
{
  "projectKey": "rust-project",
  "projectName": "Rust Project",
  "projectVersion": "1.0.0",
  "language": "rust",
  "sourceDirs": ["src"],
  "testDirs": ["tests"],
  "exclusions": [
    "target/**",
    "Cargo.lock",
    "**/*.rs.bk"
  ],
  "sonarHostUrl": "http://sonarqube:9000",
  "sonarToken": "squ_44characterlongtoken...",
  "coverage": {
    "tool": "cargo-tarpaulin",
    "outputFormat": "xml",
    "outputDir": "coverage",
    "additionalArgs": ["--skip-clean", "--ignore-tests"]
  }
}
```

### Python Projects
```json
{
  "projectKey": "python-project",
  "projectName": "Python Project",
  "projectVersion": "1.0.0",
  "language": "py",
  "sourceDirs": ["src", "lib"],
  "testDirs": ["tests", "test"],
  "exclusions": [
    "venv/**",
    "__pycache__/**",
    "*.pyc",
    "*.pyo",
    ".pytest_cache/**"
  ],
  "sonarHostUrl": "http://sonarqube:9000",
  "sonarToken": "squ_44characterlongtoken...",
  "coverage": {
    "tool": "pytest-cov",
    "outputFormat": "xml",
    "outputDir": "coverage",
    "additionalArgs": ["--cov=src", "--cov-report=xml"]
  },
  "customProperties": {
    "sonar.python.coverage.reportPaths": "coverage/coverage.xml",
    "sonar.python.xunit.reportPath": "coverage/xunit.xml"
  }
}
```

### JavaScript/TypeScript Projects
```json
{
  "projectKey": "js-project",
  "projectName": "JavaScript Project",
  "projectVersion": "1.0.0",
  "language": "js",
  "sourceDirs": ["src", "lib"],
  "testDirs": ["tests", "test", "__tests__"],
  "exclusions": [
    "node_modules/**",
    "dist/**",
    "build/**",
    "coverage/**",
    "*.min.js",
    "*.bundle.js"
  ],
  "sonarHostUrl": "http://sonarqube:9000",
  "sonarToken": "squ_44characterlongtoken...",
  "coverage": {
    "tool": "jest",
    "outputFormat": "lcov",
    "outputDir": "coverage",
    "additionalArgs": ["--coverage", "--coverageReporters=lcov"]
  },
  "customProperties": {
    "sonar.javascript.lcov.reportPaths": "coverage/lcov.info"
  }
}
```

### Java Projects
```json
{
  "projectKey": "java-project",
  "projectName": "Java Project",
  "projectVersion": "1.0.0",
  "language": "java",
  "sourceDirs": ["src/main/java"],
  "testDirs": ["src/test/java"],
  "exclusions": [
    "target/**",
    "build/**",
    "*.class",
    "*.jar"
  ],
  "sonarHostUrl": "http://sonarqube:9000",
  "sonarToken": "squ_44characterlongtoken...",
  "coverage": {
    "tool": "jacoco",
    "outputFormat": "xml",
    "outputDir": "target/site/jacoco",
    "additionalArgs": []
  },
  "customProperties": {
    "sonar.java.binaries": "target/classes",
    "sonar.java.test.binaries": "target/test-classes",
    "sonar.jacoco.reportPaths": "target/site/jacoco/jacoco.xml"
  }
}
```

### Multi-Language Projects
```json
{
  "projectKey": "multi-lang-project",
  "projectName": "Multi-Language Project",
  "projectVersion": "1.0.0",
  "language": "js",
  "sourceDirs": [
    "frontend/src",
    "backend/src",
    "shared/src"
  ],
  "testDirs": [
    "frontend/tests",
    "backend/tests",
    "shared/tests"
  ],
  "exclusions": [
    "frontend/node_modules/**",
    "backend/target/**",
    "frontend/dist/**",
    "**/*.min.js"
  ],
  "sonarHostUrl": "http://sonarqube:9000",
  "sonarToken": "squ_44characterlongtoken...",
  "coverage": {
    "tool": "multi",
    "outputFormat": "xml",
    "outputDir": "coverage",
    "additionalArgs": []
  },
  "customProperties": {
    "sonar.javascript.lcov.reportPaths": "coverage/frontend/lcov.info",
    "sonar.python.coverage.reportPaths": "coverage/backend/coverage.xml",
    "sonar.java.binaries": "backend/target/classes"
  }
}
```

## Configuration Management Workflow

### 1. Creating New Configuration
```bash
# Method 1: Use setup script (recommended)
./setup-sonarqube.sh "My Project" "my-project" "1.0.0" rust "http://sonarqube:9000"

# Method 2: Manual creation
cp sonar-config.json.template sonar-config.json
vim sonar-config.json
```

### 2. Validating Configuration
```bash
# Validate JSON syntax
jq . sonar-config.json

# Expected: Formatted JSON without errors

# Validate with loader script
bash scripts/sonar/config_loader.sh

# Expected: "Configuration loaded successfully"
```

### 3. Testing Configuration
```bash
# Test token validity
TOKEN=$(jq -r '.sonarToken' sonar-config.json)
curl -u "$TOKEN:" "http://localhost:9000/api/authentication/validate"

# Test project exists
PROJECT_KEY=$(jq -r '.projectKey' sonar-config.json)
curl -u admin:admin "http://localhost:9000/api/components/tree?component=$PROJECT_KEY"
```

### 4. Updating Configuration
```bash
# Edit configuration
vim sonar-config.json

# Regenerate properties
bash scripts/sonar/sonar_scanner.sh create_properties

# Verify properties
cat sonar-project.properties
```

## Advanced Configuration Options

### 1. Custom Quality Gates
```json
{
  "qualityGate": {
    "name": "Custom Quality Gate",
    "conditions": [
      {
        "metric": "coverage",
        "op": "LT",
        "error": "80"
      },
      {
        "metric": "reliability_rating",
        "op": "GT",
        "error": "1"
      }
    ]
  }
}
```

### 2. Multi-Module Projects
```json
{
  "modules": [
    {
      "key": "module1",
      "name": "Module 1",
      "sourceDirs": ["module1/src"],
      "testDirs": ["module1/tests"]
    },
    {
      "key": "module2", 
      "name": "Module 2",
      "sourceDirs": ["module2/src"],
      "testDirs": ["module2/tests"]
    }
  ],
  "sourceDirs": ["module1/src", "module2/src"],
  "testDirs": ["module1/tests", "module2/tests"]
}
```

### 3. Environment-Specific Configuration
```bash
# Development config
cp sonar-config.json sonar-config.dev.json
# Edit for development settings

# Production config
cp sonar-config.json sonar-config.prod.json
# Edit for production settings

# Use environment-specific config
CONFIG_FILE="sonar-config.${ENV}.json"
if [[ -f "$CONFIG_FILE" ]]; then
    cp "$CONFIG_FILE" sonar-config.json
fi
```

### 4. Custom Properties
```json
{
  "customProperties": {
    "sonar.scm.provider": "git",
    "sonar.scm.exclusions.disabled": "true",
    "sonar.issue.ignore.multicriteria": "e1,e2",
    "sonar.issuesReport.html.enable": "true",
    "sonar.coverage.exclusions": "**/*Test*.java,**/generated/**",
    "sonar.cpd.exclusions": "**/*generated*.*,**/test/**",
    "sonar.externalIssuesReportPaths": "external-issues.json"
  }
}
```

## Configuration Templates

### Template 1: Minimal Rust Project
```json
{
  "projectKey": "my-rust-project",
  "projectName": "My Rust Project",
  "projectVersion": "0.1.0",
  "language": "rust",
  "sourceDirs": ["src"],
  "exclusions": ["target/**"],
  "sonarHostUrl": "http://sonarqube:9000",
  "sonarToken": "squ_REPLACE_WITH_TOKEN",
  "coverage": {
    "tool": "cargo-tarpaulin",
    "outputFormat": "xml",
    "outputDir": "coverage"
  }
}
```

### Template 2: Full-Featured Python Project
```json
{
  "projectKey": "my-python-project",
  "projectName": "My Python Project",
  "projectVersion": "1.0.0",
  "language": "py",
  "sourceDirs": ["src", "lib"],
  "testDirs": ["tests", "test"],
  "exclusions": [
    "venv/**",
    "__pycache__/**",
    "*.pyc",
    ".pytest_cache/**",
    "migrations/**"
  ],
  "sonarHostUrl": "http://sonarqube:9000",
  "sonarToken": "squ_REPLACE_WITH_TOKEN",
  "coverage": {
    "tool": "pytest-cov",
    "outputFormat": "xml",
    "outputDir": "coverage",
    "additionalArgs": ["--cov=src", "--cov-report=xml"]
  },
  "customProperties": {
    "sonar.python.coverage.reportPaths": "coverage/coverage.xml",
    "sonar.python.xunit.reportPath": "coverage/xunit.xml",
    "sonar.python.flake8.reportPaths": "reports/flake8.txt",
    "sonar.python.bandit.reportPaths": "reports/bandit.json"
  }
}
```

### Template 3: Enterprise Java Project
```json
{
  "projectKey": "my-java-project",
  "projectName": "My Java Project",
  "projectVersion": "1.0.0",
  "language": "java",
  "sourceDirs": ["src/main/java"],
  "testDirs": ["src/test/java"],
  "exclusions": [
    "target/**",
    "build/**",
    "*.class",
    "*.jar",
    "src/main/resources/**/generated/**"
  ],
  "sonarHostUrl": "http://sonarqube:9000",
  "sonarToken": "squ_REPLACE_WITH_TOKEN",
  "coverage": {
    "tool": "jacoco",
    "outputFormat": "xml",
    "outputDir": "target/site/jacoco"
  },
  "customProperties": {
    "sonar.java.binaries": "target/classes",
    "sonar.java.test.binaries": "target/test-classes",
    "sonar.jacoco.reportPaths": "target/site/jacoco/jacoco.xml",
    "sonar.java.source": "17",
    "sonar.java.target": "17",
    "sonar.scm.provider": "git",
    "sonar.java.spotbugs.reportPaths": "target/spotbugsXml.xml"
  }
}
```

## Configuration Scripts

### 1. Configuration Generator Script
```bash
#!/bin/bash
# generate_config.sh

PROJECT_NAME="$1"
PROJECT_KEY="$2"
LANGUAGE="$3"
OUTPUT_FILE="$4"

if [[ -z "$OUTPUT_FILE" ]]; then
    OUTPUT_FILE="sonar-config.json"
fi

cat > "$OUTPUT_FILE" << EOF
{
  "projectKey": "$PROJECT_KEY",
  "projectName": "$PROJECT_NAME",
  "projectVersion": "1.0.0",
  "language": "$LANGUAGE",
EOF

# Add language-specific configuration
case "$LANGUAGE" in
    "rust")
        cat >> "$OUTPUT_FILE" << EOF
  "sourceDirs": ["src"],
  "testDirs": ["tests"],
  "exclusions": ["target/**"],
  "coverage": {
    "tool": "cargo-tarpaulin",
    "outputFormat": "xml",
    "outputDir": "coverage"
  }
EOF
        ;;
    "py")
        cat >> "$OUTPUT_FILE" << EOF
  "sourceDirs": ["src", "lib"],
  "testDirs": ["tests", "test"],
  "exclusions": ["venv/**", "__pycache__/**"],
  "coverage": {
    "tool": "pytest-cov",
    "outputFormat": "xml",
    "outputDir": "coverage"
  }
EOF
        ;;
    "js")
        cat >> "$OUTPUT_FILE" << EOF
  "sourceDirs": ["src", "lib"],
  "testDirs": ["tests", "test"],
  "exclusions": ["node_modules/**", "dist/**"],
  "coverage": {
    "tool": "jest",
    "outputFormat": "lcov",
    "outputDir": "coverage"
  }
EOF
        ;;
esac

# Add common fields
cat >> "$OUTPUT_FILE" << EOF
  "sonarHostUrl": "http://sonarqube:9000",
  "sonarToken": "squ_REPLACE_WITH_TOKEN"
}
EOF

echo "Configuration generated: $OUTPUT_FILE"
echo "Please update the sonarToken field with your actual token."
```

### 2. Configuration Validator Script
```bash
#!/bin/bash
# validate_config.sh

CONFIG_FILE="$1"

if [[ -z "$CONFIG_FILE" ]]; then
    CONFIG_FILE="sonar-config.json"
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "❌ Configuration file not found: $CONFIG_FILE"
    exit 1
fi

echo "=== Validating Configuration ==="

# Check JSON syntax
if jq . "$CONFIG_FILE" > /dev/null 2>&1; then
    echo "✅ JSON syntax is valid"
else
    echo "❌ Invalid JSON syntax"
    exit 1
fi

# Check required fields
REQUIRED_FIELDS=("projectKey" "projectName" "projectVersion" "language" "sourceDirs" "sonarHostUrl" "sonarToken")

for field in "${REQUIRED_FIELDS[@]}"; do
    if jq -e ".$field" "$CONFIG_FILE" > /dev/null; then
        echo "✅ $field field exists"
    else
        echo "❌ $field field missing"
    fi
done

# Validate project key format
PROJECT_KEY=$(jq -r '.projectKey' "$CONFIG_FILE")
if [[ "$PROJECT_KEY" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "✅ Project key format is valid"
else
    echo "❌ Project key contains invalid characters"
fi

# Validate token format
TOKEN=$(jq -r '.sonarToken' "$CONFIG_FILE")
if [[ "$TOKEN" =~ ^squ_[a-zA-Z0-9]{40}$ ]]; then
    echo "✅ Token format is valid"
else
    echo "❌ Token format is invalid (should be 44 chars starting with squ_)"
fi

echo "=== Validation Complete ==="
```

### 3. Configuration Updater Script
```bash
#!/bin/bash
# update_config.sh

CONFIG_FILE="sonar-config.json"
FIELD="$1"
VALUE="$2"

if [[ -z "$FIELD" || -z "$VALUE" ]]; then
    echo "Usage: $0 <field> <value>"
    echo "Example: $0 projectVersion 1.1.0"
    exit 1
fi

# Backup original config
cp "$CONFIG_FILE" "$CONFIG_FILE.backup"

# Update field
jq ".$FIELD = \"$VALUE\"" "$CONFIG_FILE.backup" > "$CONFIG_FILE"

echo "Updated $FIELD to $VALUE"
echo "Backup saved as $CONFIG_FILE.backup"
```

## Environment Variables

### Configuration Override Variables
```bash
# Override config file values
export SONAR_PROJECT_KEY="custom-project-key"
export SONAR_PROJECT_NAME="Custom Project Name"
export SONAR_PROJECT_VERSION="2.0.0"
export SONAR_LANGUAGE="rust"
export SONAR_HOST_URL="http://custom-sonarqube:9000"
export SONAR_TOKEN="squ_customtoken..."

# Override coverage settings
export COVERAGE_TOOL="cargo-tarpaulin"
export COVERAGE_OUTPUT_FORMAT="xml"
export COVERAGE_OUTPUT_DIR="coverage"
```

### Environment-Specific Configuration
```bash
#!/bin/bash
# load_env_config.sh

ENVIRONMENT="${ENVIRONMENT:-development}"

echo "Loading configuration for environment: $ENVIRONMENT"

# Load environment-specific config
CONFIG_FILE="sonar-config.${ENVIRONMENT}.json"
if [[ -f "$CONFIG_FILE" ]]; then
    echo "Using environment-specific config: $CONFIG_FILE"
    cp "$CONFIG_FILE" sonar-config.json
else
    echo "Using default config: sonar-config.json"
fi

# Override with environment variables
if [[ -n "$SONAR_TOKEN" ]]; then
    jq ".sonarToken = \"$SONAR_TOKEN\"" sonar-config.json > temp.json
    mv temp.json sonar-config.json
fi

if [[ -n "$SONAR_HOST_URL" ]]; then
    jq ".sonarHostUrl = \"$SONAR_HOST_URL\"" sonar-config.json > temp.json
    mv temp.json sonar-config.json
fi
```

## Best Practices

### 1. Configuration Management
- ✅ Store configuration in version control (except tokens)
- ✅ Use environment variables for sensitive data
- ✅ Validate configuration before use
- ✅ Document configuration changes
- ✅ Use templates for consistency

### 2. Security Practices
- ✅ Never commit tokens to version control
- ✅ Use token rotation policies
- ✅ Limit token permissions
- ✅ Store tokens in secure environment variables
- ✅ Use different tokens per project/environment

### 3. Maintenance Practices
- ✅ Regularly update configuration schema
- ✅ Keep documentation current
- ✅ Test configuration changes
- ✅ Monitor configuration usage
- ✅ Backup working configurations

## Troubleshooting Configuration

### Common Issues

#### Invalid JSON Syntax
```bash
# Error: parse error: Invalid numeric literal at line X
# Solution: Validate JSON syntax
jq . sonar-config.json

# Fix common issues:
# - Missing commas
# - Trailing commas
# - Unquoted strings
# - Invalid escape characters
```

#### Missing Required Fields
```bash
# Error: Required field 'projectKey' is missing
# Solution: Add missing field
jq '.projectKey = "my-project"' sonar-config.json > temp.json
mv temp.json sonar-config.json
```

#### Invalid Token Format
```bash
# Error: Token format is invalid
# Solution: Generate new token and update
curl -X POST -u admin:admin \
  "http://localhost:9000/api/user_tokens/generate?name=new-token"

# Update config with new token
jq '.sonarToken = "squ_44characterlongtoken..."' sonar-config.json > temp.json
mv temp.json sonar-config.json
```

#### Network Configuration Issues
```bash
# Error: Cannot connect to SonarQube server
# Solution: Check URL and network connectivity
jq '.sonarHostUrl = "http://sonarqube:9000"' sonar-config.json > temp.json
mv temp.json sonar-config.json

# Test connectivity
curl "$(jq -r '.sonarHostUrl' sonar-config.json)/api/system/status"
```

## Quick Reference

### Essential Commands
```bash
# Validate configuration
bash validate_config.sh

# Generate new config
bash generate_config.sh "My Project" "my-project" rust

# Update configuration
bash update_config.sh projectVersion 1.1.0

# Test configuration
bash scripts/sonar/config_loader.sh
```

### Configuration Templates
- **Rust**: Minimal, Full-featured
- **Python**: Basic, Enterprise
- **JavaScript**: Simple, Advanced
- **Java**: Standard, Enterprise
- **Multi-Language**: Complex project

### Key Files
- `sonar-config.json`: Main configuration
- `scripts/sonar/config_loader.sh`: Configuration loader
- `sonar-project.properties`: Generated scanner config

## Next Steps

After mastering configuration management:
1. 📖 Read **Runbook 6** for troubleshooting
2. 🚀 Create custom configurations for your projects
3. 🔧 Set up automated configuration validation
4. 📊 Monitor configuration usage and performance

## Support Resources

### Documentation
- SonarQube Configuration: https://docs.sonarsource.com/sonarqube/latest/administration/configuration/
- JSON Validation: https://jsonlint.com/
- jq Manual: https://stedolan.github.io/jq/manual/

### Tools
- Online JSON Validator: https://jsonformatter.org/
- SonarQube Project Configurator: Built-in web interface
- Configuration Generator Scripts: Included in this runbook
