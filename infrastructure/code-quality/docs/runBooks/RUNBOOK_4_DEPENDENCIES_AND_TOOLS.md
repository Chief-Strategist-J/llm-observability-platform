# Runbook 4: Dependencies and Required Tools

## Overview
This runbook covers all dependencies, required tools, project structures, and command-line tools needed for the SonarQube DTAE setup, including SonarQube Community, Scanner CLI, and all supporting tools.

## Core Dependencies

### 1. SonarQube Server Components

#### SonarQube Community Edition
- **Purpose**: Main analysis server and web interface
- **Version**: Latest Community Edition (currently 26.4.0.121862)
- **Deployment**: Docker container
- **Requirements**: Docker, Docker Compose

#### PostgreSQL Database
- **Purpose**: SonarQube data storage
- **Version**: Included with SonarQube Docker setup
- **Deployment**: Docker container (managed by Docker Compose)

### 2. Analysis Tools

#### SonarScanner CLI
- **Purpose**: Command-line scanner for code analysis
- **Version**: 8.0.1.6346 (or latest)
- **Deployment**: Docker container
- **Image**: `sonarsource/sonar-scanner-cli`

#### Language-Specific Tools
- **Rust**: `cargo-tarpaulin` (coverage)
- **Python**: `pytest-cov` (coverage)
- **JavaScript**: `jest` (coverage)
- **Java**: `jacoco` (coverage)

## System Requirements

### Minimum Hardware Requirements
```
CPU: 2 cores minimum, 4 cores recommended
RAM: 4GB minimum, 8GB recommended, 16GB for large projects
Storage: 10GB free space minimum, 50GB recommended for multiple projects
Network: Internet access for downloads (Docker Hub, package repositories)
Swap: 2GB recommended for systems with <8GB RAM
```

### Detailed Hardware Analysis

#### CPU Requirements by Project Size
- **Small Projects** (<10K LOC): 2 cores sufficient
- **Medium Projects** (10K-100K LOC): 4 cores recommended  
- **Large Projects** (>100K LOC): 8+ cores recommended
- **Multi-project Analysis**: 4+ cores per concurrent analysis

#### Memory Requirements Analysis
```
Component                    Minimum    Recommended    Notes
SonarQube Server             1GB        2GB           Base server
PostgreSQL Database          512MB      1GB           Data storage
SonarScanner CLI             512MB      2GB           Analysis engine
Rust Compiler (if needed)    1GB        2GB           For cargo-tarpaulin
Docker Overhead             512MB      1GB           Container runtime
System Overhead              1GB        2GB           OS and services
TOTAL                        3.5GB      8GB           Minimum system
```

#### Storage Requirements by Project Type
- **Rust Projects**: 500MB base + 100MB per 10K LOC
- **Python Projects**: 300MB base + 50MB per 10K LOC  
- **JavaScript Projects**: 200MB base + 30MB per 10K LOC
- **Java Projects**: 1GB base + 200MB per 10K LOC
- **Multi-language**: Sum of all languages + 20% overhead

### Software Requirements

#### Docker Platform
```bash
# Check Docker installation
docker --version
# Expected: Docker version 20.10.x or later

# Check Docker Compose
docker-compose --version
# Expected: docker-compose version 2.0.x or later
```

#### Operating System Support
- ✅ Linux (Ubuntu 18.04+, CentOS 7+, Debian 9+)
- ✅ macOS (10.14+)
- ✅ Windows 10/11 with WSL2
- ❌ Windows without WSL (limited support)

## Installation Guide

### 1. Docker Installation

#### Ubuntu/Debian
```bash
# Update package index
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER

# Reboot or log out/in to apply group changes
newgrp docker
```

#### macOS
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop
brew install --cask docker

# Start Docker Desktop
open /Applications/Docker.app
```

#### Windows (WSL2)
```powershell
# Install WSL2
wsl --install

# Install Docker Desktop for Windows
# Download from: https://www.docker.com/products/docker-desktop

# Enable WSL2 integration in Docker Desktop settings
```

### 2. Verify Docker Setup
```bash
# Test Docker
docker run hello-world

# Test Docker Compose
docker-compose --version

# Check system info
docker system info
```

## SonarQube Server Setup

### 1. Docker Compose Configuration
Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  sonarqube:
    image: sonarqube:community
    container_name: sonarqube
    ports:
      - "9000:9000"
    environment:
      - SONAR_JDBC_URL=jdbc:postgresql://db:5432/sonar
      - SONAR_JDBC_USERNAME=sonar
      - SONAR_JDBC_PASSWORD=sonar
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_logs:/opt/sonarqube/logs
      - sonarqube_extensions:/opt/sonarqube/extensions
    networks:
      - sonarqube_network
    depends_on:
      - db

  db:
    image: postgres:13
    container_name: sonarqube_db
    environment:
      - POSTGRES_USER=sonar
      - POSTGRES_PASSWORD=sonar
      - POSTGRES_DB=sonar
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - sonarqube_network

volumes:
  sonarqube_data:
  sonarqube_logs:
  sonarqube_extensions:
  postgres_data:

networks:
  sonarqube_network:
    driver: bridge
```

### 2. Start SonarQube Server
```bash
# Start services
docker-compose up -d

# Wait for initialization (2-3 minutes)
docker-compose logs -f sonarqube

# Check server status
curl http://localhost:9000/api/system/status
```

### 3. Initial Configuration
```bash
# Wait for server to be ready
until curl -s http://localhost:9000/api/system/status | grep -q "UP"; do
  echo "Waiting for SonarQube..."
  sleep 10
done

# Change default password (optional but recommended)
curl -X POST -u admin:admin \
  "http://localhost:9000/api/users/change_password?login=admin&previousPassword=admin&password=newpassword"
```

## Language-Specific Tools

### Rust Projects

#### Cargo Tarpaulin (Coverage Tool)
```bash
# Install via cargo
cargo install cargo-tarpaulin

# Verify installation
cargo tarpaulin --version

# Generate coverage
cargo tarpaulin --output-dir coverage --output-format xml

# Expected output: coverage/cobertura.xml
```

#### Rust Toolchain Requirements
```bash
# Install Rust (if not installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Verify installation
rustc --version
cargo --version

# Install required components
rustup component add rustfmt clippy
```

### Python Projects

#### Coverage Tools
```bash
# Install pytest and coverage
pip install pytest pytest-cov

# Generate coverage report
pytest --cov=src --cov-report=xml tests/

# Expected output: coverage.xml
```

#### Python Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### JavaScript/TypeScript Projects

#### Jest Coverage
```bash
# Install Jest and coverage
npm install --save-dev jest

# Generate coverage
npm test -- --coverage

# Expected output: coverage/lcov.info
```

#### Node.js Setup
```bash
# Install Node.js (using nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install node
nvm use node

# Verify installation
node --version
npm --version
```

### Java Projects

#### JaCoCo Coverage
```xml
<!-- Add to pom.xml -->
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.7</version>
    <executions>
        <execution>
            <goals>
                <goal>prepare-agent</goal>
            </goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>test</phase>
            <goals>
                <goal>report</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

#### Java Requirements
```bash
# Install OpenJDK 11+ (Ubuntu/Debian)
sudo apt-get install openjdk-11-jdk

# Verify installation
java -version
javac -version

# Install Maven (optional)
sudo apt-get install maven
mvn --version
```

## Command-Line Tools

### 1. Essential Tools

#### curl (HTTP Client)
```bash
# Install (Ubuntu/Debian)
sudo apt-get install curl

# Install (macOS)
brew install curl

# Test installation
curl --version
```

#### jq (JSON Processor)
```bash
# Install (Ubuntu/Debian)
sudo apt-get install jq

# Install (macOS)
brew install jq

# Test installation
jq --version
```

#### make (Build Tool)
```bash
# Install (Ubuntu/Debian)
sudo apt-get install build-essential

# Install (macOS)
xcode-select --install

# Test installation
make --version
```

### 2. Optional Tools

#### Docker Compose V2
```bash
# Check current version
docker-compose version

# Upgrade to V2 if needed
# Follow official Docker documentation
```

#### Git (Version Control)
```bash
# Install (Ubuntu/Debian)
sudo apt-get install git

# Install (macOS)
brew install git

# Configure
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## Project Structure Requirements

### Standard DTAE Project Structure
```
distributed-trace-analysis-engine/
├── sonar-config.json              # Main configuration file
├── sonar-project.properties       # Generated scanner config
├── Makefile                       # Build commands
├── Cargo.toml                     # Rust project manifest
├── src/                          # Source code
│   ├── main.rs
│   ├── lib.rs
│   └── ...
├── tests/                        # Test files
│   └── ...
├── scripts/sonar/               # SonarQube scripts
│   ├── utils.sh
│   ├── config_loader.sh
│   ├── server_manager.sh
│   ├── coverage_generator.sh
│   ├── sonar_scanner.sh
│   └── orchestrator.sh
├── coverage/                    # Coverage reports
│   └── cobertura.xml
└── target/                      # Build artifacts
    └── ...
```

### Multi-Language Project Structure
```
multi-language-project/
├── sonar-config.json
├── Makefile
├── backend/                     # Rust/Python/Java
│   ├── src/
│   ├── tests/
│   └── pom.xml / Cargo.toml
├── frontend/                    # JavaScript/TypeScript
│   ├── src/
│   ├── tests/
│   └── package.json
├── scripts/sonar/
└── coverage/
    ├── backend/
    └── frontend/
```

## API and Service Dependencies

### 1. SonarQube Web API
- **Base URL**: http://localhost:9000/api
- **Authentication**: Token-based
- **Format**: JSON
- **Rate Limits**: None (local deployment)

### 2. External Services
- **None required** for local deployment
- **Internet access** needed for:
  - Docker image downloads
  - Tool installations
  - Documentation access

### 3. Network Requirements
- **Inbound**: Port 9000 (from host to container)
- **Outbound**: Internet (for Docker Hub)
- **Internal**: Docker network communication

## Version Compatibility Matrix

| Component | Minimum Version | Recommended Version | Latest Tested | Notes |
|-----------|-----------------|---------------------|---------------|-------|
| Docker | 20.10.x | 24.0.x | 24.0.7 | Required for all components |
| Docker Compose | 2.0.x | 2.20.x | 2.21.0 | V2 recommended |
| SonarQube | 9.9.x | 26.4.x | 26.4.0.121862 | Community Edition |
| SonarScanner CLI | 6.0.x | 8.0.x | 8.0.1.6346 | Docker image |
| Rust | 1.70.0 | 1.75.0 | 1.75.0 | For cargo-tarpaulin |
| Python | 3.8+ | 3.11+ | 3.11.5 | For pytest-cov |
| Node.js | 16.x | 20.x | 20.11.0 | For Jest coverage |
| Java | 11 | 17 | 21.0.2 | For JaCoCo |
| jq | 1.6 | 1.7 | 1.7.1 | For JSON processing |
| curl | 7.68 | 8.0 | 8.5.0 | For API calls |

### Detailed Version Requirements

#### Docker Platform
```bash
# Check Docker version requirements
docker --version
# Minimum: Docker version 20.10.0
# Recommended: Docker version 24.0.0+
# Features required: Multi-stage builds, health checks, volume mounts

docker-compose --version
# Minimum: docker-compose version 2.0.0
# Recommended: docker-compose version 2.20.0+
# Features required: Docker Compose V2 syntax, health checks
```

#### SonarQube Platform
```bash
# SonarQube Server Requirements
# Minimum: 9.9 LTS (Long Term Support)
# Recommended: 26.4 Community Edition
# Critical Features: 
# - REST API v2 support
# - Docker container support
# - Multi-language analysis
# - Quality gates

# SonarScanner CLI Requirements  
# Minimum: 6.0 (legacy support)
# Recommended: 8.0+ (current generation)
# Features required:
# - Docker image support
# - JSON configuration
# - Coverage report integration
```

#### Language Toolchains

##### Rust Ecosystem
```bash
# Rust Toolchain Requirements
rustc --version
# Minimum: 1.70.0 (for cargo-tarpaulin compatibility)
# Recommended: 1.75.0+ (stable)
# Components required: rustc, cargo, rustfmt

cargo --version
# Minimum: 1.70.0
# Recommended: 1.75.0+

cargo tarpaulin --version
# Minimum: 0.25.0
# Recommended: 0.27.0+
# Features required: XML output, Docker support
```

##### Python Ecosystem
```bash
# Python Requirements
python --version
# Minimum: 3.8.0
# Recommended: 3.11.5+
# Features required: f-strings, type hints, asyncio

pip --version
# Minimum: 21.0
# Recommended: 23.0+

# Package requirements
pytest --version
# Minimum: 6.0
# Recommended: 7.4+

pytest-cov --version
# Minimum: 3.0
# Recommended: 4.1+
```

##### JavaScript/TypeScript Ecosystem
```bash
# Node.js Requirements
node --version
# Minimum: 16.0.0
# Recommended: 20.11.0+
# Features required: ES2020, async/await

npm --version
# Minimum: 7.0
# Recommended: 10.0+

# Jest requirements
jest --version
# Minimum: 27.0
# Recommended: 29.7+
# Features required: coverage reports, TypeScript support
```

##### Java Ecosystem
```bash
# Java Requirements
java -version
# Minimum: Java 11 (LTS)
# Recommended: Java 17 (LTS) or Java 21 (latest LTS)
# Features required: Modules, var keyword, records

javac -version
# Minimum: javac 11
# Recommended: javac 17+

# Maven Requirements (if using)
mvn --version
# Minimum: 3.8.0
# Recommended: 3.9.0+

# JaCoCo Requirements
# Minimum: 0.8.0
# Recommended: 0.8.10+
# Features required: XML reports, integration with Maven/Gradle
```

### System Library Dependencies

#### Linux Systems
```bash
# Ubuntu/Debian Requirements
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    pkg-config \
    libssl-dev \
    libpq-dev \
    git \
    curl \
    jq \
    net-tools

# RHEL/CentOS Requirements
sudo yum groupinstall -y "Development Tools"
sudo yum install -y \
    pkgconfig \
    openssl-devel \
    postgresql-devel \
    git \
    curl \
    jq \
    net-tools
```

#### macOS Systems
```bash
# macOS Requirements via Homebrew
brew install \
    docker \
    docker-compose \
    git \
    curl \
    jq \
    openssl \
    postgresql

# Xcode Command Line Tools
xcode-select --install
```

#### Windows Systems (WSL2)
```powershell
# Windows Subsystem for Linux Requirements
# Install Ubuntu 20.04+ or Debian 11+
wsl --install -d Ubuntu

# Inside WSL2, follow Linux requirements
sudo apt-get update && sudo apt-get install -y docker.io docker-compose git curl jq
```

## Installation Verification Script

#!/bin/bash
# verify_installation.sh

echo "=== SonarQube DTAE Installation Verification ==="

# Check Docker
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker: $(docker --version)"
else
    echo "❌ Docker not found"
fi

# Check Docker Compose
echo "Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo "✅ Docker Compose: $(docker-compose --version)"
else
    echo "❌ Docker Compose not found"
fi

# Check curl
echo "Checking curl..."
if command -v curl &> /dev/null; then
    echo "✅ curl: $(curl --version | head -1)"
else
    echo "❌ curl not found"
fi

# Check jq
echo "Checking jq..."
if command -v jq &> /dev/null; then
    echo "✅ jq: $(jq --version)"
else
    echo "❌ jq not found"
fi

# Check make
echo "Checking make..."
if command -v make &> /dev/null; then
    echo "✅ make: $(make --version | head -1)"
else
    echo "❌ make not found"
fi

# Check SonarQube server
echo "Checking SonarQube server..."
if curl -s http://localhost:9000/api/system/status > /dev/null 2>&1; then
    echo "✅ SonarQube server is running"
else
    echo "❌ SonarQube server not accessible"
fi

echo "=== Verification Complete ==="
```

### 2. Project Structure Verification
```bash
#!/bin/bash
# verify_project_structure.sh

PROJECT_ROOT="$1"

if [[ -z "$PROJECT_ROOT" ]]; then
    PROJECT_ROOT="."
fi

echo "=== Project Structure Verification ==="

# Required files
REQUIRED_FILES=(
    "sonar-config.json"
    "Makefile"
    "scripts/sonar/utils.sh"
    "scripts/sonar/config_loader.sh"
    "scripts/sonar/server_manager.sh"
    "scripts/sonar/coverage_generator.sh"
    "scripts/sonar/sonar_scanner.sh"
    "scripts/sonar/orchestrator.sh"
)

# Check each required file
for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$PROJECT_ROOT/$file" ]]; then
        echo "✅ $file"
    else
        echo "❌ $file (missing)"
    fi
done

# Check directories
REQUIRED_DIRS=(
    "src"
    "scripts/sonar"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [[ -d "$PROJECT_ROOT/$dir" ]]; then
        echo "✅ $dir/"
    else
        echo "❌ $dir/ (missing)"
    fi
done

echo "=== Structure Verification Complete ==="
```

## Performance Considerations

### 1. Resource Allocation
```bash
# Docker daemon settings (recommended)
{
  "default-runtime": "runc",
  "default-ulimits": {
    "memlock": {
      "Name": "memlock",
      "Hard": -1,
      "Soft": -1
    }
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ]
}
```

### 2. SonarQube Performance Tuning
```yaml
# Add to docker-compose.yml for production
services:
  sonarqube:
    environment:
      - SONAR_WEB_JVMOPTS=-Xmx4g -Xms2g -XX:+UseG1GC
      - SONAR_CE_JVMOPTS=-Xmx2g -Xms1g -XX:+UseG1GC
    deploy:
      resources:
        limits:
          memory: 6g
          cpus: '2.0'
        reservations:
          memory: 4g
          cpus: '1.0'
```

### 3. Scanner Performance
```bash
# Increase scanner memory
export SONAR_SCANNER_JAVA_OPTS="-Xmx4g"

# Run with verbose output for debugging
docker run --rm --network docker_sonarqube_network \
  -e SONAR_SCANNER_JAVA_OPTS="-Xmx4g" \
  -e SONAR_HOST_URL="http://sonarqube:9000" \
  -e SONAR_TOKEN="$TOKEN" \
  -v "$(pwd):/project" \
  sonarsource/sonar-scanner-cli \
  -X -Dproject.settings=/project/sonar-project.properties
```

## Security Considerations

### 1. Container Security
```bash
# Use specific image versions (not latest)
sonarqube:community-26.4.0.121862
sonarsource/sonar-scanner-cli:8.0.1.6346

# Run containers as non-root (when possible)
# Most official images already do this
```

### 2. Network Security
```bash
# Create dedicated network
docker network create sonarqube_network

# Use internal network for communication
# No need to expose database port
```

### 3. Token Security
```bash
# Store tokens in environment variables
export SONAR_TOKEN="squ_44characterlongtoken..."

# Don't commit tokens to version control
echo "sonar-token" >> .gitignore
```

## Troubleshooting Dependencies

### Common Issues

#### Docker Permission Denied
```bash
# Fix: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo (not recommended)
sudo docker run hello-world
```

#### Port Already in Use
```bash
# Check what's using port 9000
sudo netstat -tlnp | grep :9000

# Stop conflicting service
sudo systemctl stop conflicting-service

# Or change SonarQube port in docker-compose.yml
ports:
  - "9001:9000"  # Use different host port
```

#### Out of Memory Errors
```bash
# Check available memory
free -h

# Increase Docker memory allocation
# Docker Desktop -> Settings -> Resources -> Memory

# Add swap space (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### Network Connectivity Issues
```bash
# Check Docker network
docker network ls

# Inspect network
docker network inspect docker_sonarqube_network

# Recreate network
docker network rm docker_sonarqube_network
docker network create docker_sonarqube_network
```

## Quick Installation Commands

### One-Command Setup (Ubuntu/Debian)
```bash
# Install Docker and dependencies
curl -fsSL https://get.docker.com -o get-docker.sh && \
sudo sh get-docker.sh && \
sudo usermod -aG docker $USER && \
sudo apt-get install -y curl jq make && \
newgrp docker

# Start SonarQube
cd /path/to/project && \
make sonar-start

# Install project dependencies
make sonar-setup
```

### Verification Commands
```bash
# Verify all components
./verify_installation.sh
./verify_project_structure.sh

# Test complete workflow
make sonar-analyze
```

## Next Steps

After completing this setup:
1. 📖 Read **Runbook 5** for configuration management
2. 📖 Read **Runbook 6** for troubleshooting
3. 🚀 Run your first analysis
4. 🔧 Configure automated scanning

## Support Resources

### Documentation
- SonarQube Official Docs: https://docs.sonarsource.com/
- Docker Documentation: https://docs.docker.com/
- Cargo Tarpaulin: https://github.com/RustSec/rustsec-crate

### Community Support
- SonarQube Community: https://community.sonarsource.com/
- Stack Overflow: https://stackoverflow.com/questions/tagged/sonarqube

### Issue Reporting
- SonarQube Issues: https://github.com/SonarSource/sonarqube/issues
- Docker Issues: https://github.com/docker/docker/issues
