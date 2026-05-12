#!/bin/bash
# Validation script to verify architectural rules compliance

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

# Validation results
VALIDATION_PASSED=true
VIOLATIONS=()

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    log_validation_issue "$1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    log_validation_issue "$1"
}

log_validation() {
    echo -e "${BLUE}[VALIDATE]${NC} $1"
}

log_validation_issue() {
    VALIDATION_PASSED=false
    VIOLATIONS+=("$1")
}

# Check if required files exist
check_required_files() {
    log_validation "Checking required files..."
    
    local required_files=(
        "contracts/openapi/v1.yaml"
        "src/infra/ports/database_port.py"
        "src/infra/ports/schema_registry_port.py"
        "src/features/event-processing/index.py"
        "src/features/schema-registry/index.py"
        "src/features/database-operations/index.py"
        "src/api/rest/v1/router.py"
        "src/infra/tracing/tracer.py"
        "database/migrations/0001_init.sql"
        "database/schema.lock"
        "pyproject.toml"
        ".env.example"
        "coupling-map.md"
        ".port-registry"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$PROJECT_ROOT/$file" ]]; then
            log_error "Required file missing: $file"
        else
            log_info "Required file exists: $file"
        fi
    done
}

# Validate package isolation (no cross-package imports)
validate_isolation() {
    log_validation "Validating package isolation..."
    
    # Check for imports from other packages
    local forbidden_patterns=(
        "from infrastructure.messaging"
        "import infrastructure.messaging"
        "from llm_messaging_sdk"
        "import llm_messaging_sdk"
    )
    
    for pattern in "${forbidden_patterns[@]}"; do
        if grep -r "$pattern" "$PROJECT_ROOT/src" --include="*.py" 2>/dev/null; then
            log_error "Forbidden import pattern found: $pattern"
        else
            log_info "No forbidden imports found for pattern: $pattern"
        fi
    done
}

# Validate layer call rules
validate_layer_call_rules() {
    log_validation "Validating layer call rules..."
    
    # API should only call feature/index
    local api_files=("$PROJECT_ROOT/src/api" -name "*.py" -type f)
    
    while IFS= read -r -d '' api_file; do
        # Check for direct feature service imports
        if grep -E "from.*features.*\.service|from.*features.*\.repository" "$api_file" 2>/dev/null; then
            log_error "API file imports service/repository directly: $(basename "$api_file")"
        fi
        
        # Check for direct infrastructure imports
        if grep -E "from.*infra|import.*infra" "$api_file" 2>/dev/null; then
            log_error "API file imports infrastructure directly: $(basename "$api_file")"
        fi
    done < <(find "$PROJECT_ROOT/src/api" -name "*.py" -type f -print0)
    
    # Features should only use ports for infrastructure
    local service_files=($(find "$PROJECT_ROOT/src/features" -name "*service.py" -type f))
    
    for service_file in "${service_files[@]}"; do
        if grep -E "from.*infra\.adapters\.|import.*infra\.adapters\." "$service_file" 2>/dev/null; then
            log_error "Service file imports adapter directly: $(basename "$service_file")"
        fi
    done
}

# Validate port interface compliance
validate_port_interfaces() {
    log_validation "Validating port interface compliance..."
    
    local port_files=(
        "src/infra/ports/database_port.py"
        "src/infra/ports/schema_registry_port.py"
    )
    
    for port_file in "${port_files[@]}"; do
        local full_path="$PROJECT_ROOT/$port_file"
        if [[ -f "$full_path" ]]; then
            # Check if port file contains ABC and abstract methods
            if ! grep -q "ABC" "$full_path"; then
                log_error "Port file missing ABC: $port_file"
            fi
            
            if ! grep -q "@abstractmethod" "$full_path"; then
                log_error "Port file missing abstract methods: $port_file"
            fi
            
            log_info "Port interface valid: $port_file"
        else
            log_error "Port file missing: $port_file"
        fi
    done
}

# Validate tracing implementation
validate_tracing() {
    log_validation "Validating tracing implementation..."
    
    # Check if tracer.py exists and has required attributes
    local tracer_file="$PROJECT_ROOT/src/infra/tracing/tracer.py"
    if [[ -f "$tracer_file" ]]; then
        # Check for required tracing attributes
        local required_attrs=(
            "service.name"
            "service.version"
            "deployment.env"
            "host.name"
            "feature.name"
            "api.version"
        )
        
        for attr in "${required_attrs[@]}"; do
            if grep -q "$attr" "$tracer_file"; then
                log_info "Tracing attribute found: $attr"
            else
                log_error "Tracing attribute missing: $attr"
            fi
        done
    else
        log_error "Tracer file missing: src/infra/tracing/tracer.py"
    fi
    
    # Check if middleware exists
    local middleware_file="$PROJECT_ROOT/src/infra/tracing/middleware.py"
    if [[ -f "$middleware_file" ]]; then
        log_info "Tracing middleware exists"
    else
        log_error "Tracing middleware missing: src/infra/tracing/middleware.py"
    fi
}

# Validate migration structure
validate_migrations() {
    log_validation "Validating migration structure..."
    
    # Check for migration files
    local migration_dir="$PROJECT_ROOT/database/migrations"
    if [[ -d "$migration_dir" ]]; then
        # Check for migration files
        local migration_files=($(find "$migration_dir" -name "*.sql" ! -name "*.rollback.sql"))
        local has_migration=false
        
        for file in "${migration_files[@]}"; do
            if [[ -f "$file" ]]; then
                has_migration=true
                log_info "Migration file found: $(basename "$file")"
                
                # Check for corresponding rollback file
                local base_name=$(basename "$file" .sql)
                local rollback_file="$migration_dir/${base_name}.rollback.sql"
                if [[ -f "$rollback_file" ]]; then
                    log_info "Rollback file found: ${base_name}.rollback.sql"
                else
                    log_error "Rollback file missing: ${base_name}.rollback.sql"
                fi
            fi
        done
        
        if [[ "$has_migration" == "false" ]]; then
            log_error "No migration files found"
        fi
    else
        log_error "Migration directory missing: database/migrations"
    fi
    
    # Check for schema.lock
    local schema_lock="$PROJECT_ROOT/database/schema.lock"
    if [[ -f "$schema_lock" ]]; then
        log_info "Schema lock file exists"
    else
        log_error "Schema lock file missing: database/schema.lock"
    fi
}

# Validate test structure
validate_test_structure() {
    log_validation "Validating test structure..."
    
    local test_dirs=(
        "tests/unit"
        "tests/integration"
        "tests/contract"
        "tests/e2e"
        "tests/performance"
    )
    
    for test_dir in "${test_dirs[@]}"; do
        local full_path="$PROJECT_ROOT/$test_dir"
        if [[ -d "$full_path" ]]; then
            # Check for test files
            local test_files=("$full_path"/*.py)
            local has_tests=false
            
            for file in $test_files; do
                if [[ -f "$file" ]]; then
                    has_tests=true
                    log_info "Test file found in $test_dir: $(basename "$file")"
                fi
            done
            
            if [[ "$has_tests" == "false" ]]; then
                log_warn "No test files found in $test_dir"
            fi
        else
            log_error "Test directory missing: $test_dir"
        fi
    done
    
    # Check for conftest.py
    local conftest_file="$PROJECT_ROOT/tests/conftest.py"
    if [[ -f "$conftest_file" ]]; then
        log_info "conftest.py exists"
    else
        log_error "conftest.py missing: tests/conftest.py"
    fi
}

# Validate script structure
validate_script_structure() {
    log_validation "Validating script structure..."
    
    local required_scripts=(
        "scripts/setup.sh"
        "scripts/run.sh"
        "scripts/test.sh"
        "scripts/migrate.sh"
    )
    
    for script in "${required_scripts[@]}"; do
        local full_path="$PROJECT_ROOT/$script"
        if [[ -f "$full_path" ]]; then
            # Check if script is executable
            if [[ -x "$full_path" ]]; then
                log_info "Script exists and executable: $script"
            else
                log_error "Script exists but not executable: $script"
            fi
        else
            log_error "Script missing: $script"
        fi
    done
}

# Validate OpenAPI contract
validate_openapi_contract() {
    log_validation "Validating OpenAPI contract..."
    
    local contract_file="$PROJECT_ROOT/contracts/openapi/v1.yaml"
    if [[ -f "$contract_file" ]]; then
        # Check for required OpenAPI elements
        local required_elements=(
            "openapi:"
            "info:"
            "paths:"
            "components:"
        )
        
        for element in "${required_elements[@]}"; do
            if grep -q "$element" "$contract_file"; then
                log_info "OpenAPI element found: $element"
            else
                log_error "OpenAPI element missing: $element"
            fi
        done
        
        # Check for version
        if grep -q "version:" "$contract_file"; then
            log_info "OpenAPI version specified"
        else
            log_error "OpenAPI version missing"
        fi
    else
        log_error "OpenAPI contract missing: contracts/openapi/v1.yaml"
    fi
}

# Validate coupling map
validate_coupling_map() {
    log_validation "Validating coupling map..."
    
    local coupling_file="$PROJECT_ROOT/coupling-map.md"
    if [[ -f "$coupling_file" ]]; then
        # Check for required sections
        local required_sections=(
            "Package Isolation Status"
            "Internal Coupling Analysis"
            "Post-Migration Target State"
        )
        
        for section in "${required_sections[@]}"; do
            if grep -q "$section" "$coupling_file"; then
                log_info "Coupling map section found: $section"
            else
                log_error "Coupling map section missing: $section"
            fi
        done
    else
        log_error "Coupling map missing: coupling-map.md"
    fi
}

# Validate port registry
validate_port_registry() {
    log_validation "Validating port registry..."
    
    local registry_file="$PROJECT_ROOT/.port-registry"
    if [[ -f "$registry_file" ]]; then
        # Check for port interface documentation
        local required_ports=(
            "DatabasePort"
            "SchemaRegistryPort"
        )
        
        for port in "${required_ports[@]}"; do
            if grep -q "$port" "$registry_file"; then
                log_info "Port registry entry found: $port"
            else
                log_error "Port registry entry missing: $port"
            fi
        done
    else
        log_error "Port registry missing: .port-registry"
    fi
}

# Main validation function
main() {
    echo "🔍 Kafka Messaging Internal - Validation Script"
    echo "==============================================="
    echo ""
    
    # Run all validations
    check_required_files
    validate_isolation
    validate_layer_call_rules
    validate_port_interfaces
    validate_tracing
    validate_migrations
    validate_test_structure
    validate_script_structure
    validate_openapi_contract
    validate_coupling_map
    validate_port_registry
    
    echo ""
    echo "==============================================="
    echo "Validation Results:"
    echo "==============================================="
    
    if [[ "$VALIDATION_PASSED" == "true" ]]; then
        echo -e "${GREEN}✅ All validations passed!${NC}"
        echo ""
        echo "The package is fully compliant with architectural rules:"
        echo "- Package isolation: ✅"
        echo "- Layer call rules: ✅"
        echo "- Port interface compliance: ✅"
        echo "- Tracing implementation: ✅"
        echo "- Migration structure: ✅"
        echo "- Test structure: ✅"
        echo "- Script structure: ✅"
        echo "- OpenAPI contract: ✅"
        echo "- Coupling documentation: ✅"
        echo "- Port registry: ✅"
        return 0
    else
        echo -e "${RED}❌ Validation failed with ${#VIOLATIONS[@]} issues:${NC}"
        echo ""
        for violation in "${VIOLATIONS[@]}"; do
            echo -e "${RED}  - $violation${NC}"
        done
        echo ""
        echo "Please fix these issues before proceeding with deployment."
        return 1
    fi
}

# Run main function with all arguments
main "$@"
