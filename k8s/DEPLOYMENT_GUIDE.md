# Comprehensive Deployment Guide - Falco AI Alert System v2.1.4

## 🚀 Quick Start - One Command Deployment

For most users, deployment is now a single command:

```bash
cd k8s
./install-dynamic.sh
```

This automatically detects your platform and deploys with optimal settings.

## 🌐 Supported Platforms

### ✅ **Cloud Platforms (Auto-Detected)**
- **Google Kubernetes Engine (GKE)** - Auto-configured storage classes and ARM64 support
- **Amazon Elastic Kubernetes Service (EKS)** - Graviton2/3 optimization
- **Azure Kubernetes Service (AKS)** - Ampere ARM64 instance support
- **DigitalOcean Kubernetes (DOKS)** - SSD storage optimization
- **IBM Cloud Kubernetes Service (IKS)** - Multi-zone configuration

### ✅ **Local Platforms (Auto-Detected)**
- **minikube** - Single-node development
- **kind** - Local testing clusters
- **k3s** - Lightweight Kubernetes
- **Docker Desktop** - Local development

## 🏗️ Multi-Architecture Support

### **Container Architecture Compatibility**
| Architecture | Cloud Support | Cost Benefits | Performance |
|--------------|---------------|---------------|-------------|
| **AMD64** | All providers | Standard pricing | High performance |
| **ARM64** | AWS Graviton, GCP Tau T2A, Azure Ampere | 20-40% cost savings | Excellent efficiency |

### **Cloud-Specific ARM64 Recommendations**

#### **AWS EKS - Cost-Optimized ARM64**
```bash
# Node group configuration
eksctl create nodegroup \
  --cluster=falco-cluster \
  --name=arm64-nodes \
  --instance-types=t4g.large,m6g.large,c6g.large \
  --nodes=2 --nodes-min=1 --nodes-max=5 \
  --node-arch=arm64
```

#### **GCP GKE - ARM64 Node Pool**
```bash
# Create ARM64 node pool
gcloud container node-pools create arm64-pool \
  --cluster=falco-cluster \
  --machine-type=t2a-standard-2 \
  --num-nodes=2 \
  --min-nodes=1 --max-nodes=5 \
  --enable-autoscaling
```

#### **Azure AKS - Ampere Instances**
```bash
# ARM64 node pool configuration
az aks nodepool add \
  --resource-group falco-rg \
  --cluster-name falco-cluster \
  --name arm64pool \
  --node-vm-size Standard_D2ps_v5 \
  --node-count 2 \
  --min-count 1 --max-count 5 \
  --enable-cluster-autoscaler
```

## 🎯 Environment-Specific Deployment

### **Production Deployment**
```bash
# Deploy with production optimizations
./install-dynamic.sh --environment production
```

**Features:**
- Horizontal Pod Autoscaling (2-10 replicas)
- Network policies for security
- Resource limits and requests
- Health checks and monitoring
- Persistent volume claims

### **Development Deployment**
```bash
# Deploy for development
./install-dynamic.sh --environment development
```

**Features:**
- Single replica for resource efficiency
- Relaxed security policies
- Debug logging enabled
- Local storage options

### **Manual Cloud Deployment**

#### **AWS EKS Setup**
```bash
# 1. Create EKS cluster
eksctl create cluster --name falco-cluster --region us-west-2 \
  --nodegroup-name standard-workers --node-type t3.medium \
  --nodes 3 --nodes-min 1 --nodes-max 4

# 2. Install required add-ons
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/aws/deploy.yaml

# 3. Deploy Falco AI
cd k8s && ./install.sh --cloud aws
```

#### **GCP GKE Setup**
```bash
# 1. Create GKE cluster
gcloud container clusters create falco-cluster \
  --zone us-central1-a --num-nodes 3 \
  --machine-type e2-standard-4 \
  --enable-autoscaling --min-nodes 1 --max-nodes 5

# 2. Get credentials
gcloud container clusters get-credentials falco-cluster --zone us-central1-a

# 3. Deploy Falco AI
cd k8s && ./install.sh --cloud gcp
```

#### **Azure AKS Setup**
```bash
# 1. Create resource group
az group create --name falco-rg --location eastus

# 2. Create AKS cluster
az aks create --resource-group falco-rg --name falco-cluster \
  --node-count 3 --node-vm-size Standard_D2s_v3 \
  --enable-cluster-autoscaler --min-count 1 --max-count 5

# 3. Get credentials
az aks get-credentials --resource-group falco-rg --name falco-cluster

# 4. Deploy Falco AI
cd k8s && ./install.sh --cloud azure
```

## 🔧 Resource Requirements

### **Development Environment**
- **Memory**: 8GB available RAM
- **CPU**: 2 cores minimum
- **Storage**: 15GB available storage
- **Model**: `phi3:mini` (default, fastest)

### **Production Environment**
- **Memory**: 10GB available RAM
- **CPU**: 4 cores minimum
- **Storage**: 20GB available storage
- **Model**: `phi3:mini` or `llama3.1:8b`

### **Enterprise Environment**
- **Memory**: 18GB+ available RAM
- **CPU**: 8+ cores
- **Storage**: 30GB+ available storage
- **Model**: `jimscard/whiterabbit-neo:latest` (cybersecurity-optimized)

## 📦 Component Architecture

### **Core Services**
- **falco-ai-alerts**: Main application (maddigsys/falco-ai-alerts:v2.1.4)
- **ollama**: Local LLM service for AI analysis
- **weaviate**: Vector database for enhanced search and analytics

### **Optional Components**
- **NGINX Ingress**: Load balancer and SSL termination
- **Cert-Manager**: Automatic TLS certificate management
- **Prometheus**: Metrics collection and monitoring

## 🔐 Security Configuration

### **Service Account and RBAC**
```yaml
# Minimal RBAC permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: falco-ai-alerts
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
```

### **Network Policies**
```yaml
# Restrict inter-pod communication
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: falco-ai-alerts-netpol
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: falco-ai-alerts
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: falco-ai-alerts
```

## 🚦 Troubleshooting

### **Common Issues**

#### **Pod Pending - Insufficient Resources**
```bash
# Check node resources
kubectl top nodes
kubectl describe nodes

# Solution: Add more nodes or reduce resource requests
kubectl patch deployment falco-ai-alerts -p '{"spec":{"template":{"spec":{"containers":[{"name":"falco-ai-alerts","resources":{"requests":{"memory":"512Mi","cpu":"250m"}}}]}}}}'
```

#### **Ollama Model Download Timeout**
```bash
# Check Ollama logs
kubectl logs deployment/ollama -f

# Increase timeout in configmap
kubectl patch configmap falco-ai-alerts-config -p '{"data":{"OLLAMA_TIMEOUT":"300"}}'
```

#### **Storage Class Issues**
```bash
# Check available storage classes
kubectl get storageclass

# Use dynamic storage detection
./detect-platform.sh
```

## 🔄 Upgrade Process

### **Rolling Update**
```bash
# Update to new version
kubectl set image deployment/falco-ai-alerts falco-ai-alerts=maddigsys/falco-ai-alerts:v2.1.4

# Monitor rollout
kubectl rollout status deployment/falco-ai-alerts

# Rollback if needed
kubectl rollout undo deployment/falco-ai-alerts
```

### **Blue-Green Deployment**
```bash
# Deploy new version alongside current
kubectl apply -f k8s/overlays/blue-green/

# Switch traffic
kubectl patch service falco-ai-alerts -p '{"spec":{"selector":{"version":"v2.1.4"}}}'
``` 