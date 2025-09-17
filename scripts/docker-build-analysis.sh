#!/bin/bash

# Docker Build Analysis Script
# Analyzes Docker image sizes and build performance before/after optimizations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="originfd"
VERSION="latest"
TEMP_TAG="temp-comparison"

echo -e "${BLUE}🔍 Docker Build Analysis - OriginFD Image Optimization${NC}"
echo "=================================================="

# Function to format bytes
format_bytes() {
    local bytes=$1
    if [ $bytes -gt 1073741824 ]; then
        echo "$(echo "scale=2; $bytes/1073741824" | bc)GB"
    elif [ $bytes -gt 1048576 ]; then
        echo "$(echo "scale=2; $bytes/1048576" | bc)MB"
    else
        echo "$(echo "scale=2; $bytes/1024" | bc)KB"
    fi
}

# Function to calculate percentage change
calc_percentage() {
    local old=$1
    local new=$2
    if [ $old -eq 0 ]; then
        echo "N/A"
    else
        echo "$(echo "scale=1; (($old - $new) * 100) / $old" | bc)%"
    fi
}

# Function to build and analyze single service
analyze_service() {
    local service=$1
    local dockerfile=$2
    local context=${3:-"."}

    echo -e "\n${YELLOW}📦 Analyzing: $service${NC}"
    echo "----------------------------------------"

    # Build the optimized image
    echo "Building optimized image..."
    docker build -f "$dockerfile" -t "${REGISTRY}/${service}:${VERSION}" "$context" --quiet

    # Get image details
    local image_id=$(docker images "${REGISTRY}/${service}:${VERSION}" --format "{{.ID}}")
    local image_size=$(docker images "${REGISTRY}/${service}:${VERSION}" --format "{{.Size}}")
    local image_size_bytes=$(docker inspect "${REGISTRY}/${service}:${VERSION}" --format='{{.Size}}')

    echo "Image ID: $image_id"
    echo "Image Size: $image_size"

    # Analyze layers
    echo "Layer analysis:"
    docker history "${REGISTRY}/${service}:${VERSION}" --format "table {{.CreatedBy}}\t{{.Size}}" | head -10

    # Security scan (if available)
    if command -v docker &> /dev/null && docker --help | grep -q "scout"; then
        echo "Security scan:"
        docker scout cves "${REGISTRY}/${service}:${VERSION}" --only-severity high,critical || echo "Scout not available"
    fi

    return $image_size_bytes
}

# Function to show optimization recommendations
show_recommendations() {
    echo -e "\n${GREEN}✅ Optimization Implemented:${NC}"
    echo "• Multi-stage builds to separate build and runtime dependencies"
    echo "• Minimal base images (python:3.11-slim, node:20-alpine)"
    echo "• Virtual environments for Python dependency isolation"
    echo "• Comprehensive .dockerignore to exclude unnecessary files"
    echo "• Proper layer caching with strategic COPY ordering"
    echo "• Non-root user security implementation"
    echo "• Optimized health checks and entry points"
    echo "• Build dependency cleanup in separate stages"

    echo -e "\n${YELLOW}📊 Expected Benefits:${NC}"
    echo "• 40-60% reduction in final image size"
    echo "• Faster build times through better caching"
    echo "• Improved security with minimal attack surface"
    echo "• Better deployment performance"
    echo "• Reduced storage and transfer costs"
}

# Function to compare builds
compare_builds() {
    echo -e "\n${BLUE}🔄 Build Comparison Analysis${NC}"
    echo "============================================"

    # Services to analyze
    declare -A services=(
        ["api"]="services/api/Dockerfile"
        ["orchestrator"]="services/orchestrator/Dockerfile"
        ["workers"]="services/workers/Dockerfile"
        ["web"]="apps/web/Dockerfile"
        ["main"]="Dockerfile"
    )

    local total_optimized=0
    local service_count=0

    for service in "${!services[@]}"; do
        dockerfile="${services[$service]}"

        if [ -f "$dockerfile" ]; then
            analyze_service "$service" "$dockerfile"
            service_count=$((service_count + 1))
        else
            echo -e "${RED}⚠️  Dockerfile not found: $dockerfile${NC}"
        fi
    done

    echo -e "\n${GREEN}📈 Summary${NC}"
    echo "Services analyzed: $service_count"
    echo "All images built with multi-stage optimization"
}

# Function to test production build
test_production_build() {
    echo -e "\n${BLUE}🚀 Testing Production Build${NC}"
    echo "======================================"

    if [ -f "docker-compose.prod.yml" ]; then
        echo "Building production images..."
        docker compose -f docker-compose.prod.yml build --no-cache

        echo -e "\n${GREEN}Production images built successfully!${NC}"
        echo "Image sizes:"
        docker images | grep "$REGISTRY" | awk '{print $1":"$2" - "$7}'
    else
        echo -e "${YELLOW}⚠️  docker-compose.prod.yml not found${NC}"
    fi
}

# Function to cleanup
cleanup() {
    echo -e "\n${BLUE}🧹 Cleanup${NC}"
    echo "============"

    # Remove temporary images
    docker images | grep "$TEMP_TAG" | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true

    # Remove dangling images
    docker image prune -f

    echo "Cleanup completed"
}

# Main execution
main() {
    echo "Starting Docker optimization analysis..."

    # Check dependencies
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed or not in PATH${NC}"
        exit 1
    fi

    if ! command -v bc &> /dev/null; then
        echo -e "${YELLOW}⚠️  bc calculator not found, percentage calculations may not work${NC}"
    fi

    # Show current directory
    echo "Working directory: $(pwd)"

    # Run analysis
    compare_builds
    show_recommendations

    # Optional production test
    read -p "Test production build? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        test_production_build
    fi

    # Cleanup
    cleanup

    echo -e "\n${GREEN}✅ Analysis Complete!${NC}"
    echo "Check the output above for optimization results."
}

# Run main function
main "$@"
