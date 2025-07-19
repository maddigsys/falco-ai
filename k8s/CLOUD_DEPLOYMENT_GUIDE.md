# Cloud Deployment Guide - Falco AI Alert System v2.1.0

This guide addresses specific constraints and considerations for deploying the Falco AI Alert System on major cloud Kubernetes platforms with **multi-architecture support** (AMD64/ARM64).

## 🏗️ **Multi-Architecture Support (NEW in v2.1.0)**

### **Container Architecture Compatibility**
| Architecture | Cloud Support | Cost Benefits | Performance |
|--------------|---------------|---------------|-------------|
| **AMD64** | All providers | Standard pricing | High performance |
| **ARM64** | AWS Graviton2/3, GCP Tau T2A, Azure Ampere | 20-40% cost savings | Excellent efficiency |

### **Recommended Instance Types by Cloud**

#### **AWS EKS - ARM64 (Cost-Optimized)**
```bash
# Node group configuration for ARM64
eksctl create nodegroup \
  --cluster=falco-cluster \
  --name=arm64-nodes \
  --instance-types=t4g.large,m6g.large,c6g.large \
  --nodes=2 \
  --nodes-min=1 \
  --nodes-max=5 \
  --node-arch=arm64
```

#### **GCP GKE - ARM64 (Cost-Optimized)**
```bash
# Node pool configuration for ARM64
gcloud container node-pools create arm64-pool \
  --cluster=falco-cluster \
  --machine-type=t2a-standard-2 \
  --num-nodes=2 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=5
```

#### **Azure AKS - ARM64 (Cost-Optimized)**
```bash
# Node pool configuration for ARM64
az aks nodepool add \
  --cluster-name falco-cluster \
  --resource-group falco-rg \
  --name arm64pool \
  --node-vm-size Standard_D2ps_v5 \
  --node-count 2 \
  --min-count 1 \
  --max-count 5 \
  --enable-cluster-autoscaler
```

### **Deployment Commands by Architecture**

#### **Multi-Architecture (Recommended)**
```bash
# Kubernetes automatically selects the correct architecture
kubectl apply -k overlays/eks/    # AWS EKS
kubectl apply -k overlays/gke/    # Google GKE
kubectl apply -k overlays/aks/    # Azure AKS
```

#### **Force Specific Architecture (Advanced)**
```bash
# Force AMD64 deployment
kubectl patch deployment prod-falco-ai-alerts -p '{"spec":{"template":{"spec":{"nodeSelector":{"kubernetes.io/arch":"amd64"}}}}}'

# Force ARM64 deployment  
kubectl patch deployment prod-falco-ai-alerts -p '{"spec":{"template":{"spec":{"nodeSelector":{"kubernetes.io/arch":"arm64"}}}}}'
```

## 🚨 **Critical Cloud Deployment Constraints**

### **Overview of Platform-Specific Issues**
| Component | EKS | GKE | AKS | Impact |
|-----------|-----|-----|-----|---------|
| Storage Classes | `gp2` default (slow) | `standard` (slow) | `default` (slow) | ❌ **High** - AI model loading |
| Ingress Controller | Not installed | Not installed | Not installed | ❌ **Critical** - External access |
| Network Policies | Not supported | Supported | Supported | ⚠️ **Medium** - Security |
| Load Balancer | ALB/NLB | GLB | Azure LB | ✅ **Low** - Works with ingress |
| Node Sizing | Instance types | Machine types | VM sizes | ❌ **Critical** - AI inference |
| Metrics Server | Not installed | Installed | Installed | ⚠️ **Medium** - HPA |
| Cert Manager | Not installed | Not installed | Not installed | ⚠️ **Medium** - TLS |

---

## 🛠️ **Platform-Specific Solutions**

### **1. AWS EKS**

#### **Required Pre-requisites**
```bash
# 1. Install AWS Load Balancer Controller
kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller/crds?ref=master"

# 2. Install Metrics Server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 3. Create IAM role for AWS Load Balancer Controller
eksctl create iamserviceaccount \
  --cluster=<cluster-name> \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name=AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess \
  --approve
```

#### **EKS-Specific Deployment**
```bash
# Deploy with EKS optimizations
kubectl apply -k overlays/eks/
```

#### **Node Requirements**
```yaml
# Recommended node group configuration
NodeGroups:
  - name: falco-ai-nodes
    instanceTypes: ["t3.xlarge", "t3.2xlarge"]  # 16GB+ RAM
    minSize: 2
    maxSize: 10
    desiredCapacity: 3
    volumeSize: 100
    volumeType: gp3
    tags:
      component: "falco-ai-workloads"
```

#### **Storage Optimization**
```yaml
# Create optimized storage class
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: falco-gp3-fast
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
allowVolumeExpansion: true
```

---

### **2. Google GKE**

#### **Required Pre-requisites**
```bash
# 1. Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com

# 2. Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# 3. Install Cert-Manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

#### **GKE-Specific Configuration**
```yaml
# k8s/overlays/gke/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base
  - hpa.yaml

patches:
  # GKE SSD storage class
  - target:
      kind: PersistentVolumeClaim
    patch: |-
      - op: add
        path: /spec/storageClassName
        value: "ssd"
  
  # GKE LoadBalancer for webhook
  - target:
      kind: Service
      name: falco-ai-alerts
    patch: |-
      - op: replace
        path: /spec/type
        value: LoadBalancer
      - op: add
        path: /metadata/annotations
        value:
          cloud.google.com/load-balancer-type: "External"
```

#### **Node Pool Configuration**
```bash
# Create AI-optimized node pool
gcloud container node-pools create falco-ai-pool \
  --cluster=<cluster-name> \
  --zone=<zone> \
  --machine-type=n1-standard-4 \
  --num-nodes=2 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=5 \
  --disk-size=100GB \
  --disk-type=pd-ssd \
  --node-labels=workload=ai-inference
```

---

### **3. Azure AKS**

#### **Required Pre-requisites**
```bash
# 1. Install NGINX Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx

# 2. Install Cert-Manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

#### **AKS-Specific Configuration**
```yaml
# k8s/overlays/aks/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base
  - hpa.yaml

patches:
  # Azure Premium SSD storage
  - target:
      kind: PersistentVolumeClaim
    patch: |-
      - op: add
        path: /spec/storageClassName
        value: "managed-premium"
  
  # Azure-specific node selector
  - target:
      kind: Deployment
      name: ollama
    patch: |-
      - op: add
        path: /spec/template/spec/nodeSelector
        value:
          kubernetes.io/os: "linux"
          node.kubernetes.io/instance-type: "Standard_D4s_v3"
```

#### **Node Pool Configuration**
```bash
# Create AI-optimized node pool
az aks nodepool add \
  --resource-group <resource-group> \
  --cluster-name <cluster-name> \
  --name aipool \
  --node-count 2 \
  --min-count 1 \
  --max-count 5 \
  --node-vm-size Standard_D4s_v3 \
  --enable-cluster-autoscaler \
  --node-osdisk-size 100 \
  --node-osdisk-type Premium_LRS
```

---

## 📊 **Resource Planning by Cloud Provider**

### **⚠️ CRITICAL: Minimum Resource Requirements**

**For AI Model Inference (Ollama):**
- **Memory**: 6-8GB RAM (tinyllama) to 16GB+ (cybersecurity models)
- **CPU**: 2+ cores (4+ recommended for production)
- **Storage**: 15-30GB SSD (fast I/O required for model loading)

**Node types below these specifications will result in deployment failures.**

### **Recommended Node Configurations**

#### **AWS EKS**
| Use Case | Instance Type | vCPU | RAM | Storage | Cost/Month* | AI Model Support |
|----------|---------------|------|-----|---------|-------------|------------------|
| Development | t3.large | 2 | 8GB | 50GB | ~$60 | ✅ tinyllama only |
| Production | t3.xlarge | 4 | 16GB | 100GB | ~$120 | ✅ All models |
| AI-Optimized | c5.2xlarge | 8 | 16GB | 100GB | ~$250 | ✅ All + fast inference |

#### **Google GKE**
| Use Case | Machine Type | vCPU | RAM | Storage | Cost/Month* | AI Model Support |
|----------|--------------|------|-----|---------|-------------|------------------|
| Development | n1-standard-2 | 2 | 7.5GB | 50GB | ~$55 | ⚠️ Insufficient RAM |
| Production | n1-standard-4 | 4 | 15GB | 100GB | ~$110 | ✅ All models |
| AI-Optimized | n1-highmem-4 | 4 | 26GB | 100GB | ~$160 | ✅ All + fast inference |

#### **Azure AKS**
| Use Case | VM Size | vCPU | RAM | Storage | Cost/Month* | AI Model Support |
|----------|---------|------|-----|---------|-------------|------------------|
| Development | Standard_D2s_v3 | 2 | 8GB | 50GB | ~$65 | ✅ tinyllama only |
| Production | Standard_D4s_v3 | 4 | 16GB | 100GB | ~$130 | ✅ All models |
| AI-Optimized | Standard_D4s_v4 | 4 | 16GB | 100GB | ~$125 | ✅ All + fast inference |

*Approximate costs in US regions, subject to change*

### **🚨 Resource Validation Before Deployment**

**Always validate your cluster resources before deployment:**

```bash
# Check available cluster resources
kubectl top nodes
kubectl describe nodes | grep -A5 "Allocated resources"

# Verify storage classes
kubectl get storageclass
```

**Signs of Insufficient Resources:**
- ❌ **Pods stuck in Pending**: `kubectl get pods -n falco-ai-alerts`
- ❌ **OOMKilled events**: `kubectl get events --sort-by='.lastTimestamp'`
- ❌ **Model download timeouts**: Check init container logs
- ❌ **Slow AI inference** (>60s): Indicates CPU starvation

**Resource Failure Recovery:**
```bash
# Scale up node groups (platform-specific)
# AWS EKS
eksctl scale nodegroup --cluster=<name> --name=<nodegroup> --nodes=<count>

# Upgrade node types
eksctl create nodegroup --cluster=<name> --node-type=t3.xlarge
```

---

## 🔧 **Common Issues & Solutions**

### **1. AI Model Download Timeouts**
**Problem**: Large models (>5GB) failing to download within init container timeout
**Solution**: 
```yaml
# Increase init container timeout
spec:
  template:
    spec:
      initContainers:
      - name: model-downloader
        args:
        - timeout=3600  # 1 hour for large models
```

### **2. Persistent Volume Performance**
**Problem**: Slow model loading and inference
**Solution**:
```yaml
# Use high-performance storage
spec:
  storageClassName: "fast-ssd"  # Cloud-specific fast storage
  resources:
    requests:
      storage: 50Gi  # Larger for better IOPS allocation
```

### **3. Load Balancer SSL/TLS Issues**
**Problem**: Certificate management complexity
**Solution**:
```yaml
# Use cloud-native certificate management
metadata:
  annotations:
    # AWS
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: "arn:aws:acm:..."
    # Azure
    service.beta.kubernetes.io/azure-load-balancer-certificate: "cert-name"
    # GCP
    cloud.google.com/load-balancer-type: "External"
```

### **4. Network Policies Not Working**
**Problem**: Security policies failing to apply
**Solution**:
```bash
# Check CNI support
kubectl get nodes -o wide

# Install compatible CNI if needed
# For EKS: Install Calico
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/calico.yaml
```

---

## 🚀 **Quick Start by Platform**

### **EKS Deployment**
```bash
# 1. Pre-requisites
./scripts/setup-eks-prereqs.sh

# 2. Deploy
kubectl apply -k k8s/overlays/eks/

# 3. Get LoadBalancer URL
kubectl get ingress -n falco-ai-alerts
```

### **GKE Deployment**
```bash
# 1. Pre-requisites
./scripts/setup-gke-prereqs.sh

# 2. Deploy
kubectl apply -k k8s/overlays/gke/

# 3. Get LoadBalancer IP
kubectl get svc falco-ai-alerts -n falco-ai-alerts
```

### **AKS Deployment**
```bash
# 1. Pre-requisites
./scripts/setup-aks-prereqs.sh

# 2. Deploy
kubectl apply -k k8s/overlays/aks/

# 3. Get LoadBalancer IP
kubectl get svc falco-ai-alerts -n falco-ai-alerts
```

---

## 🔒 **Security Considerations**

### **Cloud-Specific Security**
- **EKS**: Use AWS Security Groups for Pods instead of NetworkPolicy
- **GKE**: Enable Workload Identity for secure access to GCP services
- **AKS**: Use Azure AD integration for RBAC

### **Network Security**
```yaml
# Cloud-agnostic security annotations
metadata:
  annotations:
    # Rate limiting
    nginx.ingress.kubernetes.io/rate-limit: "10"
    # IP whitelisting
    nginx.ingress.kubernetes.io/whitelist-source-range: "10.0.0.0/8"
    # DDoS protection
    nginx.ingress.kubernetes.io/limit-connections: "5"
```

---

## 📈 **Monitoring & Observability**

### **Cloud-Native Monitoring**
```yaml
# Prometheus ServiceMonitor
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: falco-ai-alerts
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: falco-ai-alerts
  endpoints:
  - port: http
    path: /metrics
```

### **Cloud Provider Integration**
- **AWS**: CloudWatch Container Insights
- **GCP**: Cloud Monitoring and Logging
- **Azure**: Container Insights and Log Analytics

---

## 🎯 **Best Practices**

### **1. Cost Optimization**
- Use spot instances for non-critical workloads
- Implement cluster autoscaling
- Set appropriate resource requests/limits
- Use regional persistent disks where available

### **2. High Availability**
- Deploy across multiple availability zones
- Use pod disruption budgets
- Implement proper health checks
- Configure backup strategies

### **3. Performance Tuning**
- Place AI workloads on dedicated nodes
- Use SSD storage for model storage
- Implement proper CPU/memory limits
- Consider GPU nodes for large models

---

## 🆘 **Troubleshooting**

### **Common Cloud Issues**
| Issue | Symptom | Solution |
|-------|---------|----------|
| Storage not mounting | Pods stuck in pending | Check storage class exists |
| LoadBalancer not working | External IP shows `<pending>` | Verify cloud provider permissions |
| High inference latency | AI responses >30s | Upgrade node type or add GPU |
| Network policies blocking | Pods can't communicate | Check CNI compatibility |
| Certificate errors | SSL/TLS warnings | Verify cert-manager installation |

For detailed troubleshooting, see the platform-specific sections above.

---

## 📞 **Support Matrix**

| Platform | Supported | Testing Status | Recommended |
|----------|-----------|----------------|-------------|
| **EKS** | ✅ Full | ✅ Tested | ✅ Yes |
| **GKE** | ✅ Full | ⚠️ Limited | ✅ Yes |
| **AKS** | ✅ Full | ⚠️ Limited | ✅ Yes |
| **DigitalOcean** | ⚠️ Basic | ❌ Untested | ⚠️ Community |
| **Linode** | ⚠️ Basic | ❌ Untested | ⚠️ Community |

**Legend:**
- ✅ **Full Support**: Extensively tested, documented, and supported
- ⚠️ **Basic Support**: Should work but may require adjustments
- ❌ **No Support**: Not tested, may have compatibility issues 