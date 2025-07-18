#!/bin/bash

# Kubernetes Platform Detection Script
# Automatically detects cloud provider and returns appropriate storage class

detect_platform() {
    echo "🔍 Detecting Kubernetes platform..." >&2
    
    # Check for GKE
    if kubectl get nodes -o jsonpath='{.items[0].spec.providerID}' 2>/dev/null | grep -q "gce://"; then
        echo "gke"
        return 0
    fi
    
    # Check for EKS
    if kubectl get nodes -o jsonpath='{.items[0].spec.providerID}' 2>/dev/null | grep -q "aws://"; then
        echo "eks"
        return 0
    fi
    
    # Check for AKS
    if kubectl get nodes -o jsonpath='{.items[0].spec.providerID}' 2>/dev/null | grep -q "azure://"; then
        echo "aks"
        return 0
    fi
    
    # Check for DigitalOcean
    if kubectl get nodes -o jsonpath='{.items[0].spec.providerID}' 2>/dev/null | grep -q "digitalocean://"; then
        echo "doks"
        return 0
    fi
    
    # Check for IBM Cloud
    if kubectl get nodes -o jsonpath='{.items[0].metadata.labels}' 2>/dev/null | grep -q "ibm-cloud"; then
        echo "ibm"
        return 0
    fi
    
    # Check available storage classes for local/minikube
    if kubectl get storageclass 2>/dev/null | grep -q "hostpath\|local-path"; then
        echo "local"
        return 0
    fi
    
    # Default fallback
    echo "unknown"
    return 1
}

get_storage_class() {
    local platform=$1
    
    case $platform in
        "gke")
            # Check if premium is available, otherwise use standard
            if kubectl get storageclass premium-rwo >/dev/null 2>&1; then
                echo "premium-rwo"
            else
                echo "standard-rwo"
            fi
            ;;
        "eks")
            # Check available EKS storage classes
            if kubectl get storageclass gp3 >/dev/null 2>&1; then
                echo "gp3"
            elif kubectl get storageclass gp2 >/dev/null 2>&1; then
                echo "gp2"
            else
                echo "default"
            fi
            ;;
        "aks")
            if kubectl get storageclass managed-premium >/dev/null 2>&1; then
                echo "managed-premium"
            else
                echo "default"
            fi
            ;;
        "doks")
            echo "do-block-storage"
            ;;
        "ibm")
            echo "ibmc-block-silver"
            ;;
        "local")
            if kubectl get storageclass local-path >/dev/null 2>&1; then
                echo "local-path"
            else
                echo "hostpath"
            fi
            ;;
        *)
            # Try to find the default storage class
            kubectl get storageclass -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}' 2>/dev/null || echo "default"
            ;;
    esac
}

get_node_resources() {
    local platform=$1
    
    case $platform in
        "gke")
            echo "requests_memory=256Mi requests_cpu=100m limits_memory=512Mi limits_cpu=500m"
            ;;
        "eks")
            echo "requests_memory=512Mi requests_cpu=250m limits_memory=1Gi limits_cpu=1000m"
            ;;
        "aks")
            echo "requests_memory=256Mi requests_cpu=100m limits_memory=512Mi limits_cpu=500m"
            ;;
        "local")
            echo "requests_memory=128Mi requests_cpu=50m limits_memory=256Mi limits_cpu=250m"
            ;;
        *)
            echo "requests_memory=256Mi requests_cpu=100m limits_memory=512Mi limits_cpu=500m"
            ;;
    esac
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    PLATFORM=$(detect_platform)
    STORAGE_CLASS=$(get_storage_class "$PLATFORM")
    RESOURCES=$(get_node_resources "$PLATFORM")
    
    echo "Platform: $PLATFORM" >&2
    echo "Storage Class: $STORAGE_CLASS" >&2
    echo "Resources: $RESOURCES" >&2
    
    # Output for scripting
    case "${1:-all}" in
        "platform")
            echo "$PLATFORM"
            ;;
        "storage")
            echo "$STORAGE_CLASS"
            ;;
        "resources")
            echo "$RESOURCES"
            ;;
        "all")
            echo "PLATFORM=$PLATFORM"
            echo "STORAGE_CLASS=$STORAGE_CLASS"
            echo "$RESOURCES"
            ;;
    esac
fi 