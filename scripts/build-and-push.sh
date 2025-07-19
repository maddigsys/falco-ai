#!/bin/bash

# Multi-Architecture Docker Build and Push Script for Falco AI Alert System
# Usage: ./scripts/build-and-push.sh [version] [--push] [--arch]

set -e

# Configuration
DOCKER_REPO="maddigsys"
IMAGE_NAME="falco-ai-alerts"
DEFAULT_VERSION="latest"
DEFAULT_PLATFORMS="linux/amd64,linux/arm64"

# Parse arguments
VERSION=${1:-$DEFAULT_VERSION}
PUSH_IMAGE=${2:-"--push"}
CUSTOM_PLATFORMS=${3:-$DEFAULT_PLATFORMS}

echo "🐳 Multi-Architecture Docker Build and Push Script"
echo "================================================="
echo "Repository: $DOCKER_REPO/$IMAGE_NAME"
echo "Version: $VERSION"
echo "Platforms: $CUSTOM_PLATFORMS"
echo "Push: $PUSH_IMAGE"
echo ""

# Validate version format
if [[ "$VERSION" != "latest" && ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Error: Version must be 'latest' or follow semantic versioning (e.g., v1.0.0)"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if buildx is available
if ! docker buildx version > /dev/null 2>&1; then
    echo "❌ Error: Docker buildx is not available. Please update Docker to a newer version."
    exit 1
fi

# Check if logged into Docker Hub
if ! docker info | grep -q "Username"; then
    echo "⚠️  Warning: Not logged into Docker Hub. Please run 'docker login' first."
    if [[ "$PUSH_IMAGE" == "--push" ]]; then
        echo "❌ Error: Cannot push without being logged in."
        exit 1
    fi
fi

# Create and use a new buildx builder if needed
BUILDER_NAME="falco-multiarch-builder"
if ! docker buildx ls | grep -q "$BUILDER_NAME"; then
    echo "🛠️  Creating multi-architecture builder..."
    docker buildx create --name "$BUILDER_NAME" --driver docker-container --bootstrap
fi

echo "🔧 Using buildx builder: $BUILDER_NAME"
docker buildx use "$BUILDER_NAME"

# Ensure builder is running
docker buildx inspect --bootstrap

# Build the multi-architecture image
echo "🔨 Building multi-architecture Docker image..."
if [[ "$PUSH_IMAGE" == "--push" ]]; then
    # Build and push
    docker buildx build \
        --platform "$CUSTOM_PLATFORMS" \
        --tag "$DOCKER_REPO/$IMAGE_NAME:$VERSION" \
        --push \
        .
    
    # Tag and push as latest if this is a specific version
    if [[ "$VERSION" != "latest" ]]; then
        echo "🏷️  Building and pushing as latest..."
        docker buildx build \
            --platform "$CUSTOM_PLATFORMS" \
            --tag "$DOCKER_REPO/$IMAGE_NAME:latest" \
            --push \
            .
    fi
    
    echo "✅ Successfully built and pushed multi-architecture images!"
    echo ""
    echo "📋 Image URLs (multi-arch manifests):"
    echo "   $DOCKER_REPO/$IMAGE_NAME:$VERSION"
    if [[ "$VERSION" != "latest" ]]; then
        echo "   $DOCKER_REPO/$IMAGE_NAME:latest"
    fi
    echo ""
    echo "🏗️  Supported Architectures:"
    echo "   $(echo $CUSTOM_PLATFORMS | tr ',' '\n' | sed 's/linux\///g' | sed 's/^/   - /')"
    
else
    # Build only (load to local Docker)
    echo "🔨 Building for local testing (amd64 only)..."
    docker buildx build \
        --platform "linux/amd64" \
        --tag "$DOCKER_REPO/$IMAGE_NAME:$VERSION" \
        --load \
        .
    
    # Test the image
    echo "🧪 Testing the image..."
    docker run --rm -d --name test-falco-ai "$DOCKER_REPO/$IMAGE_NAME:$VERSION" &
    TEST_CONTAINER_PID=$!
    
    # Wait for container to start
    sleep 10
    
    # Check if container is running
    if docker ps | grep -q test-falco-ai; then
        echo "✅ Image test successful"
        docker stop test-falco-ai > /dev/null 2>&1 || true
    else
        echo "❌ Image test failed"
        docker stop test-falco-ai > /dev/null 2>&1 || true
        exit 1
    fi
    
    echo "✅ Multi-architecture image built successfully (not pushed)"
    echo ""
    echo "📋 To push manually:"
    echo "   ./scripts/build-and-push.sh $VERSION --push"
fi

echo ""
echo "🎉 Multi-architecture build completed successfully!"
echo ""
echo "🚀 Cloud Deployment Ready:"
echo "   - AMD64: Compatible with standard cloud instances"
echo "   - ARM64: Compatible with AWS Graviton, GCP Tau T2A, Azure Ampere"
echo ""
echo "📖 For Kubernetes deployment, see k8s/README.md"

# Cleanup builder if this was a one-time build
if [[ "$PUSH_IMAGE" != "--push" ]]; then
    echo ""
    echo "🧹 Cleaning up builder..."
    docker buildx rm "$BUILDER_NAME" || true
fi 