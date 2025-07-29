# Dynamic Multi-Platform Kubernetes Deployment Guide

## 🚀 Overview

The Falco AI Alert System now supports **dynamic, multi-platform deployments** that automatically detect your Kubernetes environment and configure optimal settings for:

- **Google Kubernetes Engine (GKE)**
- **Amazon Elastic Kubernetes Service (EKS)**
- **Azure Kubernetes Service (AKS)**
- **DigitalOcean Kubernetes (DOKS)**
- **IBM Cloud Kubernetes Service (IKS)**
- **Local Kubernetes (minikube, kind, k3s)**

## 🎯 Key Features

### ✅ **Automatic Platform Detection**
- Detects cloud provider automatically
- Selects optimal storage classes
- Configures appropriate resource limits
- Handles platform-specific optimizations

### ✅ **Dynamic Configuration Generation**
- Creates platform-specific Kustomization files
- Optimizes resource allocation per platform
- Handles storage class compatibility
- Generates environment-specific configs

### ✅ **One-Command Deployment**
- Single script for all platforms
- Automatic secret generation
- Deployment status monitoring
- Access information display

## 🛠️ Quick Start

### **1. One-Command Installation**
```bash
# Auto-detect platform and deploy
./install-dynamic.sh development

# Or specify actions individually
./install-dynamic.sh development detect    # Just detect platform
./install-dynamic.sh development generate  # Generate config
./install-dynamic.sh development deploy    # Deploy only
```

### **2. Manual Platform Detection**
```bash
# Check what platform you're on
./detect-platform.sh

# Get specific information
./detect-platform.sh platform  # Returns: gke, eks, aks, etc.
./detect-platform.sh storage   # Returns: standard-rwo, gp3, etc.
./detect-platform.sh resources # Returns: resource limits
```

### **3. Generate Platform-Specific Config**
```bash
# Generate config for current platform
./generate-config.sh generate development

# Generate for all environments
./generate-config.sh all
```

## 📋 Platform-Specific Configurations

### **Google Kubernetes Engine (GKE)**
```yaml
Platform: gke
Storage Class: premium-rwo (or standard-rwo)
Resources:
  requests: 256Mi RAM, 100m CPU
  limits: 512Mi RAM, 500m CPU
Optimizations:
  - GKE Autopilot compatible
  - Efficient resource allocation
  - Premium SSD storage
```

### **Amazon EKS**
```yaml
Platform: eks
Storage Class: gp3 (or gp2)
Resources:
  requests: 512Mi RAM, 250m CPU
  limits: 1Gi RAM, 1000m CPU
Optimizations:
  - AWS-optimized settings
  - GP3 storage for better performance
  - Higher resource allocation
```

### **Azure AKS**
```yaml
Platform: aks
Storage Class: managed-premium (or default)
Resources:
  requests: 256Mi RAM, 100m CPU
  limits: 512Mi RAM, 500m CPU
Optimizations:
  - Azure-optimized settings
  - Premium managed disks
  - Balanced resource allocation
```

### **Local Development**
```yaml
Platform: local
Storage Class: local-path (or hostpath)
Resources:
  requests: 128Mi RAM, 50m CPU
  limits: 256Mi RAM, 250m CPU
Optimizations:
  - Minimal resource usage
  - Local storage compatibility
  - Development-friendly settings
```

## 🔧 Advanced Usage

### **Custom Platform Detection**
```bash
# Add custom platform detection logic
vim k8s/detect-platform.sh

# Add new platform case
detect_platform() {
    # ... existing code ...
    
    # Check for custom platform
    if kubectl get nodes -o jsonpath='{.items[0].metadata.labels}' | grep -q "custom-platform"; then
        echo "custom"
        return 0
    fi
}
```

### **Custom Resource Profiles**
```bash
# Modify resource allocation
vim k8s/detect-platform.sh

get_node_resources() {
    case $platform in
        "custom")
            echo "requests_memory=1Gi requests_cpu=500m limits_memory=2Gi limits_cpu=2000m"
            ;;
    esac
}
```

### **Environment-Specific Overrides**
```bash
# Generate configs for different environments
./generate-config.sh generate development
./generate-config.sh generate staging
./generate-config.sh generate production

# Each gets platform-optimized settings
```

## 📁 File Structure

```
k8s/
├── detect-platform.sh           # Platform detection logic
├── generate-config.sh           # Dynamic config generation
├── install-dynamic.sh           # One-command installer
├── base/                        # Base Kubernetes manifests
├── overlays/
│   ├── development/            # Static development config
│   ├── development-auto/       # Auto-generated development config
│   ├── staging-auto/           # Auto-generated staging config
│   └── production-auto/        # Auto-generated production config
└── DYNAMIC_DEPLOYMENT_GUIDE.md # This guide
```

## 🚨 Troubleshooting

### **Platform Not Detected**
```bash
# Check node provider ID
kubectl get nodes -o jsonpath='{.items[0].spec.providerID}'

# Check available storage classes
kubectl get storageclass

# Force platform detection
PLATFORM=gke ./install-dynamic.sh development
```

### **Storage Class Issues**
```bash
# List available storage classes
kubectl get storageclass

# Check PVC status
kubectl get pvc -n falco-ai-alerts-development

# Manual storage class override
kubectl patch pvc dev-weaviate-pvc -n falco-ai-alerts-development -p '{"spec":{"storageClassName":"standard-rwo"}}'
```

### **Resource Constraints**
```bash
# Check node resources
kubectl describe nodes

# Adjust resource limits
vim k8s/detect-platform.sh  # Modify get_node_resources()

# Regenerate config
./generate-config.sh generate development
```

## 🔄 Migration from Static Config

### **From Existing Deployment**
```bash
# 1. Delete existing deployment
kubectl delete -k overlays/development/

# 2. Generate dynamic config
./install-dynamic.sh development generate

# 3. Deploy with dynamic config
./install-dynamic.sh development deploy
```

### **Keep Both Approaches**
```bash
# Static deployment
kubectl apply -k overlays/development/

# Dynamic deployment (different namespace)
./install-dynamic.sh development-auto
```

## 📊 Platform Comparison

| Platform | Storage Class | CPU Request | Memory Request | Optimizations |
|----------|---------------|-------------|----------------|---------------|
| GKE      | premium-rwo   | 100m        | 256Mi          | Autopilot ready |
| EKS      | gp3           | 250m        | 512Mi          | AWS optimized |
| AKS      | managed-premium| 100m       | 256Mi          | Azure optimized |
| DOKS     | do-block-storage| 100m      | 256Mi          | DO optimized |
| Local    | local-path    | 50m         | 128Mi          | Minimal resources |

## 🎯 Benefits

### **For Developers**
- ✅ No manual platform configuration
- ✅ Consistent deployment across environments
- ✅ Automatic resource optimization
- ✅ One command deployment

### **For DevOps**
- ✅ Platform-agnostic deployments
- ✅ Reduced configuration drift
- ✅ Automated best practices
- ✅ Easy multi-cloud support

### **For Operations**
- ✅ Optimal resource utilization
- ✅ Platform-specific optimizations
- ✅ Reduced troubleshooting
- ✅ Standardized deployments

## 🔮 Future Enhancements

- **Auto-scaling based on platform capabilities**
- **Network policy generation per platform**
- **Monitoring stack integration**
- **Backup strategy per platform**
- **Security policy automation**

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Run `./detect-platform.sh` to verify platform detection
3. Check generated configs in `overlays/*-auto/`
4. Review deployment logs: `kubectl logs -n falco-ai-alerts-development deployment/dev-falco-ai-alerts`

---

## 📋 **Post-Deployment Operations**

For comprehensive operational commands including port forwarding, UI access, log checking, and troubleshooting, see the **[Operational Commands Guide](OPERATIONAL_COMMANDS.md)**.

**Quick Access Example:**
```bash
# Development environment access
kubectl port-forward svc/dev-falco-ai-alerts 8080:8080 -n falco-ai-alerts-development &
open http://localhost:8080/

# Production environment access  
kubectl port-forward svc/prod-falco-ai-alerts 8080:8080 -n falco-ai-alerts &
open http://localhost:8080/
```

---

**🎉 Enjoy seamless multi-platform Kubernetes deployments!** 