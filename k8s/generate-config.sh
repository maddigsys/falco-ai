#!/bin/bash

# Dynamic Kubernetes Configuration Generator
# Generates platform-specific configurations based on detected environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/detect-platform.sh"

# Get platform info
PLATFORM=$(detect_platform)
STORAGE_CLASS=$(get_storage_class "$PLATFORM")
RESOURCES=$(get_node_resources "$PLATFORM")

# Parse resources
eval "$RESOURCES"

echo "🚀 Generating configuration for platform: $PLATFORM"
echo "📦 Storage class: $STORAGE_CLASS"
echo "🔧 Resources: $RESOURCES"

# Generate dynamic PVC configuration
generate_pvc_patch() {
    cat <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: weaviate-pvc
  labels:
    app: weaviate
    platform: $PLATFORM
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: $STORAGE_CLASS
EOF
}

# Generate dynamic deployment patch
generate_deployment_patch() {
    cat <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: weaviate
  labels:
    platform: $PLATFORM
spec:
  template:
    spec:
      containers:
      - name: weaviate
        resources:
          requests:
            memory: "$requests_memory"
            cpu: "$requests_cpu"
          limits:
            memory: "$limits_memory"
            cpu: "$limits_cpu"
        env:
        - name: PLATFORM
          value: "$PLATFORM"
        - name: STORAGE_CLASS
          value: "$STORAGE_CLASS"
EOF
}

# Generate platform-specific kustomization
generate_kustomization() {
    local environment=${1:-dev}
    local output_dir="$SCRIPT_DIR/overlays/$environment-auto"
    
    mkdir -p "$output_dir"
    
    cat <<EOF > "$output_dir/kustomization.yaml"
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

metadata:
  name: falco-ai-alerts-$environment-auto
  annotations:
    platform: $PLATFORM
    storage-class: $STORAGE_CLASS
    generated-at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

resources:
  - ../../base

namespace: falco-ai-alerts-$environment

namePrefix: ${environment:0:3}-

commonLabels:
  environment: $environment
  platform: $PLATFORM
  app.kubernetes.io/version: "2.0.0-$environment"

patches:
  # Platform-specific storage class
  - target:
      kind: PersistentVolumeClaim
      name: weaviate-pvc
    patch: |-
      - op: replace
        path: /spec/storageClassName
        value: $STORAGE_CLASS
  
  # Platform-specific resource limits
  - target:
      kind: Deployment
      name: weaviate
    patch: |-
      - op: replace
        path: /spec/template/spec/containers/0/resources/requests/memory
        value: "$requests_memory"
      - op: replace
        path: /spec/template/spec/containers/0/resources/requests/cpu
        value: "$requests_cpu"
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/memory
        value: "$limits_memory"
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/cpu
        value: "$limits_cpu"
  
  # Environment-specific replicas
  - target:
      kind: Deployment
      name: falco-ai-alerts
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 1
  
  # Environment-specific service URLs
  - target:
      kind: ConfigMap
      name: falco-ai-alerts-config
    patch: |-
      - op: replace
        path: /data/OLLAMA_API_URL
        value: "http://${environment:0:3}-ollama:11434/api/generate"
      - op: replace
        path: /data/WEAVIATE_HOST
        value: "${environment:0:3}-weaviate"
  
  # Environment-specific Ollama service name in init job
  - target:
      kind: Job
      name: ollama-model-init
    patch: |-
      - op: replace
        path: /spec/template/spec/initContainers/0/command/2
        value: |
          echo "Waiting for Ollama service to be ready..."
          until wget -q --spider http://${environment:0:3}-ollama:11434/api/tags; do
            echo "Ollama not ready, waiting 10 seconds..."
            sleep 10
          done
          echo "Ollama is ready!"
      - op: replace
        path: /spec/template/spec/containers/0/command/2
        value: |
          echo "Pulling ultra-fast model: tinyllama (~637MB)"
          curl -X POST http://${environment:0:3}-ollama:11434/api/pull \
            -H "Content-Type: application/json" \
            -d '{"name": "tinyllama"}' \
            --max-time 1800
          
          echo "Pulling embedding model: nomic-embed-text (~274MB)"
          curl -X POST http://${environment:0:3}-ollama:11434/api/pull \
            -H "Content-Type: application/json" \
            -d '{"name": "nomic-embed-text"}' \
            --max-time 1800
          
          echo "Verifying models were pulled..."
          curl -s http://${environment:0:3}-ollama:11434/api/tags | grep -q "tinyllama" || exit 1
          curl -s http://${environment:0:3}-ollama:11434/api/tags | grep -q "nomic-embed-text" || exit 1
          
          echo "Warming up models with test inference..."
          curl -X POST http://${environment:0:3}-ollama:11434/api/generate \
            -H "Content-Type: application/json" \
            -d '{"model": "tinyllama", "prompt": "Hello, test", "stream": false}' \
            --max-time 60
          
          echo "Testing embedding model..."
          curl -X POST http://${environment:0:3}-ollama:11434/api/embeddings \
            -H "Content-Type: application/json" \
            -d '{"model": "nomic-embed-text", "prompt": "Hello, test"}' \
            --max-time 60
          
          echo "Model initialization and warm-up complete!"

images:
  - name: falco-ai-alerts
    newName: maddigsys/falco-ai-alerts
    newTag: v2.1.0
EOF

    echo "✅ Generated configuration: $output_dir/kustomization.yaml"
}

# Main execution
case "${1:-generate}" in
    "detect")
        echo "Platform: $PLATFORM"
        echo "Storage: $STORAGE_CLASS"
        echo "Resources: $RESOURCES"
        ;;
    "pvc")
        generate_pvc_patch
        ;;
    "deployment")
        generate_deployment_patch
        ;;
    "generate")
        generate_kustomization "${2:-dev}"
        ;;
    "all")
        for env in dev staging production; do
            generate_kustomization "$env"
        done
        ;;
    *)
        echo "Usage: $0 [detect|pvc|deployment|generate|all] [environment]"
        exit 1
        ;;
esac 