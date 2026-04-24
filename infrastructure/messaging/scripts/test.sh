#!/bin/bash
set -e

echo "Running tests..."

# Run all tests with coverage
pytest tests/ -v --cov=infrastructure/messaging --cov-report=html --cov-report=term

echo "Tests completed!"
