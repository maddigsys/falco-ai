# Performance Optimization Guide - Falco AI Alert System v2.1.12

## 🎯 Model Selection & Resource Planning

### **Model Recommendations by Use Case**

#### **Development/Testing** ✅ **DEFAULT**
**Recommended Model**: `phi3:mini`
- **Memory Required**: 3-4GB RAM (very efficient)
- **Storage**: ~2.3GB
- **Response Quality**: Excellent for general security analysis
- **Speed**: Ultra-fast inference (2-8 seconds)
- **Use Case**: Default for all environments, fastest option
- **Timeout Recommendation**: 30 seconds

#### **Production (Balanced Performance)** ⚡ **UPGRADE OPTION**
**Performance Model**: `llama3.1:8b`
- **Memory Required**: 6-8GB RAM
- **Storage**: ~4.9GB
- **Response Quality**: Enhanced analysis with larger context
- **Speed**: Fast inference (5-15 seconds)
- **Reliability**: Excellent balance of speed and capability
- **Timeout Recommendation**: 45 seconds

#### **Production (Cybersecurity-Specialized)** 🛡️ **PREMIUM OPTION**
**Cybersecurity Model**: `jimscard/whiterabbit-neo:latest` (13B)
- **Memory Required**: 14-16GB RAM
- **Storage**: ~13GB
- **Response Quality**: Specialized cybersecurity analysis
- **Speed**: Moderate inference (15-45 seconds)
- **Use Case**: Maximum security analysis capability
- **Timeout Recommendation**: 90 seconds

### **Model Configuration Matrix**

| Environment | Memory | Model | Timeout | Parallel | Keep-Alive |
|-------------|--------|-------|---------|----------|------------|
| **Development** | 4GB | phi3:mini | 30s | 1 | 5m |
| **Production** | 8GB | llama3.1:8b | 45s | 2 | 10m |
| **Enterprise** | 16GB | whiterabbit-neo | 90s | 1 | 15m |
| **Cloud ARM64** | 6GB | phi3:mini | 30s | 2 | 10m |

## ⚙️ Resource Optimization

### **Kubernetes Resource Allocation**

#### **Development Environment**
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

#### **Production Environment**
```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

#### **Enterprise Environment**
```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "8Gi"
    cpu: "4000m"
```

### **Ollama-Specific Optimization**

#### **Memory Management**
```yaml
# Ollama deployment optimization
env:
- name: OLLAMA_NUM_PARALLEL
  value: "2"  # Number of parallel requests
- name: OLLAMA_MAX_LOADED_MODELS
  value: "1"  # Keep only one model loaded
- name: OLLAMA_KEEP_ALIVE
  value: "10m"  # Keep model in memory for 10 minutes
- name: OLLAMA_HOST
  value: "0.0.0.0"
```

#### **Storage Optimization**
```yaml
# Use faster storage classes for model loading
spec:
  storageClassName: "fast-ssd"
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
```

## 🚀 Performance Tuning

### **Application-Level Optimizations**

#### **Timeout Configuration**
```bash
# Model-specific timeout settings
kubectl patch configmap falco-ai-alerts-config -n falco-ai-alerts -p '{"data":{
  "OLLAMA_TIMEOUT": "30",           # phi3:mini
  "AI_REQUEST_TIMEOUT": "45",       # llama3.1:8b
  "OLLAMA_KEEP_ALIVE": "10"         # Keep model loaded for 10 minutes
}}'
```

#### **Connection Pool Optimization**
```bash
# Optimize HTTP connections
kubectl patch configmap falco-ai-alerts-config -n falco-ai-alerts -p '{"data":{
  "OLLAMA_PARALLEL": "2",           # Parallel requests
  "MAX_CONNECTIONS": "10",          # Connection pool size
  "CONNECTION_TIMEOUT": "30"        # Connection timeout
}}'
```

### **Model-Specific Optimizations**

#### **Fast Response Models** (phi3:mini, tinyllama)
```yaml
env:
- name: OLLAMA_MODEL_NAME
  value: "phi3:mini"
- name: OLLAMA_TIMEOUT
  value: "30"
- name: OLLAMA_PARALLEL
  value: "2"
- name: OLLAMA_KEEP_ALIVE
  value: "5m"
```

#### **Balanced Models** (llama3.1:8b)
```yaml
env:
- name: OLLAMA_MODEL_NAME
  value: "llama3.1:8b"
- name: OLLAMA_TIMEOUT
  value: "45"
- name: OLLAMA_PARALLEL
  value: "1"
- name: OLLAMA_KEEP_ALIVE
  value: "10m"
```

#### **Specialized Models** (whiterabbit-neo)
```yaml
env:
- name: OLLAMA_MODEL_NAME
  value: "jimscard/whiterabbit-neo:latest"
- name: OLLAMA_TIMEOUT
  value: "90"
- name: OLLAMA_PARALLEL
  value: "1"
- name: OLLAMA_KEEP_ALIVE
  value: "15m"
```

## 📊 Monitoring & Metrics

### **Performance Monitoring**
```bash
# Monitor response times
kubectl exec deployment/falco-ai-alerts -n falco-ai-alerts -- curl -s http://localhost:8080/metrics | grep response_time

# Monitor memory usage
kubectl top pods -n falco-ai-alerts

# Monitor Ollama performance
kubectl exec deployment/ollama -n falco-ai-alerts -- curl -s http://localhost:11434/api/ps
```

### **Resource Utilization Metrics**
```bash
# CPU utilization
kubectl exec deployment/falco-ai-alerts -n falco-ai-alerts -- cat /proc/loadavg

# Memory usage patterns
kubectl exec deployment/falco-ai-alerts -n falco-ai-alerts -- free -h

# Disk I/O for model loading
kubectl exec deployment/ollama -n falco-ai-alerts -- iostat -x 1 5
```

## 🔧 Environment-Specific Optimization

### **Cloud Platform Optimization**

#### **AWS EKS Optimization**
```bash
# Use Graviton2/3 instances for cost savings
instanceTypes: [t4g.large, m6g.large, c6g.large]

# Use gp3 storage for better performance
storageClassName: gp3
```

#### **GCP GKE Optimization**
```bash
# Use Tau T2A ARM instances
machineType: t2a-standard-2

# Use SSD persistent disks
storageClassName: fast-ssd
```

#### **Azure AKS Optimization**
```bash
# Use Ampere-based instances
vmSize: Standard_D2ps_v5

# Use Premium SSD
storageClassName: managed-premium
```

### **Local Development Optimization**

#### **minikube Configuration**
```bash
# Start with optimal resources
minikube start --memory=8192 --cpus=4 --disk-size=20g

# Enable required add-ons
minikube addons enable metrics-server
minikube addons enable ingress
```

#### **Docker Desktop Configuration**
```bash
# Configure Docker Desktop resources
# Memory: 8GB minimum
# CPU: 4 cores minimum
# Disk: 20GB minimum
```

## 📈 Scaling Strategies

### **Horizontal Pod Autoscaling (HPA)**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: falco-ai-alerts-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: falco-ai-alerts
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### **Vertical Pod Autoscaling (VPA)**
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: falco-ai-alerts-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: falco-ai-alerts
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: falco-ai-alerts
      maxAllowed:
        memory: "8Gi"
        cpu: "4000m"
```

## 🎛️ Advanced Configuration

### **Model Caching Strategy**
```bash
# Pre-load models during initialization
kubectl patch job ollama-model-init -n falco-ai-alerts -p '{"spec":{"template":{"spec":{"containers":[{"name":"model-downloader","env":[{"name":"PRELOAD_MODELS","value":"phi3:mini,llama3.1:8b"}]}]}}}}'
```

### **Request Prioritization**
```yaml
# Priority classes for different workload types
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority-ai
value: 1000
globalDefault: false
description: "High priority for AI processing workloads"
```

### **Network Optimization**
```yaml
# Service mesh configuration for better networking
apiVersion: v1
kind: Service
metadata:
  name: falco-ai-alerts
  annotations:
    service.alpha.kubernetes.io/tolerate-unready-endpoints: "true"
spec:
  publishNotReadyAddresses: true
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 300
```

## 📋 Performance Benchmarking

### **Load Testing**
```bash
# Simple load test
kubectl run load-test --image=busybox --rm -it -- sh -c "
  while true; do
    wget -qO- http://falco-ai-alerts:8080/health
    sleep 1
  done
"

# Advanced load testing with hey
kubectl run hey --image=williamyeh/hey --rm -it -- hey -n 1000 -c 10 http://falco-ai-alerts:8080/api/test
```

### **Baseline Performance Metrics**

| Model | Response Time | Memory Usage | CPU Usage | Concurrent Requests |
|-------|--------------|--------------|-----------|-------------------|
| phi3:mini | 2-8s | 3-4GB | 0.5-1 CPU | 2-4 |
| llama3.1:8b | 5-15s | 6-8GB | 1-2 CPU | 1-2 |
| whiterabbit-neo | 15-45s | 14-16GB | 2-4 CPU | 1 |

### **Optimization Checklist**

#### **✅ Resource Optimization**
- [ ] Right-sized memory allocation
- [ ] Appropriate CPU limits
- [ ] Fast storage class selection
- [ ] Network optimization

#### **✅ Model Optimization**
- [ ] Model selection appropriate for use case
- [ ] Timeout configuration optimized
- [ ] Keep-alive settings tuned
- [ ] Parallel processing configured

#### **✅ Kubernetes Optimization**
- [ ] HPA configured for scaling
- [ ] Resource requests/limits set
- [ ] Health checks configured
- [ ] Monitoring enabled

#### **✅ Application Optimization**
- [ ] Connection pooling enabled
- [ ] Caching strategy implemented
- [ ] Request prioritization configured
- [ ] Performance monitoring active 