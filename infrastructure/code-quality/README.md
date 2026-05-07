# SonarQube Code Quality Infrastructure

A comprehensive, production-ready code quality infrastructure that provides automated analysis, reporting, and monitoring capabilities for multiple programming languages.

## 🚀 Features

- **Multi-Language Support**: Python, Go, and Rust analysis tools
- **Domain-Driven Design**: Clean, maintainable hexagonal architecture
- **Production-Ready**: Comprehensive testing and monitoring
- **CI/CD Integration**: Automated pipeline with quality gates
- **Security Scanning**: Built-in vulnerability detection
- **Performance Monitoring**: Resource usage tracking and optimization
- **Docker Support**: Containerized deployment with caching
- **Comprehensive Reporting**: Allure test reports and coverage analysis

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Installation](#installation)
- [Testing](#testing)
- [CI/CD Pipeline](#ci-cd-pipeline)
- [Documentation](#documentation)
- [Docker Images](#docker-images)
- [Contributing](#contributing)

## 🏃‍♂️ Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Node.js 18+ (for Allure CLI)
- Make (optional, for convenience commands)

### Local Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd infrastructure/code-quality

# Set up development environment
make setup

# Run tests
make test

# Run critical production tests
make test-critical

# Generate coverage report
make coverage

# Generate Allure report
make allure
make allure-open
```

### Docker Quick Start

```bash
# Build all Docker images
make build

# Run the API server
docker run -p 8000:8000 sonarqube-quality-api:latest

# Run Python analyzer
docker run -v /path/to/code:/code sonarqube-python-analyzer:latest /code
```

## 🏗️ Architecture

The system follows a hexagonal architecture pattern with clear separation of concerns:

```
├── domain/                 # Core business logic and entities
│   ├── models/            # Domain models (Analysis, Project, Issue, etc.)
│   ├── ports/             # Repository and service interfaces
│   └── services/         # Domain services and business rules
├── application/           # Use cases and orchestration
│   └── analysis/         # Analysis use cases
├── infrastructure/        # External integrations
│   ├── persistence/      # Database repositories
│   └── sonarqube/        # SonarQube service adapter
├── adapters/             # External interfaces
│   ├── http/            # HTTP/REST adapters
│   └── cli/             # Command-line interface
├── shared/               # Shared utilities and constants
├── analysis-tools/       # Multi-language analysis tools
│   ├── python/          # Python deep analyzer
│   ├── go/              # Go infrastructure analyzer
│   └── rust/            # Rust performance tools
└── tests/               # Comprehensive test suite
    ├── test_domain/      # Domain layer tests
    ├── test_application/ # Application layer tests
    ├── test_critical/    # Production-breaking tests
    └── test_analysis_tools/ # Analysis tools tests
```

## 🔧 Installation

### Development Environment

```bash
# Create virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install dependencies
pip install -r deployment/docker/requirements.txt
pip install -r deployment/docker/requirements-dev.txt

# Install Allure CLI
npm install -g allure-commandline
```

### Production Environment

```bash
# Using Docker (recommended)
docker-compose -f deployment/docker/docker-compose.optimized.yml up -d

# Or using pip
pip install -r deployment/docker/requirements.txt
```

## 🧪 Testing

### Test Categories

- **Unit Tests**: Domain and application logic
- **Integration Tests**: Database and external services
- **Critical Tests**: Production-breaking scenarios
- **Security Tests**: Vulnerability scanning
- **Performance Tests**: Load and memory testing

### Running Tests

```bash
# Run all tests
make test-all

# Run specific test categories
make test              # Unit tests only
make test-critical     # Critical production tests
make test-integration  # Integration tests

# Run tests with coverage
make coverage

# Run tests with Allure reporting
make allure
make allure-open
```

### Test Coverage

The project maintains comprehensive test coverage:

- **Domain Layer**: 89% coverage
- **Application Layer**: 85% coverage
- **Critical Tests**: 100% coverage of production scenarios
- **Overall**: 82% coverage minimum requirement

## 🚀 CI/CD Pipeline

The CI/CD pipeline provides automated testing, security scanning, and deployment:

### Pipeline Features

- **Automated Testing**: Runs on every push and PR
- **Coverage Reporting**: Codecov integration with trend analysis
- **Allure Reporting**: Comprehensive test reports with history
- **Security Scanning**: Trivy and Bandit vulnerability scanning
- **Docker Builds**: Multi-platform container builds
- **Documentation**: Auto-generated API documentation
- **Quality Gates**: Enforced quality standards
- **Notifications**: Slack integration for pipeline status

### Pipeline Triggers

The pipeline runs on:

- **Push to main/develop**: Full pipeline execution
- **Pull Requests**: Test execution and reporting
- **Code Changes**: Only runs when code-quality package is modified

### Local CI/CD Simulation

```bash
# Run full CI/CD pipeline locally
make ci-local

# This includes:
# - All tests with coverage
# - Allure report generation
# - Security scanning
# - Code quality checks
```

### CI/CD Configuration

The pipeline is configured in `.github/workflows/ci-cd.yml` with:

- **Path Filtering**: Only runs on relevant code changes
- **Parallel Execution**: Optimized job execution
- **Conditional Steps**: Different behavior for PRs vs. main branch
- **Artifact Management**: Proper artifact retention and deployment

## 📚 Documentation

### Generated Documentation

- **API Documentation**: Auto-generated from source code
- **Architecture Docs**: Detailed system design documentation
- **CI/CD Guide**: Complete pipeline documentation
- **Testing Guide**: Comprehensive testing strategy

### Accessing Documentation

- **GitHub Pages**: Deployed automatically on main branch
- **Local Generation**: `make docs && make docs-serve`
- **API Reference**: Available in docs/api/ directory

### Documentation Structure

```
docs/
├── index.rst           # Main documentation index
├── introduction.rst    # Project overview
├── architecture.rst    # System architecture
├── installation.rst    # Installation guide
├── quickstart.rst      # Quick start guide
├── api/                # API documentation
├── testing.rst         # Testing guidelines
├── deployment.rst      # Deployment guide
├── cicd.rst           # CI/CD pipeline documentation
├── troubleshooting.rst # Troubleshooting guide
└── contributing.rst    # Contributing guidelines
```

## 🐳 Docker Images

### Available Images

- **API Server**: `your-dockerhub-username/sonarqube-quality-api`
- **Python Analyzer**: `your-dockerhub-username/sonarqube-python-analyzer`
- **Go Analyzer**: `your-dockerhub-username/sonarqube-go-analyzer`
- **Rust Analyzer**: `your-dockerhub-username/sonarqube-rust-analyzer`

### Docker Features

- **Multi-Platform**: Support for amd64 and arm64 architectures
- **Optimized Caching**: GitHub Actions cache for faster builds
- **Multi-Stage Builds**: Optimized image sizes
- **Security Scanning**: Integrated vulnerability scanning

### Using Docker Images

```bash
# Pull images
docker pull your-dockerhub-username/sonarqube-quality-api:latest
docker pull your-dockerhub-username/sonarqube-python-analyzer:latest

# Run API server
docker run -p 8000:8000 \
  -e SONARQUBE_URL=http://sonarqube:9000 \
  -e SONARQUBE_TOKEN=your-token \
  your-dockerhub-username/sonarqube-quality-api:latest

# Run Python analyzer
docker run -v /path/to/code:/code \
  your-dockerhub-username/sonarqube-python-analyzer:latest /code
```

## 🔒 Security

### Security Features

- **Vulnerability Scanning**: Trivy and Bandit integration
- **Dependency Management**: Regular security updates
- **Code Analysis**: Static analysis for security issues
- **Access Control**: Role-based permissions
- **Data Protection**: Sensitive data redaction

### Security Reports

Security reports are generated:

- **CI/CD Pipeline**: Automated scanning on every build
- **Local Development**: `make security`
- **GitHub Security Tab**: Trivy results uploaded automatically

### Security Best Practices

- **Input Validation**: Comprehensive input sanitization
- **Authentication**: Secure token-based authentication
- **Data Encryption**: Encrypted data storage and transmission
- **Audit Logging**: Comprehensive audit trails

## 📊 Monitoring & Observability

### Performance Monitoring

- **Memory Usage**: Real-time memory monitoring
- **Execution Time**: Performance benchmarking
- **Resource Tracking**: CPU and disk usage monitoring
- **Error Tracking**: Comprehensive error logging

### Metrics Collection

- **Test Performance**: Allure performance metrics
- **Coverage Trends**: Codecov trend analysis
- **Build Performance**: CI/CD pipeline execution time
- **Quality Metrics**: Code quality indicators

## 🤝 Contributing

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Run** `make quality-check` to ensure code quality
5. **Submit** a pull request

### Code Quality Standards

- **Test Coverage**: Minimum 80% coverage required
- **Code Style**: Black and isort formatting
- **Type Hints**: MyPy type checking
- **Security**: Bandit security scanning
- **Documentation**: Comprehensive docstrings

### Pre-commit Hooks

```bash
# Install pre-commit hooks
make pre-commit

# This will run:
# - Code formatting (black, isort)
# - Linting (flake8, mypy)
# - Security scanning (bandit, safety)
# - Test execution
```

## 🛠️ Development Tools

### Make Commands

The project includes a comprehensive Makefile for common tasks:

```bash
make help           # Show all available commands
make setup          # Set up development environment
make test           # Run unit tests
make test-critical  # Run critical tests
make coverage       # Generate coverage report
make allure         # Generate Allure report
make format         # Format code
make lint           # Run linting
make security       # Run security scans
make docs           # Generate documentation
make build          # Build Docker images
make ci-local       # Run full CI/CD pipeline locally
```

### IDE Configuration

For optimal development experience, configure your IDE with:

- **Python**: Python 3.12 interpreter
- **Formatting**: Black and isort
- **Linting**: Flake8 and MyPy
- **Testing**: pytest integration
- **Documentation**: Sphinx integration

## 📈 Performance

### Benchmarks

The system includes performance benchmarks for:

- **Memory Usage**: Large analysis processing
- **Execution Time**: Test execution performance
- **Resource Usage**: CPU and disk consumption
- **Scalability**: Concurrent operation performance

### Performance Optimization

- **Caching**: Intelligent result caching
- **Parallel Processing**: Multi-threaded analysis
- **Resource Management**: Efficient resource utilization
- **Memory Optimization**: Memory leak prevention

## 🔧 Configuration

### Environment Variables

- **PYTHONPATH**: Python path configuration
- **SONARQUBE_URL**: SonarQube server URL
- **SONARQUBE_TOKEN**: SonarQube authentication token
- **DATABASE_URL**: PostgreSQL connection string
- **LOG_LEVEL**: Logging verbosity level

### Configuration Files

- **pytest.ini**: Test configuration
- **allure.yml**: Allure reporting configuration
- **.pre-commit-config.yaml**: Pre-commit hooks
- **Dockerfile**: Container configuration

## 📞 Support

### Troubleshooting

For common issues:

1. **Check the logs**: Review GitHub Actions logs
2. **Run locally**: Use `make ci-local` to reproduce issues
3. **Check dependencies**: Ensure all dependencies are up to date
4. **Review documentation**: Check relevant documentation sections

### Getting Help

- **Documentation**: Comprehensive guides in docs/ directory
- **Issues**: Create GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Security**: Report security issues privately

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **SonarQube**: For the excellent code quality platform
- **pytest**: For the powerful testing framework
- **Allure**: For comprehensive test reporting
- **Docker**: For containerization support
- **GitHub Actions**: For CI/CD automation

---

**Built with ❤️ by the LLM Observability Platform Team**
