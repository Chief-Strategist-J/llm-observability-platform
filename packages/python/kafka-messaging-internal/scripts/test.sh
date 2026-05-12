#!/bin/bash
# Test runner script

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

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

# Check if test dependencies are available
check_dependencies() {
    log_info "Checking test dependencies..."
    
    local missing_deps=()
    
    if ! command -v python >/dev/null 2>&1; then
        missing_deps+=("python")
    fi
    
    if ! python -c "import pytest" >/dev/null 2>&1; then
        missing_deps+=("pytest")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing test dependencies: ${missing_deps[*]}"
        log_info "Install with: pip install -e .[dev]"
        exit 1
    fi
    
    log_info "Test dependencies verified"
}

# Set up test environment
setup_test_env() {
    log_info "Setting up test environment..."
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Set PYTHONPATH
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    
    # Set test environment variables
    export DEPLOYMENT_ENV=test
    export TEST_DATABASE_URL="${TEST_DATABASE_URL:-postgresql://test:test@localhost:5432/kafka_events_test}"
    export TEST_SCHEMA_REGISTRY_URL="${TEST_SCHEMA_REGISTRY_URL:-http://localhost:8081}"
    export TEST_KAFKA_BOOTSTRAP_SERVERS="${TEST_KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"
    
    log_info "Test environment configured"
}

# Run unit tests
run_unit_tests() {
    log_test "Running unit tests..."
    
    cd "$PROJECT_ROOT"
    
    if python -m pytest tests/unit -v --cov=src --cov-report=term-missing --cov-report=html; then
        log_info "Unit tests passed"
        return 0
    else
        log_error "Unit tests failed"
        return 1
    fi
}

# Run integration tests
run_integration_tests() {
    log_test "Running integration tests..."
    
    cd "$PROJECT_ROOT"
    
    if python -m pytest tests/integration -v --cov=src --cov-report=term-missing --cov-report=html; then
        log_info "Integration tests passed"
        return 0
    else
        log_error "Integration tests failed"
        return 1
    fi
}

# Run contract tests
run_contract_tests() {
    log_test "Running contract tests..."
    
    cd "$PROJECT_ROOT"
    
    # Start application in background for contract testing
    log_info "Starting application for contract testing..."
    python -m uvicorn kafka_messaging_internal.main:main \
        --host 127.0.0.1 --port 8001 --log-level error &
    local app_pid=$!
    
    # Wait for application to start
    sleep 5
    
    # Run contract tests
    local test_result=0
    if python -m pytest tests/contract -v; then
        log_info "Contract tests passed"
    else
        log_error "Contract tests failed"
        test_result=1
    fi
    
    # Stop application
    kill $app_pid 2>/dev/null || true
    wait $app_pid 2>/dev/null || true
    
    return $test_result
}

# Run e2e tests
run_e2e_tests() {
    log_test "Running end-to-end tests..."
    
    cd "$PROJECT_ROOT"
    
    if python -m pytest tests/e2e -v --timeout=300; then
        log_info "E2E tests passed"
        return 0
    else
        log_error "E2E tests failed"
        return 1
    fi
}

# Run performance tests
run_performance_tests() {
    log_test "Running performance tests..."
    
    cd "$PROJECT_ROOT"
    
    if python -m pytest tests/performance -v --benchmark-only; then
        log_info "Performance tests passed"
        return 0
    else
        log_error "Performance tests failed"
        return 1
    fi
}

# Run all tests
run_all_tests() {
    log_info "Running all tests..."
    
    local failed_tests=()
    
    # Run unit tests
    if ! run_unit_tests; then
        failed_tests+=("unit")
    fi
    
    # Run integration tests
    if ! run_integration_tests; then
        failed_tests+=("integration")
    fi
    
    # Run contract tests
    if ! run_contract_tests; then
        failed_tests+=("contract")
    fi
    
    # Run E2E tests (optional - requires full environment)
    if [[ "${RUN_E2E_TESTS:-false}" == "true" ]]; then
        if ! run_e2e_tests; then
            failed_tests+=("e2e")
        fi
    fi
    
    # Run performance tests (optional)
    if [[ "${RUN_PERFORMANCE_TESTS:-false}" == "true" ]]; then
        if ! run_performance_tests; then
            failed_tests+=("performance")
        fi
    fi
    
    # Report results
    if [[ ${#failed_tests[@]} -eq 0 ]]; then
        log_info "All tests passed! 🎉"
        return 0
    else
        log_error "Failed test suites: ${failed_tests[*]}"
        return 1
    fi
}

# Generate test coverage report
generate_coverage() {
    log_info "Generating coverage report..."
    
    cd "$PROJECT_ROOT"
    
    # Run tests with coverage
    python -m pytest tests/unit tests/integration --cov=src --cov-report=html --cov-report=xml
    
    # Check coverage threshold
    local coverage
    coverage=$(python -c "
import coverage
cov = coverage.Coverage()
cov.load()
print(int(cov.report()))
")
    
    log_info "Coverage: ${coverage}%"
    
    if [[ $coverage -lt 80 ]]; then
        log_warn "Coverage below 80% threshold"
        return 1
    else
        log_info "Coverage meets 80% threshold"
        return 0
    fi
}

# Main function
main() {
    case "${1:-all}" in
        "unit")
            check_dependencies
            setup_test_env
            run_unit_tests
            ;;
        "integration")
            check_dependencies
            setup_test_env
            run_integration_tests
            ;;
        "contract")
            check_dependencies
            setup_test_env
            run_contract_tests
            ;;
        "e2e")
            check_dependencies
            setup_test_env
            run_e2e_tests
            ;;
        "performance")
            check_dependencies
            setup_test_env
            run_performance_tests
            ;;
        "all")
            check_dependencies
            setup_test_env
            run_all_tests
            ;;
        "coverage")
            check_dependencies
            setup_test_env
            generate_coverage
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [unit|integration|contract|e2e|performance|all|coverage|help]"
            echo ""
            echo "Commands:"
            echo "  unit        - Run unit tests only"
            echo "  integration - Run integration tests only"
            echo "  contract    - Run contract tests only"
            echo "  e2e         - Run end-to-end tests only (requires full environment)"
            echo "  performance - Run performance tests only"
            echo "  all         - Run all tests (default)"
            echo "  coverage    - Generate coverage report"
            echo "  help        - Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  RUN_E2E_TESTS=true          - Enable E2E tests in 'all' mode"
            echo "  RUN_PERFORMANCE_TESTS=true   - Enable performance tests in 'all' mode"
            ;;
        *)
            log_error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
