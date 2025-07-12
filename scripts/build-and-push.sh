#!/bin/bash

# Docker Hub Build and Push Script for Falco AI Alert System
# Usage: ./scripts/build-and-push.sh [version] [--push]

set -e

# Configuration
DOCKER_REPO="maddigsys"
IMAGE_NAME="falco-ai-alerts"
DEFAULT_VERSION="latest"

# Parse arguments
VERSION=${1:-$DEFAULT_VERSION}
PUSH_IMAGE=${2:-"--push"}

echo "🐳 Docker Hub Build and Push Script"
echo "=================================="
echo "Repository: $DOCKER_REPO/$IMAGE_NAME"
echo "Version: $VERSION"
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

# Check if logged into Docker Hub
if ! docker info | grep -q "Username"; then
    echo "⚠️  Warning: Not logged into Docker Hub. Please run 'docker login' first."
    if [[ "$PUSH_IMAGE" == "--push" ]]; then
        echo "❌ Error: Cannot push without being logged in."
        exit 1
    fi
fi

# Build the image
echo "🔨 Building Docker image..."
docker build -t "$DOCKER_REPO/$IMAGE_NAME:$VERSION" .

# Tag as latest if this is a specific version
if [[ "$VERSION" != "latest" ]]; then
    echo "🏷️  Tagging as latest..."
    docker tag "$DOCKER_REPO/$IMAGE_NAME:$VERSION" "$DOCKER_REPO/$IMAGE_NAME:latest"
fi

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

# Push to Docker Hub if requested
if [[ "$PUSH_IMAGE" == "--push" ]]; then
    echo "📤 Pushing to Docker Hub..."
    
    # Push the versioned tag
    docker push "$DOCKER_REPO/$IMAGE_NAME:$VERSION"
    
    # Push latest tag if this is a specific version
    if [[ "$VERSION" != "latest" ]]; then
        docker push "$DOCKER_REPO/$IMAGE_NAME:latest"
    fi
    
    echo "✅ Successfully pushed to Docker Hub!"
    echo ""
    echo "📋 Image URLs:"
    echo "   $DOCKER_REPO/$IMAGE_NAME:$VERSION"
    if [[ "$VERSION" != "latest" ]]; then
        echo "   $DOCKER_REPO/$IMAGE_NAME:latest"
    fi
else
    echo "✅ Image built successfully (not pushed)"
    echo ""
    echo "📋 To push manually:"
    echo "   docker push $DOCKER_REPO/$IMAGE_NAME:$VERSION"
    if [[ "$VERSION" != "latest" ]]; then
        echo "   docker push $DOCKER_REPO/$IMAGE_NAME:latest"
    fi
fi

echo ""
echo "🎉 Build completed successfully!"
echo ""
echo "🚀 To run the image:"
echo "   docker run -d -p 8080:8080 --name falco-ai-alerts $DOCKER_REPO/$IMAGE_NAME:$VERSION"
echo ""
echo "📖 For more information, see the README.md file." 