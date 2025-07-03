#!/bin/bash

echo "🔍 Checking Ollama Status..."
echo "================================"

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama service is running"
    
    # Get available models
    echo -e "\n📦 Available models:"
    MODELS=$(curl -s http://localhost:11434/api/tags | jq -r '.models[]?.name // empty' 2>/dev/null)
    
    if [ -z "$MODELS" ]; then
        echo "❌ No models downloaded yet"
        echo ""
        echo "🔄 To download the default model, run:"
        echo "curl -X POST http://localhost:11434/api/pull -H 'Content-Type: application/json' -d '{\"name\": \"tinyllama\"}'"
        echo ""
        echo "🔒 Or use cybersecurity model for advanced analysis:"
        echo "curl -X POST http://localhost:11434/api/pull -H 'Content-Type: application/json' -d '{\"name\": \"jimscard/whiterabbit-neo:latest\"}'"
    else
        echo "✅ Downloaded models:"
        echo "$MODELS" | while read -r model; do
            echo "  • $model"
        done
    fi
    
    echo -e "\n🌐 Ollama API accessible at: http://localhost:11434"
    echo "🔗 Web UI AI Config: http://localhost:8080/config/ai"
    
else
    echo "❌ Ollama service is not responding"
    echo "🚀 Try restarting with: docker-compose restart ollama"
fi

echo -e "\n================================" 