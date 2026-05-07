CI/CD Pipeline
==============

The SonarQube Code Quality Infrastructure includes a comprehensive CI/CD pipeline that ensures code quality, security, and reliability on every change.

Pipeline Overview
----------------

The CI/CD pipeline is triggered on:

* **Push to main/develop**: Full pipeline execution
* **Pull Requests**: Test execution and reporting
* **Code changes in code-quality package**: Package-specific execution

Pipeline Jobs
-------------

1. **Test and Report**: Run tests with coverage and Allure reporting
2. **Docker Build**: Build and push container images
3. **Security Scan**: Vulnerability scanning with Trivy and Bandit
4. **Documentation**: Generate and deploy API documentation
5. **Performance Test**: Run performance benchmarks
6. **Quality Gate**: Final quality check
7. **Notify**: Send notifications to Slack

Test Reporting
--------------

Coverage Reports
~~~~~~~~~~~~~~~

Coverage is generated for all test suites:

* **Domain Tests**: Core business logic coverage
* **Application Tests**: Use case coverage
* **Critical Tests**: Production scenario coverage
* **Combined Coverage**: Overall project coverage

Coverage reports are uploaded to:

* **Codecov**: For trend analysis and PR comments
* **GitHub Artifacts**: For download and review
* **Quality Gate**: Minimum 80% coverage required

Allure Reports
~~~~~~~~~~~~~~

Allure provides comprehensive test reporting with:

* **Test Categories**: Grouped by severity and type
* **Detailed Results**: Step-by-step test execution
* **Performance Metrics**: Execution time and memory usage
* **History Tracking**: Test result trends over time

Report Access
~~~~~~~~~~~~~~~

* **Pull Requests**: Allure reports posted as comments
* **Main Branch**: Reports deployed to GitHub Pages
* **Artifacts**: Available for download from GitHub Actions

Security Scanning
-----------------

Trivy Security Scan
~~~~~~~~~~~~~~~~~~~

* **Container Scanning**: Docker image vulnerability scanning
* **File System Scanning**: Source code vulnerability detection
* **Dependency Scanning**: Third-party package vulnerabilities
* **Results**: Uploaded to GitHub Security tab

Bandit Security Scan
~~~~~~~~~~~~~~~~~~~~

* **Python Security**: Code-level security issues
* **Common Vulnerabilities**: OWASP top 10 detection
* **Best Practices**: Security coding standards
* **Reports**: Available as artifacts

Docker Builds
-------------

Multi-Platform Images
~~~~~~~~~~~~~~~~~~~~~

All Docker images are built for:

* **linux/amd64**: Standard x86_64 architecture
* **linux/arm64**: ARM 64-bit architecture
* **Caching**: GitHub Actions cache for faster builds
* **Optimization**: Multi-stage builds with proper layering

Image Registry
~~~~~~~~~~~~~~

Images are pushed to Docker Hub with tags:

* **Latest**: `your-dockerhub-username/sonarqube-quality-api:latest`
* **Commit SHA**: `your-dockerhub-username/sonarqube-quality-api:{sha}`
* **Version**: `your-dockerhub-username/sonarqube-quality-api:v1.0.0`

Available Images:

* **API Server**: Main application server
* **Python Analyzer**: Python code analysis tool
* **Go Analyzer**: Go infrastructure analysis tool
* **Rust Analyzer**: Rust performance analysis tool

Quality Gates
-------------

The pipeline enforces strict quality gates:

Test Requirements
~~~~~~~~~~~~~~~~

* **All Tests Must Pass**: No test failures allowed
* **Coverage Threshold**: Minimum 80% code coverage
* **Critical Tests**: All production-breaking tests must pass

Security Requirements
~~~~~~~~~~~~~~~~~~~~

* **No Critical Vulnerabilities**: Trivy must pass
* **Security Scan**: Bandit must pass or have acceptable issues
* **Dependencies**: No known vulnerable dependencies

Performance Requirements
~~~~~~~~~~~~~~~~~~~~~~~~

* **Memory Usage**: Tests must not exceed memory limits
* **Execution Time**: Tests must complete within time limits
* **Performance Benchmarks**: Must meet minimum performance criteria

Environment Variables
----------------------

Required Secrets
~~~~~~~~~~~~~~~~

* **DOCKER_USERNAME**: Docker Hub username
* **DOCKER_PASSWORD**: Docker Hub password/token
* **SLACK_WEBHOOK_URL**: Slack notification webhook
* **GITHUB_TOKEN**: GitHub API token (automatically provided)

Optional Configuration
~~~~~~~~~~~~~~~~~~~~~~

* **PYTHON_VERSION**: Python version (default: 3.12)
* **NODE_VERSION**: Node.js version (default: 18)
* **COVERAGE_THRESHOLD**: Minimum coverage percentage (default: 80)

Pipeline Configuration
----------------------

GitHub Actions Workflow
~~~~~~~~~~~~~~~~~~~~~~~

The pipeline is defined in ``.github/workflows/ci-cd.yml`` with:

* **Path Filtering**: Only runs on code-quality package changes
* **Conditional Execution**: Different steps for PRs vs. main branch
* **Parallel Execution**: Jobs run in parallel where possible
* **Dependency Management**: Proper job dependencies

Trigger Conditions
~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

    on:
      push:
        branches: [ main, develop ]
        paths:
          - 'infrastructure/code-quality/**'
      pull_request:
        branches: [ main, develop ]
        paths:
          - 'infrastructure/code-quality/**'

Local Development
-----------------

Running Tests Locally
~~~~~~~~~~~~~~~~~~~~~

To run the same test suite locally:

.. code-block:: bash

    # Setup environment
    cd infrastructure/code-quality
    python -m venv test_env
    source test_env/bin/activate
    pip install -r deployment/docker/requirements-dev.txt

    # Run tests with coverage and Allure
    export PYTHONPATH=./infrastructure/code-quality:$PYTHONPATH
    python -m pytest tests/ \
        --cov=domain,application,infrastructure,adapters,shared \
        --cov-report=html \
        --alluredir=allure-results \
        -v

    # Generate Allure report
    allure generate allure-results --clean -o allure-report
    allure open allure-report

Coverage Reports
~~~~~~~~~~~~~~~~

Generate coverage reports locally:

.. code-block:: bash

    # Run tests with coverage
    python -m pytest tests/ --cov=domain,application,infrastructure,adapters,shared --cov-report=html

    # View coverage report
    open coverage/index.html

Allure Reports
~~~~~~~~~~~~~~

Generate Allure reports locally:

.. code-block:: bash

    # Install Allure CLI
    npm install -g allure-commandline

    # Run tests with Allure
    python -m pytest tests/ --alluredir=allure-results

    # Generate and view report
    allure generate allure-results --clean -o allure-report
    allure open allure-report

Security Scanning
~~~~~~~~~~~~~~~~

Run security scans locally:

.. code-block:: bash

    # Bandit security scan
    bandit -r . -f json -o bandit-report.json

    # Trivy security scan (requires Docker)
    trivy fs --format json -o trivy-report.json .

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~~

**Test Failures**
    * Check test logs in GitHub Actions
    * Run tests locally with same Python version
    * Verify dependencies are up to date

**Coverage Issues**
    * Ensure new code has tests
    * Check coverage exclusions in pytest.ini
    * Verify coverage calculation includes all modules

**Allure Issues**
    * Check allure-results directory permissions
    * Verify Allure CLI installation
    * Check test annotations and markers

**Docker Build Issues**
    * Verify Docker Hub credentials
    * Check Dockerfile syntax and dependencies
    * Review build logs for specific errors

**Security Scan Issues**
    * Review vulnerability reports
    * Update dependencies to fix vulnerabilities
    - Add exceptions for acceptable security issues

Performance Issues
~~~~~~~~~~~~~~~~~~

* **Memory Usage**: Monitor test memory consumption
* **Execution Time**: Optimize slow tests
* **Resource Limits**: Adjust GitHub Actions resource allocation

Best Practices
--------------

Code Quality
~~~~~~~~~~~

* **Write Tests**: Ensure comprehensive test coverage
* **Follow Standards**: Use established coding standards
* **Security First**: Consider security implications
* **Performance**: Monitor resource usage

Pipeline Maintenance
~~~~~~~~~~~~~~~~~~~~

* **Regular Updates**: Keep dependencies updated
* **Monitor Performance**: Track pipeline execution time
* **Review Reports**: Regularly review test and coverage reports
* **Security**: Address security vulnerabilities promptly

Documentation
~~~~~~~~~~~~~

* **Keep Updated**: Update documentation with changes
* **Include Examples**: Provide clear usage examples
* **Troubleshooting**: Maintain troubleshooting guide
* **API Docs**: Keep API documentation current

Additional Resources
--------------------

* `GitHub Actions Documentation <https://docs.github.com/en/actions>`_
* `Codecov Documentation <https://docs.codecov.com/>`_
* `Allure Reporting <https://docs.qameta.io/allure/>`_
* `Docker Security Scanning <https://docs.docker.com/docker-hub/security-scanning/>`_
