#!/bin/bash

# Falco AI Alert System - Installation Script
# This script provides automated installation for Kubernetes deployments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
DATE=$(date +%Y%m%d_%H%M%S)

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo -e "${PURPLE}🚀 $1${NC}"
}

print_header() {
    echo -e "${CYAN}"
    echo "=============================================="
    echo "🚀 Falco AI Alert System - Installation Script"
    echo "=============================================="
    echo -e "${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install kubectl first."
        echo "Install from: https://kubernetes.io/docs/tasks/tools/"
        exit 1
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    # Check Kustomize (built into kubectl 1.14+)
    if ! kubectl kustomize --help &> /dev/null; then
        print_error "kubectl kustomize not available. Please update kubectl to version 1.14+."
        exit 1
    fi
    
    print_success "All prerequisites satisfied"
    
    # Show cluster info
    local cluster_info=$(kubectl config current-context)
    print_info "Target cluster: $cluster_info"
}

# Function to validate environment config
validate_config() {
    local environment=$1
    print_step "Validating configuration for $environment environment..."
    
    # Check if kustomization exists
    local kustomize_path="$SCRIPT_DIR/overlays/$environment"
    if [ ! -f "$kustomize_path/kustomization.yaml" ]; then
        print_error "Configuration not found: $kustomize_path/kustomization.yaml"
        exit 1
    fi
    
    # Validate kustomization syntax
    if ! kubectl kustomize "$kustomize_path" > /dev/null 2>&1; then
        print_error "Invalid kustomization configuration in $kustomize_path"
        print_info "Run: kubectl kustomize $kustomize_path"
        exit 1
    fi
    
    print_success "Configuration validated"
}

# Function to get standardized secret name
get_secret_name() {
    local environment=$1
    case $environment in
        development)
            echo "dev-falco-ai-alerts-secrets"
            ;;
        production)
            echo "prod-falco-ai-alerts-secrets"
            ;;
        *)
            echo "${environment}-falco-ai-alerts-secrets"
            ;;
    esac
}

# Function to validate secrets
validate_secrets() {
    local environment=$1
    local namespace=$2
    local skip_validation=$3
    
    print_step "Validating secrets for $environment environment..."
    
    # Skip validation if requested
    if [ "$skip_validation" = "true" ]; then
        print_warning "Skipping secret validation (--skip-secrets enabled)"
        return 0
    fi
    
    local secret_name=$(get_secret_name "$environment")
    
    # Check if namespace exists first
    if ! kubectl get namespace "$namespace" &> /dev/null; then
        print_info "Namespace '$namespace' doesn't exist yet (will be created during installation)"
        print_error "Secrets must be created after namespace creation"
        show_secret_creation_instructions "$environment" "$namespace"
        exit 1
    fi
    
    # Check if secrets exist
    if ! kubectl get secret "$secret_name" -n "$namespace" &> /dev/null; then
        print_error "Required secrets not found: $secret_name"
        echo ""
        print_info "Secrets are required for the application to function properly."
        show_secret_creation_instructions "$environment" "$namespace"
        exit 1
    fi
    
    # Validate secret has required keys
    print_info "Checking secret content..."
    local missing_keys=()
    local required_keys=("SLACK_BOT_TOKEN" "PORTKEY_API_KEY" "OPENAI_VIRTUAL_KEY" "GEMINI_VIRTUAL_KEY")
    
    for key in "${required_keys[@]}"; do
        if ! kubectl get secret "$secret_name" -n "$namespace" -o jsonpath="{.data.$key}" &> /dev/null; then
            missing_keys+=("$key")
        fi
    done
    
    if [ ${#missing_keys[@]} -gt 0 ]; then
        print_error "Secret exists but missing required keys: ${missing_keys[*]}"
        echo ""
        print_info "Update your secret with all required keys:"
        show_secret_update_instructions "$environment" "$namespace"
        exit 1
    fi
    
    print_success "Secrets validation passed"
}

# Function to show secret creation instructions
show_secret_creation_instructions() {
    local environment=$1
    local namespace=$2
    local secret_name=$(get_secret_name "$environment")
    
    echo ""
    print_info "🔑 REQUIRED: Create secrets before installation"
    echo ""
    echo "1. First, ensure the namespace exists:"
    echo "   kubectl create namespace $namespace"
    echo ""
    echo "2. Create the required secrets:"
    echo "   kubectl create secret generic $secret_name -n $namespace \\"
    echo "     --from-literal=SLACK_BOT_TOKEN=\"xoxb-your-slack-bot-token\" \\"
    echo "     --from-literal=PORTKEY_API_KEY=\"pk-your-portkey-api-key\" \\"
    echo "     --from-literal=OPENAI_VIRTUAL_KEY=\"openai-your-virtual-key\" \\"
    echo "     --from-literal=GEMINI_VIRTUAL_KEY=\"gemini-your-virtual-key\" \\"
    echo "     --from-literal=DB_ENCRYPTION_KEY=\"\$(openssl rand -base64 32)\""
    echo ""
    print_info "📝 AI Provider Configuration:"
    echo "   • Slack: Get bot token from https://api.slack.com/apps"
    echo "   • Portkey: Get API key from https://portkey.ai (security layer for cloud AI)"
    echo "   • OpenAI: Get virtual key from Portkey dashboard (after adding OpenAI)"
    echo "   • Gemini: Get virtual key from Portkey dashboard (after adding Gemini)"
    echo "   • Ollama: No API key needed (runs locally in cluster)"
    echo ""
    print_info "🤖 Default AI Model: llama3.1:8b"
    echo "   • Size: ~4.9GB download, 6-8GB RAM required"
    echo "   • Performance: Fast inference (2-5 seconds)"
    echo "   • Use case: Reliable default for all environments"
    echo ""
    print_info "🛡️ Cybersecurity Model Upgrade (Optional):"
    echo "   • Model: jimscard/whiterabbit-neo:latest (13B)"
    echo "   • Enhanced security analysis capabilities"
    echo "   • Requires: 14-16GB RAM, 30Gi storage"
    echo "   • Upgrade via dashboard after deployment"
    echo ""
    print_info "🔄 After creating secrets, run the installation again:"
    echo "   ./install.sh $environment"
    echo ""
    print_info "⚠️  To skip secret validation (not recommended):"
    echo "   ./install.sh $environment --skip-secrets"
}

# Function to show secret update instructions
show_secret_update_instructions() {
    local environment=$1
    local namespace=$2
    local secret_name=$(get_secret_name "$environment")
    
    echo ""
    echo "Delete and recreate the secret with all required keys:"
    echo "   kubectl delete secret $secret_name -n $namespace"
    echo "   kubectl create secret generic $secret_name -n $namespace \\"
    echo "     --from-literal=SLACK_BOT_TOKEN=\"xoxb-your-slack-bot-token\" \\"
    echo "     --from-literal=PORTKEY_API_KEY=\"pk-your-portkey-api-key\" \\"
    echo "     --from-literal=OPENAI_VIRTUAL_KEY=\"openai-your-virtual-key\" \\"
    echo "     --from-literal=GEMINI_VIRTUAL_KEY=\"gemini-your-virtual-key\" \\"
    echo "     --from-literal=DB_ENCRYPTION_KEY=\"\$(openssl rand -base64 32)\""
    echo ""
    print_info "Or update existing secret by adding missing keys:"
    echo "   kubectl patch secret $secret_name -n $namespace \\"
    echo "     --type='merge' -p='{\"stringData\":{\"MISSING_KEY\":\"your-key-value\"}}'"
}

# Function to setup secrets
setup_secrets() {
    local environment=$1
    local namespace=$2
    
    print_step "Verifying secrets for $environment..."
    
    # Check if secrets already exist
    local secret_name=$(get_secret_name "$environment")
    if kubectl get secret "$secret_name" -n "$namespace" &> /dev/null; then
        print_success "Secrets found and ready to use"
        return 0
    fi
    
    print_error "Secrets not found. This should not happen after validation."
    print_info "Please run the installation again to re-validate secrets."
    exit 1
}

# Function to install environment
install_environment() {
    local environment=$1
    local namespace=""
    
    case $environment in
        development)
            namespace="falco-ai-alerts-dev"
            ;;
        production)
            namespace="falco-ai-alerts"
            ;;
        *)
            print_error "Unknown environment: $environment"
            exit 1
            ;;
    esac
    
    print_step "Installing $environment environment to namespace: $namespace"
    
    # Apply the kustomization
    local kustomize_path="$SCRIPT_DIR/overlays/$environment"
    print_info "Applying Kubernetes manifests..."
    kubectl apply -k "$kustomize_path"
    
    print_success "Manifests applied successfully"
    
    # Wait for namespace to be ready
    print_info "Waiting for namespace to be ready..."
    kubectl wait --for=condition=Ready namespace/"$namespace" --timeout=60s || true
    
    # Setup secrets
    setup_secrets "$environment" "$namespace"
    
    # Wait for deployments to be ready
    print_info "Waiting for deployments to be ready (this may take a few minutes)..."
    
    local prefix=""
    if [ "$environment" = "development" ]; then
        prefix="dev-"
    elif [ "$environment" = "production" ]; then
        prefix="prod-"
    fi
    
    # Wait for Falco AI Alerts deployment
    print_info "Waiting for Falco AI Alerts deployment..."
    kubectl wait --for=condition=available deployment/"${prefix}falco-ai-alerts" -n "$namespace" --timeout=300s
    
    # Wait for Ollama deployment
    print_info "Waiting for Ollama deployment..."
    kubectl wait --for=condition=available deployment/"${prefix}ollama" -n "$namespace" --timeout=300s
    
    # Check if model initialization job completed with progress tracking
    print_info "Checking Ollama model initialization..."
    
    # Wait for job to start
    local job_name="${prefix}ollama-model-init"
    local max_wait=60
    local waited=0
    
    while [ $waited -lt $max_wait ]; do
        if kubectl get job "$job_name" -n "$namespace" &> /dev/null; then
            break
        fi
        sleep 5
        waited=$((waited + 5))
        print_info "Waiting for Ollama model initialization job to start... (${waited}s)"
    done
    
    # Check if job exists
    if ! kubectl get job "$job_name" -n "$namespace" &> /dev/null; then
        print_warning "Ollama model initialization job not found"
        return 0
    fi
    
    # Monitor progress with real-time logs
    if [ "$SKIP_WAIT" = "true" ]; then
        print_info "Skipping Ollama progress monitoring (--skip-wait enabled)"
        print_info "Model download started. Check progress with: kubectl logs job/$job_name -n $namespace -f"
    else
        print_info "Downloading llama3.1:8b model (~4.9GB, optimized for reliability)..."
        monitor_ollama_progress "$job_name" "$namespace"
    fi
    
    print_success "$environment environment installation completed!"
}

# Function to show access instructions
show_access_instructions() {
    local environment=$1
    local namespace=""
    local service_name=""
    local port=""
    
    case $environment in
        development)
            namespace="falco-ai-alerts-dev"
            service_name="dev-falco-ai-alerts"
            port="30080"
            ;;
        production)
            namespace="falco-ai-alerts"
            service_name="prod-falco-ai-alerts"
            port="8080"
            ;;
    esac
    
    echo ""
    print_step "Access Instructions for $environment:"
    echo ""
    
    if [ "$environment" = "development" ]; then
        print_info "Development uses NodePort for easy access:"
        echo "  Browser: http://localhost:$port/dashboard"
        echo "  Webhook: http://localhost:$port/falco-webhook"
        echo ""
        print_info "Or use port-forward:"
    else
        print_info "Use port-forward to access the application:"
    fi
    
    echo "  kubectl port-forward svc/$service_name 8080:8080 -n $namespace"
    echo "  Browser: http://localhost:8080/dashboard"
    echo ""
    
    print_info "🔗 Webhook URLs (for Falco configuration):"
    if [ "$environment" = "development" ]; then
        echo "  Internal: http://dev-falco-ai-alerts-webhook.falco-ai-alerts-dev/falco-webhook"
        echo "  External: http://localhost:8080/falco-webhook (via port-forward)"
    else
        echo "  Internal: http://prod-falco-ai-alerts-webhook.falco-ai-alerts/falco-webhook"
        echo "  External: http://your-domain.com/falco-webhook (via ingress)"
    fi
    echo ""
    
    print_info "Check deployment status:"
    echo "  kubectl get all -n $namespace"
    echo ""
    
    print_info "View logs:"
    echo "  kubectl logs -f deployment/$service_name -n $namespace"
    echo ""
    
    if [ "$environment" = "production" ]; then
        print_info "🚀 Production Features Enabled:"
        echo "  • Auto-scaling (HPA): 3-10 replicas based on CPU/memory"
        echo "  • Dedicated webhook service with clean URLs (port 80)"
        echo "  • Network policies for enhanced security"
        echo "  • Resource limits and Prometheus monitoring"
        echo "  • Ingress support for external access"
        echo "  • Optimized for llama3.1:8b model (30s response time)"
        echo "  • Optional cybersecurity model upgrade available"
    fi
}

# Function to show post-installation steps
show_post_install() {
    local environment=$1
    
    echo ""
    print_step "Post-Installation Steps:"
    echo ""
    
    print_info "1. 🎯 Configure Falco Integration (Easy Setup):"
    echo "   • Open the dashboard: http://localhost:8080/dashboard"
    echo "   • Navigate to the 'Falco Integration Setup' section"
    echo "   • Copy the provided webhook URL and configuration"
    echo "   • Paste into your falco.yaml file"
    echo ""
    
    print_info "2. ✅ Test the Integration:"
    echo "   • Use the 'Send Test Alert' button in the dashboard, OR"
    echo "   • Manual test:"
    echo "     curl -X POST http://localhost:8080/falco-webhook \\"
    echo "       -H 'Content-Type: application/json' \\"
    echo "       -d '{\"rule\": \"Test Alert\", \"priority\": \"warning\", \"output\": \"Test message\"}'"
    echo ""
    
    print_info "3. 📊 Monitor Your System:"
    echo "   • Dashboard: Real-time alerts with AI analysis"
    echo "   • Logs: kubectl logs -f deployment/$service_name -n $namespace"
    echo "   • Events: kubectl get events -n $namespace --sort-by='.lastTimestamp'"
    echo ""
    
    if [ "$environment" = "production" ]; then
        print_info "4. 🏭 Production Considerations:"
        echo "   • Configure Ingress for external webhook access"
        echo "   • Set up monitoring (Prometheus metrics available)"
        echo "   • Configure backup schedules for persistent data"
        echo "   • Review and customize network security policies"
        echo "   • Consider upgrading to cybersecurity model (jimscard/whiterabbit-neo)"
        echo "   • Consider setting up external AI providers for redundancy"
        echo ""
        print_info "5. 🛡️ Cybersecurity Model Upgrade:"
        echo "   • Default: llama3.1:8b (reliable, fast, 8GB RAM)"
        echo "   • Upgrade: jimscard/whiterabbit-neo:latest (specialized, 16GB RAM)"
        echo "   • Upgrade via: http://localhost:8080/config/ai"
        echo "   • See k8s/OLLAMA_MODELS.md for detailed upgrade instructions"
    fi
}

# Function to monitor Ollama model download progress
monitor_ollama_progress() {
    local job_name=$1
    local namespace=$2
    local timeout=600  # 10 minutes timeout (optimized for 8B model downloads)
    local start_time=$(date +%s)
    local last_percentage=0
    local download_complete=false
    
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
                print_success "Model download completed successfully!"
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
    
    # Final verification
    if kubectl wait --for=condition=complete job/"$job_name" -n "$namespace" --timeout=60s &> /dev/null; then
        print_success "Ollama model initialization completed successfully!"
        
        # Show model verification
        print_info "Verifying model installation..."
        local verification_logs=$(kubectl logs job/"$job_name" -n "$namespace" --tail=5 2>/dev/null || echo "")
        if echo "$verification_logs" | grep -q "Model initialization complete"; then
            print_success "Model verification passed"
        else
            print_warning "Could not verify model installation"
        fi
    else
        print_warning "Job completed but verification failed"
        print_info "Check logs: kubectl logs job/$job_name -n $namespace"
        return 1
    fi
}

# Function to show help
show_help() {
    cat << EOF
Falco AI Alert System - Installation Script

USAGE:
    $0 [OPTIONS] ENVIRONMENT

ENVIRONMENTS:
    dev, development     - Install development environment
    prod, production     - Install production environment  

OPTIONS:
    --validate-only     - Only validate configuration, don't install
    --skip-wait         - Skip waiting for deployments to be ready
    --skip-secrets      - Skip secret validation (not recommended)
    --help, -h          - Show this help message

EXAMPLES:
    $0 dev                    # Install development environment
    $0 prod                   # Install production environment
    $0 dev --validate-only    # Just validate development config
    $0 prod --skip-wait       # Install production without waiting
    $0 dev --skip-secrets     # Install without secret validation

 FEATURES:
     - ✅ Automated prerequisite checking
     - ✅ Configuration validation  
     - ✅ Required secret validation
     - ✅ Deployment status monitoring
     - ✅ Real-time Ollama model download progress
     - ✅ Clean webhook URLs (dedicated service on port 80)
     - ✅ Comprehensive dashboard with Falco integration setup
     - ✅ Access instructions and post-installation guidance
     - ✅ Default llama3.1:8b model (fast, reliable, 8GB RAM)
     - ✅ Optional cybersecurity model upgrade (jimscard/whiterabbit-neo)

REQUIREMENTS:
    - kubectl (v1.14+)
    - Access to Kubernetes cluster
    - Cluster admin permissions (for RBAC)

EOF
}

# Main function
main() {
    # Parse command line arguments
    ENVIRONMENT=""
    VALIDATE_ONLY="false"
    SKIP_WAIT="false"
    SKIP_SECRETS="false"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --validate-only)
                VALIDATE_ONLY="true"
                shift
                ;;
            --skip-wait)
                SKIP_WAIT="true"
                shift
                ;;
            --skip-secrets)
                SKIP_SECRETS="true"
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            dev|development)
                ENVIRONMENT="development"
                shift
                ;;
            prod|production)
                ENVIRONMENT="production"
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Validate environment argument
    if [ -z "$ENVIRONMENT" ]; then
        print_error "Environment argument required"
        echo "Use: $0 [dev|prod]"
        echo "Use --help for more information"
        exit 1
    fi
    
    print_header
    
    # Check prerequisites
    check_prerequisites
    
    # Validate configuration
    validate_config "$ENVIRONMENT"
    
    # Determine namespace based on environment
    local namespace=""
    case $ENVIRONMENT in
        development)
            namespace="falco-ai-alerts-dev"
            ;;
        production)
            namespace="falco-ai-alerts"
            ;;
    esac
    
    # Validate secrets before installation
    validate_secrets "$ENVIRONMENT" "$namespace" "$SKIP_SECRETS"
    
    if [ "$VALIDATE_ONLY" = "true" ]; then
        print_success "Configuration validation completed!"
        exit 0
    fi
    
    # Show installation summary
    echo ""
    print_step "Installation Summary:"
    print_info "Environment: $ENVIRONMENT"
    print_info "Target cluster: $(kubectl config current-context)"
    if [ "$ENVIRONMENT" = "development" ]; then
        print_info "Namespace: falco-ai-alerts-dev"
        print_info "Features: Single replica, NodePort access, debug logging"
        print_info "AI Model: llama3.1:8b (default, 8GB RAM, fast inference)"
    else
        print_info "Namespace: falco-ai-alerts"
        print_info "Features: 3 replicas, HPA auto-scaling, security hardening"
        print_info "AI Model: llama3.1:8b (default, 8GB RAM, fast inference)"
        print_info "Upgrade: jimscard/whiterabbit-neo available for enhanced security"
    fi
    echo ""
    
    # Confirmation
    read -p "Proceed with installation? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_info "Installation cancelled by user"
        exit 0
    fi
    
    # Install environment
    install_environment "$ENVIRONMENT"
    
    # Skip waiting if requested
    if [ "$SKIP_WAIT" = "true" ]; then
        print_info "Skipping deployment readiness check"
    fi
    
    # Show access instructions
    show_access_instructions "$ENVIRONMENT"
    
    # Show post-installation steps
    show_post_install "$ENVIRONMENT"
    
    # Final success message
    echo ""
    print_success "🎉 Falco AI Alert System installation completed!"
    print_info "Your $ENVIRONMENT environment is ready to use."
    print_info "Check the access instructions above to start using the system."
    
    # Cleanup instructions
    echo ""
    print_info "To uninstall later, run: ./cleanup.sh $ENVIRONMENT"
}

# Run main function with all arguments
main "$@" 