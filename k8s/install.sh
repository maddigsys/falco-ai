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

# Function to setup secrets
setup_secrets() {
    local environment=$1
    local namespace=$2
    
    print_step "Setting up secrets for $environment..."
    
    # Check if secrets already exist
    if kubectl get secret "${environment}-falco-ai-alerts-secrets" -n "$namespace" &> /dev/null; then
        print_warning "Secrets already exist. Skipping secret creation."
        print_info "To update secrets, delete them first: kubectl delete secret ${environment}-falco-ai-alerts-secrets -n $namespace"
        return 0
    fi
    
    print_info "Secrets not found. You'll need to create them manually after installation."
    print_info "Example commands:"
    echo "kubectl create secret generic ${environment}-falco-ai-alerts-secrets -n $namespace \\"
    echo "  --from-literal=SLACK_BOT_TOKEN=xoxb-your-token \\"
    echo "  --from-literal=OPENAI_API_KEY=your-openai-key \\"
    echo "  --from-literal=GEMINI_API_KEY=your-gemini-key"
    echo ""
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
    
    # Check if model initialization job completed
    print_info "Checking Ollama model initialization..."
    if kubectl wait --for=condition=complete job/"${prefix}ollama-model-init" -n "$namespace" --timeout=600s; then
        print_success "Ollama model initialization completed"
    else
        print_warning "Ollama model initialization taking longer than expected"
        print_info "You can check the status with: kubectl logs job/${prefix}ollama-model-init -n $namespace"
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
    echo "  Webhook: http://localhost:8080/falco-webhook"
    echo ""
    
    print_info "Check deployment status:"
    echo "  kubectl get all -n $namespace"
    echo ""
    
    print_info "View logs:"
    echo "  kubectl logs -f deployment/$service_name -n $namespace"
    echo ""
    
    if [ "$environment" = "production" ]; then
        print_info "Production features enabled:"
        echo "  • Auto-scaling (HPA): 3-10 replicas"
        echo "  • Network policies for security"
        echo "  • Resource limits and monitoring"
        echo "  • Ingress support (configure ingress.yaml)"
    fi
}

# Function to show post-installation steps
show_post_install() {
    local environment=$1
    
    echo ""
    print_step "Post-Installation Steps:"
    echo ""
    
    print_info "1. Configure Secrets (if not done already):"
    case $environment in
        development)
            echo "   kubectl create secret generic dev-falco-ai-alerts-secrets -n falco-ai-alerts-dev \\"
            ;;
        production)
            echo "   kubectl create secret generic prod-falco-ai-alerts-secrets -n falco-ai-alerts \\"
            ;;
    esac
    echo "     --from-literal=SLACK_BOT_TOKEN=xoxb-your-token \\"
    echo "     --from-literal=OPENAI_API_KEY=your-openai-key \\"
    echo "     --from-literal=GEMINI_API_KEY=your-gemini-key"
    echo ""
    
    print_info "2. Configure Falco to send alerts:"
    echo "   Edit falco.yaml and add webhook URL to your dashboard"
    echo ""
    
    print_info "3. Test the webhook:"
    echo "   curl -X POST http://localhost:8080/falco-webhook \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"rule\": \"Test Alert\", \"priority\": \"warning\", \"output\": \"Test message\"}'"
    echo ""
    
    print_info "4. Monitor the system:"
    echo "   kubectl get events -n falco-ai-alerts --sort-by='.lastTimestamp'"
    echo ""
    
    if [ "$environment" = "production" ]; then
        print_info "5. Production considerations:"
        echo "   • Configure Ingress for external access"
        echo "   • Set up monitoring and alerting"
        echo "   • Configure backup schedules"
        echo "   • Review security policies"
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
    --help, -h          - Show this help message

EXAMPLES:
    $0 dev                    # Install development environment
    $0 prod                   # Install production environment
    $0 dev --validate-only    # Just validate development config
    $0 prod --skip-wait       # Install production without waiting

FEATURES:
    - ✅ Automated prerequisite checking
    - ✅ Configuration validation
    - ✅ Secret setup guidance
    - ✅ Deployment status monitoring
    - ✅ Access instructions
    - ✅ Post-installation guidance

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
    else
        print_info "Namespace: falco-ai-alerts"
        print_info "Features: 3 replicas, HPA auto-scaling, security hardening"
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