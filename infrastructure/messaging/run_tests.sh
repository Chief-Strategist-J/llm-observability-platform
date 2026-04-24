#!/bin/bash

# Test Execution Script for Messaging Module
# This script runs all unit tests for the messaging module

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "=========================================="
echo "Messaging Module - Test Execution"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run ./setup_env.sh first to create the virtual environment."
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Virtual environment is not activated."
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    echo "Virtual environment activated."
else
    echo "Virtual environment is already activated: $VIRTUAL_ENV"
fi

echo ""
echo "Running tests..."
echo "=========================================="
echo ""

# Set PYTHONPATH to include project root
export PYTHONPATH="$PROJECT_ROOT"

# Run pytest with verbose output
cd "$SCRIPT_DIR"
pytest tests/ -v --tb=short -m "not integration" --maxfail=5

echo ""
echo "=========================================="
echo "Test execution completed!"
echo "=========================================="
echo ""
echo "To view coverage report (if generated):"
echo "  open htmlcov/index.html"
echo ""
