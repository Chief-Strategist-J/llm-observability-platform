#!/bin/bash
set -e

echo "Running lint checks..."

# Black
echo "Running black..."
black --check infrastructure/

# isort
echo "Running isort..."
isort --check-only infrastructure/

# flake8
echo "Running flake8..."
flake8 infrastructure/

# mypy
echo "Running mypy..."
mypy infrastructure/

# bandit
echo "Running bandit..."
bandit -r infrastructure/

echo "All lint checks passed!"
