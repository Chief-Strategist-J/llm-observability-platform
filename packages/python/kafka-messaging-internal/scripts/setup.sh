#!/bin/bash
# Environment setup script

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Python is available
check_python() {
    log_step "Checking Python installation..."
    
    if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
        log_error "Python is not installed or not in PATH"
        exit 1
    fi
    
    # Set python command
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi
    
    # Check Python version
    local python_version
    python_version=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    log_info "Python version: $python_version"
    
    # Check if version is >= 3.8
    if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        log_error "Python 3.8 or higher is required"
        exit 1
    fi
    
    export PYTHON_CMD
    log_info "Python check passed"
}

# Create virtual environment
create_venv() {
    log_step "Creating virtual environment..."
    
    local venv_path="$PROJECT_ROOT/.venv"
    
    if [[ -d "$venv_path" ]]; then
        log_warn "Virtual environment already exists at $venv_path"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$venv_path"
        else
            log_info "Using existing virtual environment"
            return 0
        fi
    fi
    
    $PYTHON_CMD -m venv "$venv_path"
    log_info "Virtual environment created at $venv_path"
}

# Activate virtual environment
activate_venv() {
    log_step "Activating virtual environment..."
    
    local venv_path="$PROJECT_ROOT/.venv"
    
    if [[ ! -d "$venv_path" ]]; then
        log_error "Virtual environment not found at $venv_path"
        exit 1
    fi
    
    # Activate venv
    source "$venv_path/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    log_info "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    log_step "Installing dependencies..."
    
    cd "$PROJECT_ROOT"
    
    # Install package in development mode
    if pip install -e .; then
        log_info "Package installed successfully"
    else
        log_error "Failed to install package"
        exit 1
    fi
    
    # Install development dependencies
    if pip install -e .[dev]; then
        log_info "Development dependencies installed"
    else
        log_error "Failed to install development dependencies"
        exit 1
    fi
    
    # Install optional dependencies based on environment
    if [[ "${INSTALL_SCHEMA_REGISTRY:-true}" == "true" ]]; then
        if pip install -e .[schema-registry]; then
            log_info "Schema registry dependencies installed"
        else
            log_warn "Failed to install schema registry dependencies"
        fi
    fi
    
    if [[ "${INSTALL_APP_DEPS:-false}" == "true" ]]; then
        if pip install -e .[app]; then
            log_info "Application dependencies installed"
        else
            log_warn "Failed to install application dependencies"
        fi
    fi
    
    log_info "All dependencies installed"
}

# Set up environment file
setup_env_file() {
    log_step "Setting up environment file..."
    
    local env_file="$PROJECT_ROOT/.env"
    local env_example="$PROJECT_ROOT/.env.example"
    
    if [[ -f "$env_file" ]]; then
        log_warn ".env file already exists"
        return 0
    fi
    
    if [[ ! -f "$env_example" ]]; then
        log_error ".env.example file not found"
        exit 1
    fi
    
    # Copy example to .env
    cp "$env_example" "$env_file"
    log_info "Created .env file from .env.example"
    log_warn "Please update .env with your configuration"
}

# Set up pre-commit hooks
setup_precommit() {
    log_step "Setting up pre-commit hooks..."
    
    cd "$PROJECT_ROOT"
    
    # Check if pre-commit is installed
    if ! command -v pre-commit >/dev/null 2>&1; then
        log_warn "pre-commit not found, installing..."
        pip install pre-commit
    fi
    
    # Install pre-commit hooks
    if pre-commit install; then
        log_info "Pre-commit hooks installed"
    else
        log_warn "Failed to install pre-commit hooks"
    fi
}

# Create directories
create_directories() {
    log_step "Creating required directories..."
    
    local directories=(
        "logs"
        "temp"
        "data"
        "reports"
    )
    
    for dir in "${directories[@]}"; do
        local dir_path="$PROJECT_ROOT/$dir"
        if [[ ! -d "$dir_path" ]]; then
            mkdir -p "$dir_path"
            log_info "Created directory: $dir"
        fi
    done
    
    log_info "Required directories created"
}

# Verify installation
verify_installation() {
    log_step "Verifying installation..."
    
    cd "$PROJECT_ROOT"
    
    # Check if package can be imported
    if python -c "import kafka_messaging_internal; print('Package import successful')"; then
        log_info "Package import verification passed"
    else
        log_error "Package import verification failed"
        exit 1
    fi
    
    # Check if main module can be imported
    if python -c "from kafka_messaging_internal.main import main; print('Main module import successful')"; then
        log_info "Main module verification passed"
    else
        log_error "Main module verification failed"
        exit 1
    fi
    
    log_info "Installation verification completed"
}

# Show next steps
show_next_steps() {
    log_info "Setup completed successfully! 🎉"
    echo ""
    echo "Next steps:"
    echo "1. Update .env file with your configuration"
    echo "2. Start your database and schema registry"
    echo "3. Run migrations: ./scripts/migrate.sh"
    echo "4. Start the application: ./scripts/run.sh"
    echo "5. Run tests: ./scripts/test.sh"
    echo ""
    echo "Useful commands:"
    echo "- Activate venv: source .venv/bin/activate"
    echo "- Run app: ./scripts/run.sh"
    echo "- Run tests: ./scripts/test.sh"
    echo "- Migrate DB: ./scripts/migrate.sh"
    echo "- Check status: ./scripts/migrate.sh status"
    echo ""
    echo "Documentation:"
    echo "- API docs: http://localhost:8000/docs (when app is running)"
    echo "- OpenAPI spec: http://localhost:8000/openapi.json"
}

# Main function
main() {
    echo "🚀 Kafka Messaging Internal - Setup Script"
    echo "=========================================="
    echo ""
    
    check_python
    create_venv
    activate_venv
    install_dependencies
    setup_env_file
    setup_precommit
    create_directories
    verify_installation
    show_next_steps
}

# Run main function
main "$@"
