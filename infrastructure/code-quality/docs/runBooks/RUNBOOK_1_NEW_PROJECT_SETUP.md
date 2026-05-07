# Runbook 1: New Project Configuration and Token Creation

## Overview
This runbook covers the complete process of setting up a new project for SonarQube analysis, including token creation, project configuration, and initial setup.

## Prerequisites
- SonarQube server running and accessible
- Admin access to SonarQube
- Docker and Docker Compose installed
- Project directory with source code

## Step 1: Automatic Setup (Recommended)

### Using the Setup Script
```bash
# Navigate to your project directory
cd /path/to/your/project

# Run the automated setup script
./setup-sonarqube.sh "Project Name" "project-key" "1.0.0" rust "http://sonarqube:9000" admin admin
```

**Parameters:**
- `Project Name`: Human-readable project name
- `project-key`: Unique identifier (no spaces, special chars)
- `1.0.0`: Project version
- `rust`: Programming language
- `http://sonarqube:9000`: SonarQube server URL
- `admin`: Admin username
- `admin`: Admin password

### What the Script Does
1. ✅ Checks dependencies (Docker, curl, jq)
2. ✅ Waits for SonarQube server to be ready
3. ✅ Generates authentication token
4. ✅ Creates project in SonarQube
5. ✅ Creates `sonar-config.json` configuration file
6. ✅ Sets up scripts directory structure
7. ✅ Creates Makefile for easy commands

## Step 2: Manual Setup

### 2.1 Generate Authentication Token

#### Method A: Via API (Recommended)
```bash
# Generate token via SonarQube API
curl -X POST -u admin:admin \
  "http://localhost:9000/api/user_tokens/generate?name=my-project-token"

# Expected response:
# {"login":"admin","name":"my-project-token","token":"squ_44characterlongtoken..."}
```

#### Method B: Via Web UI
1. Login to SonarQube at http://localhost:9000
2. Click on your username (top right) → "My Account"
3. Go to "Security" tab
4. Enter token name (e.g., "my-project-token")
5. Click "Generate"
6. **IMPORTANT**: Copy the full token immediately (44 characters starting with "squ_")

### 2.2 Create Project in SonarQube

#### Method A: Via API (Recommended)
```bash
# Create project via API
curl -X POST -u admin:admin \
  "http://localhost:9000/api/projects/create?project=my-project-key&name=My%20Project"

# Expected response:
# {"project":{"key":"my-project-key","name":"My Project",...}}
```

#### Method B: Via Web UI
1. Login to SonarQube
2. Click "+" → "Create new project"
3. Select "Manually"
4. Enter project key and display name
5. Click "Set up"

### 2.3 Create Configuration File

Create `sonar-config.json` in your project root:

```json
{
  "projectKey": "my-project-key",
  "projectName": "My Project",
  "projectVersion": "1.0.0",
  "language": "rust",
  "sourceDirs": [
    "src"
  ],
  "testDirs": [
    "tests"
  ],
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
    "outputDir": "coverage"
  }
}
```

**Important Notes:**
- `projectKey`: Must be unique across SonarQube instance
- `sonarToken`: Must be exactly 44 characters starting with "squ_"
- `sonarHostUrl`: Use "http://sonarqube:9000" for Docker network

### 2.4 Verify Token Validity

```bash
# Test your token
TOKEN="squ_44characterlongtoken..."
curl -u "${TOKEN}:" "http://localhost:9000/api/authentication/validate"

# Expected response: {"valid":true}
```

## Step 3: Language-Specific Configuration

### Rust Projects
```json
{
  "language": "rust",
  "sourceDirs": ["src"],
  "testDirs": ["tests"],
  "coverage": {
    "tool": "cargo-tarpaulin",
    "outputFormat": "xml",
    "outputDir": "coverage"
  }
}
```

### Python Projects
```json
{
  "language": "py",
  "sourceDirs": ["src", "lib"],
  "testDirs": ["tests", "test"],
  "coverage": {
    "tool": "pytest-cov",
    "outputFormat": "xml",
    "outputDir": "coverage"
  }
}
```

### JavaScript/TypeScript Projects
```json
{
  "language": "js",
  "sourceDirs": ["src", "lib"],
  "testDirs": ["tests", "test", "__tests__"],
  "coverage": {
    "tool": "jest",
    "outputFormat": "lcov",
    "outputDir": "coverage"
  }
}
```

## Step 4: Project Structure Requirements

Your project should have this structure:
```
my-project/
├── sonar-config.json          # Configuration file
├── src/                       # Source code
├── tests/                     # Test files (optional)
├── scripts/sonar/             # SonarQube scripts (auto-created)
├── Makefile                   # Build commands (auto-created)
└── coverage/                  # Coverage reports (auto-generated)
```

## Step 5: Common Configuration Scenarios

### Scenario 1: Multi-Module Project
```json
{
  "sourceDirs": ["module1/src", "module2/src", "shared/src"],
  "testDirs": ["module1/tests", "module2/tests", "shared/tests"]
}
```

### Scenario 2: Exclude Generated Code
```json
{
  "exclusions": [
    "target/**",
    "generated/**",
    "**/*.pb.go",
    "**/*_generated.rs",
    "node_modules/**",
    "dist/**",
    "build/**"
  ]
}
```

### Scenario 3: Custom Coverage Tool
```json
{
  "coverage": {
    "tool": "gcovr",
    "outputFormat": "cobertura",
    "outputDir": "coverage",
    "command": "gcovr --xml --output coverage.xml"
  }
}
```

## Step 6: Validation

### 6.1 Validate Configuration
```bash
# Check if configuration is valid
jq . sonar-config.json

# Should return formatted JSON without errors
```

### 6.2 Test Project Access
```bash
# Test if project is accessible
TOKEN="squ_44characterlongtoken..."
curl -u "${TOKEN}:" \
  "http://localhost:9000/api/components/tree?component=my-project-key"
```

### 6.3 Verify Server Connectivity
```bash
# Check server status
curl "http://localhost:9000/api/system/status"

# Should return: {"status":"UP"}
```

## Step 7: Security Best Practices

### Token Management
- ✅ Use descriptive token names
- ✅ Generate separate tokens per project
- ✅ Store tokens securely (environment variables, not in code)
- ✅ Revoke tokens when no longer needed

### Project Security
- ✅ Use appropriate project permissions
- ✅ Regularly rotate tokens
- ✅ Monitor project access logs

## Step 8: Troubleshooting

### Common Issues

#### Token Too Short
**Problem**: Token appears truncated (less than 44 characters)
**Solution**: Regenerate token via API, not UI copy-paste

```bash
# Regenerate via API
curl -X POST -u admin:admin \
  "http://localhost:9000/api/user_tokens/generate?name=new-token"
```

#### Project Already Exists
**Problem**: "Could not create Project with key" error
**Solution**: Check if project exists or use different key

```bash
# Check existing projects
curl -u admin:admin "http://localhost:9000/api/projects/search"
```

#### Invalid Configuration
**Problem**: JSON parsing errors
**Solution**: Validate JSON syntax

```bash
# Validate JSON
jq . sonar-config.json
```

## Step 9: Next Steps

After completing this setup:
1. 📖 Read **Runbook 2** for running and configuration
2. 📖 Read **Runbook 3** for reports and access
3. 📖 Read **Runbook 4** for dependencies and tools
4. 🚀 Run your first analysis: `make sonar-analyze`

## Quick Reference Commands

```bash
# Generate token
curl -X POST -u admin:admin "http://localhost:9000/api/user_tokens/generate?name=project-token"

# Create project  
curl -X POST -u admin:admin "http://localhost:9000/api/projects/create?project=my-key&name=My%20Project"

# Test token
curl -u "squ_token:" "http://localhost:9000/api/authentication/validate"

# Check server status
curl "http://localhost:9000/api/system/status"

# Run setup script
./setup-sonarqube.sh "My Project" "my-key" "1.0.0" rust "http://sonarqube:9000"
```

## Support

If you encounter issues:
1. Check SonarQube logs: `docker logs sonarqube`
2. Verify network connectivity
3. Check token validity
4. Review configuration syntax
5. Consult **Runbook 6** for detailed troubleshooting
