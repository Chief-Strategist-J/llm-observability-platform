.PHONY: help check-tools install test lint format clean fix-all

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install Python dependencies using Poetry"
	@echo "  check-tools  - Verify all development tools are installed and working"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting and code quality checks"
	@echo "  format       - Format code with black and isort"
	@echo "  fix-all      - Auto-fix all linting and formatting issues"
	@echo "  clean        - Clean up cache and build files"
	@echo "  pre-commit   - Install pre-commit hooks"
	@echo "  dev-setup    - Complete development environment setup"

# Install Python dependencies
install:
	poetry install

# Check if all required tools are installed
check-tools:
	@echo "Checking development tools..."
	@command -v python3 >/dev/null 2>&1 || { echo "❌ python3 is not installed"; exit 1; }
	@command -v poetry >/dev/null 2>&1 || { echo "❌ poetry is not installed"; exit 1; }
	@command -v pre-commit >/dev/null 2>&1 || { echo "❌ pre-commit is not installed"; exit 1; }
	@echo "✅ All required tools are installed"

# Run tests
test:
	poetry run pytest

# Run linting and code quality checks
lint:
	poetry run pre-commit run --all-files

# Format code
format:
	poetry run black service/
	poetry run isort service/

# Auto-fix all linting and formatting issues
fix-all: format
	@echo "🔧 Running auto-fixable pre-commit hooks..."
	poetry run pre-commit run --all-files || true
	@echo "✅ Auto-fix complete! Some issues may need manual fixing."

# Clean up cache and build files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Install pre-commit hooks
pre-commit:
	poetry run pre-commit install
	poetry run pre-commit install --hook-type commit-msg

# Complete development environment setup
dev-setup: check-tools pre-commit
	@echo "🚀 Development environment setup complete!"
	@echo "You can now run 'make lint' to check code quality"
	@echo "or 'make test' to run tests"
