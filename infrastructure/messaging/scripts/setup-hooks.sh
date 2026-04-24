#!/bin/bash
set -e

echo "Setting up git hooks..."

# Create .git/hooks directory if it doesn't exist
mkdir -p .git/hooks

# Pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "Running pre-commit checks..."

# Format code
echo "Formatting code with black and isort..."
black infrastructure/
isort infrastructure/

# Run linting
echo "Running linting checks..."
flake8 infrastructure/
mypy infrastructure/

echo "Pre-commit checks passed!"
EOF

# Pre-push hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
echo "Running pre-push checks..."

# Run tests
echo "Running tests..."
pytest tests/ -v --cov=infrastructure/messaging --cov-report=term-missing

echo "Pre-push checks passed!"
EOF

# Make hooks executable
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/pre-push

echo "Git hooks installed successfully!"
echo ""
echo "Pre-commit: Will format code and run linting"
echo "Pre-push: Will run tests"
echo ""
echo "To skip hooks temporarily:"
echo "  git commit --no-verify"
echo "  git push --no-verify"
