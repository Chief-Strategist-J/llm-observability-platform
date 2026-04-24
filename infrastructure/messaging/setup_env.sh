#!/bin/bash

# Virtual Environment Setup Script for Messaging Module
# This script creates a Python virtual environment and installs dependencies
# Usage: ./setup_env.sh [options]
# Options:
#   --full          Install all dependencies including optional ones
#   --schema-registry Install schema registry dependencies
#   --app           Install application dependencies (temporalio, fastapi)
#   --core          Install only core dependencies (default)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
REQUIREMENTS_SCHEMA_REGISTRY="$SCRIPT_DIR/requirements-schema-registry.txt"
REQUIREMENTS_APP="$SCRIPT_DIR/requirements-app.txt"

INSTALL_FULL=false
INSTALL_SCHEMA_REGISTRY=false
INSTALL_APP=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            INSTALL_FULL=true
            shift
            ;;
        --schema-registry)
            INSTALL_SCHEMA_REGISTRY=true
            shift
            ;;
        --app)
            INSTALL_APP=true
            shift
            ;;
        --core)
            # Default, do nothing
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--full|--schema-registry|--app|--core]"
            exit 1
            ;;
    esac
done

if [ "$INSTALL_FULL" = true ]; then
    INSTALL_SCHEMA_REGISTRY=true
    INSTALL_APP=true
fi

echo "=========================================="
echo "Messaging Module - Environment Setup"
echo "=========================================="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created successfully."
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install core dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing core dependencies from requirements.txt..."
    pip install -r "$REQUIREMENTS_FILE"
    echo "Core dependencies installed successfully."
else
    echo "Warning: requirements.txt not found at $REQUIREMENTS_FILE"
fi

# Install schema registry dependencies if requested
if [ "$INSTALL_SCHEMA_REGISTRY" = true ] && [ -f "$REQUIREMENTS_SCHEMA_REGISTRY" ]; then
    echo "Installing schema registry dependencies..."
    pip install -r "$REQUIREMENTS_SCHEMA_REGISTRY"
    echo "Schema registry dependencies installed successfully."
fi

# Install application dependencies if requested
if [ "$INSTALL_APP" = true ] && [ -f "$REQUIREMENTS_APP" ]; then
    echo "Installing application dependencies..."
    pip install -r "$REQUIREMENTS_APP"
    echo "Application dependencies installed successfully."
fi

echo ""
echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "To activate the virtual environment, run:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "To deactivate the virtual environment, run:"
echo "  deactivate"
echo ""
echo "To install optional dependencies later:"
echo "  pip install -r requirements-schema-registry.txt  # For schema registry tests"
echo "  pip install -r requirements-app.txt            # For temporalio/fastapi tests"
echo ""
