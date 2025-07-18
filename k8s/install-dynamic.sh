#!/bin/bash

# Dynamic Falco AI Alert System Installation
# Auto-detects platform and deploys with appropriate configurations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/detect-platform.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}=============================================="
    echo -e "🚀 Falco AI Alert System - Dynamic Install"
    echo -e "=============================================${NC}\n"
}

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Detect platform and show info
detect_and_show_platform() {
    print_info "Detecting Kubernetes platform..."
    
    PLATFORM=$(detect_platform)
    STORAGE_CLASS=$(get_storage_class "$PLATFORM")
    RESOURCES=$(get_node_resources "$PLATFORM")
    
    echo -e "\n${GREEN}🎯 Platform Detection Results:${NC}"
    echo -e "   Platform: ${BLUE}$PLATFORM${NC}"
    echo -e "   Storage Class: ${BLUE}$STORAGE_CLASS${NC}"
    echo -e "   Resources: ${BLUE}$RESOURCES${NC}"
    
    # Platform-specific notes
    case $PLATFORM in
        "gke")
            print_info "Google Kubernetes Engine detected"
            print_info "Using optimized settings for GKE Autopilot/Standard"
            ;;
        "eks")
            print_info "Amazon EKS detected"
            print_info "Using optimized settings for AWS EKS"
            ;;
        "aks")
            print_info "Azure Kubernetes Service detected"
            print_info "Using optimized settings for AKS"
            ;;
        "local")
            print_warning "Local Kubernetes detected (minikube/kind/k3s)"
            print_warning "Using minimal resource settings"
            ;;
        "unknown")
            print_warning "Unknown platform - using default settings"
            ;;
    esac
}

# Generate dynamic configuration
generate_dynamic_config() {
    local environment=${1:-dev}
    
    print_info "Generating platform-specific configuration for $environment..."
    
    "$SCRIPT_DIR/generate-config.sh" generate "$environment"
    
    print_status "Configuration generated successfully"
}

# Create secrets
create_secrets() {
    local environment=${1:-dev}
    local namespace="falco-ai-alerts-$environment"
    
    print_info "Creating namespace and secrets for $environment..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace "$namespace" --dry-run=client -o yaml | kubectl apply -f -
    
    # Create secrets
    kubectl create secret generic "${environment:0:3}-falco-ai-alerts-secrets" \
        -n "$namespace" \
        --from-literal=SLACK_BOT_TOKEN="not-set" \
        --from-literal=PORTKEY_API_KEY="not-set" \
        --from-literal=OPENAI_VIRTUAL_KEY="not-set" \
        --from-literal=GEMINI_VIRTUAL_KEY="not-set" \
        --from-literal=DB_ENCRYPTION_KEY="$(openssl rand -base64 32)" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    print_status "Secrets created successfully"
}

# Function to convert bytes to human readable format
bytes_to_human() {
    local bytes=$1
    if [ $bytes -lt 1024 ]; then
        echo "${bytes}B"
    elif [ $bytes -lt 1048576 ]; then
        echo "$((bytes / 1024))KB"
    elif [ $bytes -lt 1073741824 ]; then
        echo "$((bytes / 1048576))MB"
    else
        echo "$((bytes / 1073741824))GB"
    fi
}

# Function to draw progress bar
draw_progress_bar() {
    local percentage=$1
    local width=40
    
    # Ensure percentage is within bounds
    if [ $percentage -lt 0 ]; then
        percentage=0
    elif [ $percentage -gt 100 ]; then
        percentage=100
    fi
    
    local filled=$((percentage * width / 100))
    local empty=$((width - filled))
    
    # Clear line and draw progress bar
    printf "\r\033[K["
    if [ $filled -gt 0 ]; then
        printf "%*s" $filled | tr ' ' '█'
    fi
    if [ $empty -gt 0 ]; then
        printf "%*s" $empty | tr ' ' '░'
    fi
    printf "] %3d%%" $percentage
}

# Function to monitor Ollama model download progress
monitor_ollama_progress() {
    local job_name=$1
    local namespace=$2
    local timeout=600  # 10 minutes timeout
    local start_time=$(date +%s)
    local last_percentage=0
    local download_complete=false
    
    print_info "Monitoring model download progress..."
    echo ""
    
    # Monitor job logs for progress
    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        # Check timeout
        if [ $elapsed -gt $timeout ]; then
            echo ""
            print_warning "Model download timeout after $((timeout / 60)) minutes"
            print_info "The download may still be running. Check logs: kubectl logs job/$job_name -n $namespace"
            return 1
        fi
        
        # Check if job completed
        if kubectl get job "$job_name" -n "$namespace" -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}' 2>/dev/null | grep -q "True"; then
            if [ "$download_complete" = "false" ]; then
                echo ""
                print_status "Model download completed successfully!"
                download_complete=true
            fi
            break
        fi
        
        # Check if job failed
        if kubectl get job "$job_name" -n "$namespace" -o jsonpath='{.status.conditions[?(@.type=="Failed")].status}' 2>/dev/null | grep -q "True"; then
            echo ""
            print_error "Model download failed"
            print_info "Check logs: kubectl logs job/$job_name -n $namespace"
            return 1
        fi
        
        # Get the latest logs and parse progress
        local latest_logs=$(kubectl logs job/"$job_name" -n "$namespace" --tail=10 2>/dev/null || echo "")
        
        if [ -n "$latest_logs" ]; then
            # Parse JSON for download progress
            local progress_line=$(echo "$latest_logs" | grep -E '"total":[0-9]+.*"completed":[0-9]+' | tail -1)
            
            if [ -n "$progress_line" ]; then
                # Extract total and completed bytes using grep and sed
                local total=$(echo "$progress_line" | grep -oE '"total":[0-9]+' | grep -oE '[0-9]+')
                local completed=$(echo "$progress_line" | grep -oE '"completed":[0-9]+' | grep -oE '[0-9]+')
                
                if [ -n "$total" ] && [ -n "$completed" ] && [ "$total" -gt 0 ]; then
                    local percentage=$((completed * 100 / total))
                    
                    # Only update if percentage changed significantly
                    if [ $percentage -gt $last_percentage ]; then
                        local completed_human=$(bytes_to_human $completed)
                        local total_human=$(bytes_to_human $total)
                        
                        # Calculate download speed and ETA
                        local remaining_bytes=$((total - completed))
                        local speed_info=""
                        if [ $elapsed -gt 10 ] && [ $completed -gt 0 ]; then
                            local speed_bps=$((completed / elapsed))
                            if [ $speed_bps -gt 0 ]; then
                                local eta_seconds=$((remaining_bytes / speed_bps))
                                local eta_minutes=$((eta_seconds / 60))
                                if [ $eta_minutes -gt 0 ]; then
                                    speed_info=$(printf " ETA: %dm" $eta_minutes)
                                else
                                    speed_info=$(printf " ETA: %ds" $eta_seconds)
                                fi
                            fi
                        fi
                        
                        draw_progress_bar $percentage
                        printf " %s / %s%s" "$completed_human" "$total_human" "$speed_info"
                        
                        last_percentage=$percentage
                    fi
                fi
            else
                # Check for status messages and other important log lines
                local status_line=$(echo "$latest_logs" | grep -E '"status":"' | tail -1)
                if [ -n "$status_line" ]; then
                    local status=$(echo "$status_line" | grep -oE '"status":"[^"]*"' | cut -d'"' -f4)
                    case "$status" in
                        "success")
                            printf "\r[✅] Model download completed                                    "
                            ;;
                        "verifying"*)
                            printf "\r[🔍] Verifying model integrity...                               "
                            ;;
                        "writing"*)
                            printf "\r[💾] Writing model to disk...                                  "
                            ;;
                        "pulling")
                            if [ $elapsed -gt 30 ]; then
                                printf "\r[📥] Downloading model (this may take several minutes)...       "
                            fi
                            ;;
                        *)
                            if [ -n "$status" ]; then
                                printf "\r[ℹ️ ] Status: %s                                    " "$status"
                            fi
                            ;;
                    esac
                else
                    # Check for other important messages
                    if echo "$latest_logs" | grep -q "Model initialization complete"; then
                        printf "\r[✅] Model initialization completed!                            "
                        download_complete=true
                        break
                    elif echo "$latest_logs" | grep -q "Waiting for Ollama"; then
                        printf "\r[⏳] Waiting for Ollama service to be ready...                 "
                    elif [ $elapsed -gt 60 ] && [ $((elapsed % 10)) -eq 0 ]; then
                        printf "\r[⏳] Model download in progress... (%dm %ds elapsed)            " $((elapsed / 60)) $((elapsed % 60))
                    fi
                fi
            fi
        fi
        
        sleep 2
    done
    
    echo ""
}

# Deploy application
deploy_application() {
    local environment=${1:-dev}
    local config_dir="$SCRIPT_DIR/overlays/$environment-auto"
    
    print_info "Deploying Falco AI Alert System for $environment..."
    
    if [[ ! -d "$config_dir" ]]; then
        print_error "Configuration directory not found: $config_dir"
        print_info "Run: $0 generate $environment"
        exit 1
    fi
    
    # Apply the configuration
    kubectl apply -k "$config_dir"
    
    print_status "Application deployed successfully"
}

# Wait for deployment
wait_for_deployment() {
    local environment=${1:-dev}
    local namespace="falco-ai-alerts-$environment"
    
    print_info "Waiting for deployments to be ready..."
    
    # Wait for Ollama first
    kubectl rollout status deployment/${environment:0:3}-ollama -n "$namespace" --timeout=300s
    
    # Wait for Weaviate
    kubectl rollout status deployment/${environment:0:3}-weaviate -n "$namespace" --timeout=300s
    
    # Monitor Ollama model download progress
    local job_name="${environment:0:3}-ollama-model-init"
    if kubectl get job "$job_name" -n "$namespace" >/dev/null 2>&1; then
        monitor_ollama_progress "$job_name" "$namespace"
    fi
    
    # Wait for main app
    kubectl rollout status deployment/${environment:0:3}-falco-ai-alerts -n "$namespace" --timeout=300s
    
    print_status "All deployments are ready"
}

# Show access information
show_access_info() {
    local environment=${1:-dev}
    local namespace="falco-ai-alerts-$environment"
    
    print_info "Getting access information..."
    
    # Get service info
    kubectl get services -n "$namespace"
    
    # Get external access
    case $PLATFORM in
        "gke"|"eks"|"aks")
            print_info "For external access, you may need to create an ingress or port-forward:"
            echo "kubectl port-forward svc/${environment:0:3}-falco-ai-alerts 8080:8080 -n $namespace"
            ;;
        "local")
            local nodeport=$(kubectl get svc ${environment:0:3}-falco-ai-alerts -n "$namespace" -o jsonpath='{.spec.ports[0].nodePort}')
            print_info "Access the application at: http://localhost:$nodeport"
            ;;
    esac
}

# Main installation flow
main() {
    print_header
    
    local environment=${1:-dev}
    local action=${2:-all}
    
    case $action in
        "detect")
            detect_and_show_platform
            ;;
        "generate")
            detect_and_show_platform
            generate_dynamic_config "$environment"
            ;;
        "secrets")
            create_secrets "$environment"
            ;;
        "deploy")
            deploy_application "$environment"
            ;;
        "wait")
            wait_for_deployment "$environment"
            ;;
        "info")
            show_access_info "$environment"
            ;;
        "all")
            detect_and_show_platform
            generate_dynamic_config "$environment"
            create_secrets "$environment"
            deploy_application "$environment"
            wait_for_deployment "$environment"
            show_access_info "$environment"
            ;;
        *)
            echo "Usage: $0 [environment] [action]"
            echo "Environment: dev, staging, production"
            echo "Action: detect, generate, secrets, deploy, wait, info, all"
            exit 1
            ;;
    esac
    
    print_status "Installation completed successfully! 🎉"
}

# Run main function
main "$@" 