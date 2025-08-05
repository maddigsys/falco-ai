#!/bin/bash

# =================================================================
# Falco Vanguard - Local Testing Script
# =================================================================
# This script helps you start and test the system locally

set -e

echo "🚀 Falco Vanguard - Local Testing"
echo "========================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Copy environment template if .env doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp env.example .env
    echo "✅ Created .env file. You can customize it if needed."
fi

echo "🐳 Starting services with Docker Compose..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 15

# Wait for health checks
echo "🔍 Checking service health..."
timeout=60
while [ $timeout -gt 0 ]; do
    if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
        echo "✅ Falco Vanguard is healthy!"
        break
    fi
    echo "⏳ Waiting for service to be ready... ($timeout seconds remaining)"
    sleep 5
    timeout=$((timeout - 5))
done

if [ $timeout -le 0 ]; then
    echo "❌ Service failed to start within 60 seconds"
    echo "📋 Check logs with: docker-compose logs"
    exit 1
fi

# Check Ollama health
if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "✅ Ollama is running!"
else
    echo "⚠️ Ollama may still be starting up..."
fi

echo ""
echo "🎉 System is ready for testing!"
echo ""
echo "📊 Web UI: http://localhost:8080/dashboard"
echo "🤖 AI Config: http://localhost:8080/config/ai"
echo "📢 Slack Config: http://localhost:8080/config/slack"
echo "💾 Database Admin: http://localhost:8081 (run with --profile dev)"
echo ""
echo "🧪 Test the webhook with sample alerts:"
echo "   ./send-test-alert.sh"
echo ""
echo "📋 View logs:"
echo "   docker-compose logs -f falco-ai-alerts"
echo "   docker-compose logs -f ollama"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo "" 