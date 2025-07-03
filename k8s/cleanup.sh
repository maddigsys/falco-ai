#!/bin/bash

# Falco AI Alert System - Cleanup Script
# This script provides safe cleanup of Kubernetes deployments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/${DATE}"

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

print_header() {
    echo -e "${BLUE}"
    echo "=============================================="
    echo "🗑️  Falco AI Alert System - Cleanup Script"
    echo "=============================================="
    echo -e "${NC}"
}

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl not found. Please install kubectl first."
        exit 1
    fi
    
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    print_success "kubectl is available and cluster is accessible"
}

# Function to backup data
backup_data() {
    local namespace=$1
    local deployment_name=$2
    
    print_info "Creating backup for namespace: $namespace"
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Check if deployment exists
    if ! kubectl get deployment "$deployment_name" -n "$namespace" &> /dev/null; then
        print_warning "Deployment $deployment_name not found in namespace $namespace. Skipping backup."
        return 0
    fi
    
    # Get first pod name
    local pod_name=$(kubectl get pods -n "$namespace" -l app.kubernetes.io/name=falco-ai-alerts -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    
    if [ -z "$pod_name" ]; then
        print_warning "No running pods found in namespace $namespace. Skipping database backup."
    else
        print_info "Backing up database from pod: $pod_name"
        
        # Backup database
        if kubectl exec "$pod_name" -n "$namespace" -- test -f /app/data/alerts.db 2>/dev/null; then
            kubectl cp "$namespace/$pod_name:/app/data/alerts.db" "$BACKUP_DIR/alerts-${namespace}-${DATE}.db"
            print_success "Database backed up to: $BACKUP_DIR/alerts-${namespace}-${DATE}.db"
        else
            print_warning "Database file not found in pod. Skipping database backup."
        fi
    fi
    
    # Backup Ollama model data if available
    local ollama_deployment=""
    if [ "$namespace" = "falco-ai-alerts-dev" ]; then
        ollama_deployment="dev-ollama"
    else
        ollama_deployment="prod-ollama"
    fi
    
    if kubectl get deployment "$ollama_deployment" -n "$namespace" &> /dev/null; then
        local ollama_pod=$(kubectl get pods -n "$namespace" -l app=ollama -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
        if [ -n "$ollama_pod" ]; then
            print_info "Backing up Ollama model configuration..."
            kubectl exec "$ollama_pod" -n "$namespace" -- ollama list > "$BACKUP_DIR/ollama-models-${namespace}-${DATE}.txt" 2>/dev/null || true
            print_success "Ollama models backed up to: $BACKUP_DIR/ollama-models-${namespace}-${DATE}.txt"
        fi
    fi
    
    # Backup configuration
    kubectl get configmap,secret -n "$namespace" -o yaml > "$BACKUP_DIR/config-${namespace}-${DATE}.yaml" 2>/dev/null || true
    print_success "Configuration backed up to: $BACKUP_DIR/config-${namespace}-${DATE}.yaml"
}

# Function to cleanup namespace
cleanup_namespace() {
    local environment=$1
    local namespace=$2
    local kustomize_path=$3
    
    print_info "Cleaning up $environment environment (namespace: $namespace)"
    
    # Check if namespace exists
    if ! kubectl get namespace "$namespace" &> /dev/null; then
        print_warning "Namespace $namespace does not exist. Skipping cleanup."
        return 0
    fi
    
    # Delete model initialization jobs first (they can block cleanup)
    print_info "Cleaning up model initialization jobs..."
    kubectl delete job --all -n "$namespace" 2>/dev/null || true
    
    # Scale down deployments gracefully
    print_info "Scaling down deployments..."
    kubectl scale deployment --all --replicas=0 -n "$namespace" 2>/dev/null || true
    
    # Wait for pods to terminate
    print_info "Waiting for pods to terminate gracefully..."
    kubectl wait --for=delete pod --all -n "$namespace" --timeout=60s 2>/dev/null || true
    
    # Delete using kustomize
    if [ -f "$kustomize_path/kustomization.yaml" ]; then
        print_info "Deleting resources using kustomize..."
        kubectl delete -k "$kustomize_path" 2>/dev/null || true
    else
        print_warning "Kustomization file not found at $kustomize_path. Deleting resources manually..."
        kubectl delete all --all -n "$namespace" 2>/dev/null || true
    fi
    
    # Delete PVCs if requested
    if [ "$DELETE_DATA" = "true" ]; then
        print_warning "Deleting persistent volumes (this will delete all data)..."
        kubectl delete pvc --all -n "$namespace" 2>/dev/null || true
    fi
    
    # Delete namespace
    print_info "Deleting namespace: $namespace"
    kubectl delete namespace "$namespace" 2>/dev/null || true
    
    # Clean up cluster-wide resources
    local prefix=""
    if [ "$environment" = "development" ]; then
        prefix="dev-"
    elif [ "$environment" = "production" ]; then
        prefix="prod-"
    fi
    
    print_info "Cleaning up cluster-wide resources..."
    kubectl delete clusterrole "${prefix}falco-ai-alerts" 2>/dev/null || true
    kubectl delete clusterrolebinding "${prefix}falco-ai-alerts" 2>/dev/null || true
    
    print_success "$environment environment cleanup completed"
}

# Function to verify cleanup
verify_cleanup() {
    print_info "Verifying cleanup..."
    
    # Check namespaces
    local remaining_namespaces=$(kubectl get namespace | grep falco-ai-alerts | wc -l)
    if [ "$remaining_namespaces" -gt 0 ]; then
        print_warning "Some falco-ai-alerts namespaces still exist:"
        kubectl get namespace | grep falco-ai-alerts
    else
        print_success "All falco-ai-alerts namespaces removed"
    fi
    
    # Check cluster-wide resources
    local remaining_clusterroles=$(kubectl get clusterrole | grep falco-ai-alerts | wc -l)
    local remaining_clusterrolebindings=$(kubectl get clusterrolebinding | grep falco-ai-alerts | wc -l)
    
    if [ "$remaining_clusterroles" -gt 0 ] || [ "$remaining_clusterrolebindings" -gt 0 ]; then
        print_warning "Some cluster-wide resources still exist:"
        kubectl get clusterrole,clusterrolebinding | grep falco-ai-alerts || true
    else
        print_success "All cluster-wide resources removed"
    fi
}

# Function to show help
show_help() {
    cat << EOF
Falco AI Alert System - Cleanup Script

USAGE:
    $0 [OPTIONS] ENVIRONMENT

ENVIRONMENTS:
    dev, development     - Clean up development environment
    prod, production     - Clean up production environment  
    all                  - Clean up all environments

OPTIONS:
    --no-backup         - Skip backup creation
    --delete-data       - Delete persistent volumes (⚠️  IRREVERSIBLE!)
    --force             - Skip confirmation prompts
    --help, -h          - Show this help message

EXAMPLES:
    $0 dev                    # Clean up development (with backup)
    $0 prod --delete-data     # Clean up production and delete all data
    $0 all --force            # Clean up everything without prompts
    $0 dev --no-backup        # Clean up development without backup

SAFETY FEATURES:
    - Creates backups by default (unless --no-backup)
    - Requires confirmation for destructive operations
    - Graceful shutdown before deletion
    - Verification of cleanup completion
    - Backs up Ollama models and database
    - Handles tinyllama model cleanup properly

EOF
}

# Main function
main() {
    # Parse command line arguments
    ENVIRONMENT=""
    CREATE_BACKUP="true"
    DELETE_DATA="false"
    FORCE="false"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-backup)
                CREATE_BACKUP="false"
                shift
                ;;
            --delete-data)
                DELETE_DATA="true"
                shift
                ;;
            --force)
                FORCE="true"
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
            all)
                ENVIRONMENT="all"
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
        echo "Use: $0 [dev|prod|all]"
        echo "Use --help for more information"
        exit 1
    fi
    
    print_header
    
    # Check prerequisites
    check_kubectl
    
    # Show current cluster info
    print_info "Current cluster context: $(kubectl config current-context)"
    print_info "Cleanup environment: $ENVIRONMENT"
    print_info "Will clean up: Falco AI Alerts + Ollama (tinyllama) + model data"
    
    # Safety confirmation
    if [ "$FORCE" != "true" ]; then
        echo ""
        print_warning "This will delete Falco AI Alert System resources from your cluster!"
        if [ "$DELETE_DATA" = "true" ]; then
            print_error "⚠️  DATA DELETION ENABLED - This will permanently delete all alert data!"
        fi
        echo ""
        read -p "Are you sure you want to proceed? (Type 'yes' to continue): " confirm
        
        if [ "$confirm" != "yes" ]; then
            print_info "Cleanup cancelled by user"
            exit 0
        fi
    fi
    
    # Create backups if requested
    if [ "$CREATE_BACKUP" = "true" ]; then
        print_info "Creating backups before cleanup..."
        
        if [ "$ENVIRONMENT" = "development" ] || [ "$ENVIRONMENT" = "all" ]; then
            backup_data "falco-ai-alerts-dev" "dev-falco-ai-alerts"
        fi
        
        if [ "$ENVIRONMENT" = "production" ] || [ "$ENVIRONMENT" = "all" ]; then
            backup_data "falco-ai-alerts" "prod-falco-ai-alerts"
        fi
    fi
    
    # Perform cleanup
    if [ "$ENVIRONMENT" = "development" ] || [ "$ENVIRONMENT" = "all" ]; then
        cleanup_namespace "development" "falco-ai-alerts-dev" "$SCRIPT_DIR/overlays/development"
    fi
    
    if [ "$ENVIRONMENT" = "production" ] || [ "$ENVIRONMENT" = "all" ]; then
        cleanup_namespace "production" "falco-ai-alerts" "$SCRIPT_DIR/overlays/production"
    fi
    
    # Verify cleanup
    verify_cleanup
    
    # Summary
    echo ""
    print_success "Cleanup completed!"
    if [ "$CREATE_BACKUP" = "true" ] && [ -d "$BACKUP_DIR" ]; then
        print_info "Backups saved to: $BACKUP_DIR"
    fi
    
    print_info "To reinstall, run: kubectl apply -k overlays/$ENVIRONMENT/"
}

# Run main function with all arguments
main "$@" 