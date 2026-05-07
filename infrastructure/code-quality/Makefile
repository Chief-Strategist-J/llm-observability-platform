# SonarQube Code Quality Infrastructure - Makefile

.PHONY: help install install-dev test test-critical test-all clean coverage allure docs build docker security format lint

# Default target
help:
	@echo "SonarQube Code Quality Infrastructure - Available Commands:"
	@echo ""
	@echo "Setup Commands:"
	@echo "  install        Install production dependencies"
	@echo "  install-dev    Install development dependencies"
	@echo "  clean          Clean virtual environment and artifacts"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test           Run unit tests"
	@echo "  test-critical  Run critical production-breaking tests"
	@echo "  test-all       Run all tests with coverage"
	@echo "  test-watch     Run tests in watch mode"
	@echo ""
	@echo "Reporting Commands:"
	@echo "  coverage       Generate coverage report"
	@echo "  allure         Generate Allure report"
	@echo "  allure-open    Open Allure report in browser"
	@echo ""
	@echo "Code Quality Commands:"
	@echo "  format         Format code with black and isort"
	@echo "  lint           Run linting with flake8 and mypy"
	@echo "  security       Run security scans with bandit and safety"
	@echo ""
	@echo "Documentation Commands:"
	@echo "  docs           Generate documentation"
	@echo "  docs-serve     Serve documentation locally"
	@echo ""
	@echo "Build Commands:"
	@echo "  build          Build Docker images"
	@echo "  docker         Build and push Docker images"
	@echo ""
	@echo "CI/CD Commands:"
	@echo "  ci-local       Run full CI/CD pipeline locally"

# Setup Commands
install:
	python -m pip install --upgrade pip
	pip install -r deployment/docker/requirements.txt

install-dev:
	python -m pip install --upgrade pip
	pip install -r deployment/docker/requirements.txt
	pip install -r deployment/docker/requirements-dev.txt
	npm install -g allure-commandline

clean:
	rm -rf test_env/
	rm -rf .pytest_cache/
	rm -rf coverage/
	rm -rf allure-results/
	rm -rf allure-report/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .bandit
	rm -rf docs/_build/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Testing Commands
test:
	source test_env/bin/activate && \
	export PYTHONPATH=./infrastructure/code-quality:$$PYTHONPATH && \
	python -m pytest tests/test_domain/ tests/test_application/ -v --tb=short

test-critical:
	source test_env/bin/activate && \
	export PYTHONPATH=./infrastructure/code-quality:$$PYTHONPATH && \
	python -m pytest tests/test_critical/ -v --tb=short

test-all:
	source test_env/bin/activate && \
	export PYTHONPATH=./infrastructure/code-quality:$$PYTHONPATH && \
	python -m pytest tests/ \
		--cov=domain,application,infrastructure,adapters,shared,analysis-tools \
		--cov-report=html \
		--cov-report=xml \
		--cov-report=term-missing \
		--alluredir=allure-results \
		-v --tb=short

test-watch:
	source test_env/bin/activate && \
	export PYTHONPATH=./infrastructure/code-quality:$$PYTHONPATH && \
	python -m pytest tests/ -f --tb=short

# Reporting Commands
coverage:
	source test_env/bin/activate && \
	export PYTHONPATH=./infrastructure/code-quality:$$PYTHONPATH && \
	python -m pytest tests/ \
		--cov=domain,application,infrastructure,adapters,shared,analysis-tools \
		--cov-report=html \
		--cov-report=xml \
		--cov-report=term-missing \
		--cov-fail-under=80
	@echo "Coverage report generated in coverage/index.html"

allure:
	source test_env/bin/activate && \
	export PYTHONPATH=./infrastructure/code-quality:$$PYTHONPATH && \
	python -m pytest tests/ --alluredir=allure-results
	allure generate allure-results --clean -o allure-report
	@echo "Allure report generated in allure-report/index.html"

allure-open:
	allure open allure-report

# Code Quality Commands
format:
	source test_env/bin/activate && \
	black . && \
	isort .

lint:
	source test_env/bin/activate && \
	flake8 . && \
	mypy domain/ application/ infrastructure/ adapters/ shared/

security:
	source test_env/bin/activate && \
	bandit -r . -f json -o bandit-report.json && \
	safety check --json --output safety-report.json
	@echo "Security reports generated"

# Documentation Commands
docs:
	source test_env/bin/activate && \
	cd docs && \
	make html
	@echo "Documentation generated in docs/_build/html/index.html"

docs-serve:
	cd docs/_build/html && \
	python -m http.server 8000

# Build Commands
build:
	docker build -f deployment/docker/Dockerfile.api.optimized -t sonarqube-quality-api:latest .
	docker build -f deployment/docker/Dockerfile.python-analyzer -t sonarqube-python-analyzer:latest .
	docker build -f deployment/docker/Dockerfile.go-analyzer -t sonarqube-go-analyzer:latest .
	docker build -f deployment/docker/Dockerfile.rust-analyzer -t sonarqube-rust-analyzer:latest .

docker: build
	@echo "Push to Docker Hub requires credentials:"
	@echo "docker tag sonarqube-quality-api:latest your-dockerhub-username/sonarqube-quality-api:latest"
	@echo "docker push your-dockerhub-username/sonarqube-quality-api:latest"

# CI/CD Commands
ci-local: clean install-dev test-all coverage allure security
	@echo "Full CI/CD pipeline completed locally"
	@echo "Check coverage report: coverage/index.html"
	@echo "Check Allure report: allure-report/index.html"
	@echo "Check security reports: bandit-report.json, safety-report.json"

# Quick development setup
setup: clean install-dev
	@echo "Development environment setup complete"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make test-critical' to run critical tests"
	@echo "Run 'make coverage' to generate coverage report"
	@echo "Run 'make allure' to generate Allure report"

# Pre-commit setup
pre-commit:
	source test_env/bin/activate && \
	pre-commit install
	@echo "Pre-commit hooks installed"

# Performance testing
perf-test:
	source test_env/bin/activate && \
	export PYTHONPATH=./infrastructure/code-quality:$$PYTHONPATH && \
	python -m pytest tests/test_critical/test_production_breaking.py::TestCriticalProductionScenarios::test_memory_exhaustion_large_analysis \
		--benchmark-only \
		--benchmark-json=performance-results.json \
		--benchmark-html=performance-results.html
	@echo "Performance results generated in performance-results.html"

# Database testing (requires PostgreSQL)
test-db:
	source test_env/bin/activate && \
	export PYTHONPATH=./infrastructure/code-quality:$$PYTHONPATH && \
	export TEST_DB_HOST=localhost && \
	export TEST_DB_USER=postgres && \
	export TEST_DB_PASSWORD=password && \
	export TEST_DB_NAME=test_quality && \
	python -m pytest tests/test_infrastructure/ -v --tb=short

# Integration testing
test-integration:
	source test_env/bin/activate && \
	export PYTHONPATH=./infrastructure/code-quality:$$PYTHONPATH && \
	python -m pytest tests/test_integration/ -v --tb=short || true

# Quick test for development
quick-test:
	source test_env/bin/activate && \
	export PYTHONPATH=./infrastructure/code-quality:$$PYTHONPATH && \
	python -m pytest tests/test_domain/ -v --tb=short -x

# Full quality check
quality-check: format lint security test-all coverage
	@echo "Full quality check completed"
