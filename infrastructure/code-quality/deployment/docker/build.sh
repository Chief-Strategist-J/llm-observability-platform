#!/bin/bash

# Optimized Docker build script with caching
set -e

# Configuration
DOCKER_REGISTRY="${DOCKER_REGISTRY:-localhost:5000}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
BUILDKIT_CACHE="${BUILDKIT_CACHE:-true}"
PARALLEL_BUILDS="${PARALLEL_BUILDS:-true}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if Docker BuildKit is available
setup_buildkit() {
    if [[ "$BUILDKIT_CACHE" == "true" ]]; then
        log_info "Setting up Docker BuildKit with caching..."
        export DOCKER_BUILDKIT=1
        
        # Create buildx builder if it doesn't exist
        if ! docker buildx ls | grep -q "quality-builder"; then
            docker buildx create --name quality-builder --use --bootstrap
        fi
    fi
}

# Build individual service with caching
build_service() {
    local service_name=$1
    local dockerfile=$2
    local context=$3
    local target=${4:-production}
    
    log_info "Building $service_name (target: $target)..."
    
    local cache_args=()
    if [[ "$BUILDKIT_CACHE" == "true" ]]; then
        cache_args=(
            "--cache-from" "type=registry,ref=${DOCKER_REGISTRY}/${service_name}:${IMAGE_TAG}"
            "--cache-to" "type=registry,ref=${DOCKER_REGISTRY}/${service_name}:${IMAGE_TAG},mode=max"
        )
    fi
    
    local build_cmd=(
        docker buildx build
        "--platform" "linux/amd64,linux/arm64"
        "--tag" "${DOCKER_REGISTRY}/${service_name}:${IMAGE_TAG}"
        "--tag" "${service_name}:${IMAGE_TAG}"
        "--target" "$target"
        "${cache_args[@]}"
        "--push"
        "-f" "$dockerfile"
        "$context"
    )
    
    if [[ "$BUILDKIT_CACHE" != "true" ]]; then
        build_cmd=(
            docker build
            "--tag" "${service_name}:${IMAGE_TAG}"
            "--target" "$target"
            "-f" "$dockerfile"
            "$context"
        )
    fi
    
    log_info "Running: ${build_cmd[*]}"
    "${build_cmd[@]}" || {
        log_error "Failed to build $service_name"
        return 1
    }
    
    log_info "Successfully built $service_name"
}

# Build all services in parallel
build_all_services() {
    log_info "Building all services..."
    
    local services=(
        "quality-api:deployment/docker/Dockerfile.api.optimized:../../:production"
        "python-analyzer:deployment/docker/Dockerfile.python-analyzer:../../:production"
        "go-analyzer:deployment/docker/Dockerfile.go-analyzer:../../:production"
        "rust-analyzer:deployment/docker/Dockerfile.rust-analyzer:../../:production"
    )
    
    if [[ "$PARALLEL_BUILDS" == "true" ]]; then
        log_info "Building services in parallel..."
        local pids=()
        
        for service_config in "${services[@]}"; do
            IFS=':' read -r service_name dockerfile context target <<< "$service_config"
            
            (
                build_service "$service_name" "$dockerfile" "$context" "$target"
            ) &
            pids+=($!)
        done
        
        # Wait for all builds to complete
        local failed_builds=0
        for pid in "${pids[@]}"; do
            if ! wait "$pid"; then
                ((failed_builds++))
            fi
        done
        
        if [[ $failed_builds -gt 0 ]]; then
            log_error "$failed_builds builds failed"
            return 1
        fi
    else
        log_info "Building services sequentially..."
        for service_config in "${services[@]}"; do
            IFS=':' read -r service_name dockerfile context target <<< "$service_config"
            build_service "$service_name" "$dockerfile" "$context" "$target"
        done
    fi
    
    log_info "All services built successfully"
}

# Build development images
build_dev_images() {
    log_info "Building development images..."
    
    local dev_services=(
        "quality-api-dev:deployment/docker/Dockerfile.api.optimized:../../:development"
        "python-analyzer-dev:deployment/docker/Dockerfile.python-analyzer:../../:development"
        "go-analyzer-dev:deployment/docker/Dockerfile.go-analyzer:../../:development"
        "rust-analyzer-dev:deployment/docker/Dockerfile.rust-analyzer:../../:development"
    )
    
    for service_config in "${dev_services[@]}"; do
        IFS=':' read -r service_name dockerfile context target <<< "$service_config"
        build_service "$service_name" "$dockerfile" "$context" "$target"
    done
}

# Build test images
build_test_images() {
    log_info "Building test images..."
    
    local test_services=(
        "quality-api-test:deployment/docker/Dockerfile.api.optimized:../../:testing"
        "python-analyzer-test:deployment/docker/Dockerfile.python-analyzer:../../:testing"
        "go-analyzer-test:deployment/docker/Dockerfile.go-analyzer:../../:testing"
        "rust-analyzer-test:deployment/docker/Dockerfile.rust-analyzer:../../:testing"
    )
    
    for service_config in "${test_services[@]}"; do
        IFS=':' read -r service_name dockerfile context target <<< "$service_config"
        build_service "$service_name" "$dockerfile" "$context" "$target"
    done
}

# Clean up build cache
cleanup_cache() {
    log_info "Cleaning up Docker build cache..."
    
    if docker buildx ls | grep -q "quality-builder"; then
        docker buildx rm quality-builder
    fi
    
    docker system prune -f
    docker volume prune -f
    
    log_info "Cache cleanup completed"
}

# Show build information
show_build_info() {
    log_info "Build Configuration:"
    echo "  Docker Registry: $DOCKER_REGISTRY"
    echo "  Image Tag: $IMAGE_TAG"
    echo "  BuildKit Cache: $BUILDKIT_CACHE"
    echo "  Parallel Builds: $PARALLEL_BUILDS"
    echo ""
    
    if [[ "$BUILDKIT_CACHE" == "true" ]]; then
        log_info "BuildKit builders:"
        docker buildx ls
    fi
    
    log_info "Available images:"
    docker images | grep -E "(quality-api|python-analyzer|go-analyzer|rust-analyzer)" || true
}

# Main function
main() {
    local command=${1:-"build"}
    
    case $command in
        "setup")
            setup_buildkit
            ;;
        "build")
            setup_buildkit
            build_all_services
            ;;
        "dev")
            setup_buildkit
            build_dev_images
            ;;
        "test")
            setup_buildkit
            build_test_images
            ;;
        "all")
            setup_buildkit
            build_all_services
            build_dev_images
            build_test_images
            ;;
        "clean")
            cleanup_cache
            ;;
        "info")
            show_build_info
            ;;
        *)
            echo "Usage: $0 {setup|build|dev|test|all|clean|info}"
            echo ""
            echo "Commands:"
            echo "  setup   - Set up Docker BuildKit"
            echo "  build   - Build production images"
            echo "  dev     - Build development images"
            echo "  test    - Build test images"
            echo "  all     - Build all image types"
            echo "  clean   - Clean up build cache"
            echo "  info    - Show build information"
            echo ""
            echo "Environment variables:"
            echo "  DOCKER_REGISTRY    - Docker registry URL (default: localhost:5000)"
            echo "  IMAGE_TAG          - Image tag (default: latest)"
            echo "  BUILDKIT_CACHE     - Enable BuildKit caching (default: true)"
            echo "  PARALLEL_BUILDS    - Build in parallel (default: true)"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
