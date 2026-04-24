.PHONY: help install install-dev lint test build publish clean docker-up docker-down docker-logs format check-format setup-hooks

help:
	@echo "Available commands:"
	@echo "  make install          - Install package"
	@echo "  make install-dev      - Install package with dev dependencies"
	@echo "  make lint             - Run all linting checks"
	@echo "  make test             - Run tests"
	@echo "  make build            - Build package"
	@echo "  make publish          - Publish to PyPI (requires PYPI_API_TOKEN)"
	@echo "  make clean            - Clean build artifacts"
	@echo "  make docker-up        - Start Docker services"
	@echo "  make docker-down      - Stop Docker services"
	@echo "  make docker-logs      - Show Docker logs"
	@echo "  make format           - Format code with black and isort"
	@echo "  make check-format     - Check code formatting"
	@echo "  make setup-hooks      - Setup git hooks for local validation"

install:
	pip install -e .

install-dev:
	pip install -e .[dev]

lint:
	./scripts/lint.sh

test:
	./scripts/test.sh

build:
	./scripts/build.sh

publish:
	./scripts/publish.sh

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

format:
	black infrastructure/
	isort infrastructure/

check-format:
	black --check infrastructure/
	isort --check-only infrastructure/

setup-hooks:
	./scripts/setup-hooks.sh
