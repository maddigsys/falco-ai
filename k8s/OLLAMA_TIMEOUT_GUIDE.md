# Ollama Timeout Configuration Guide

This guide explains how to configure Ollama timeout settings for different models and deployment environments.

## 🕐 **Model-Specific Timeout Recommendations**

### **Quick Reference Table**
| Model | Size | Expected Response Time | Recommended Timeout | Use Case |
|-------|------|----------------------|-------------------|----------|
| `tinyllama` | 637MB | 3-10s | 30s | ✅ **Default** - Ultra-fast, reliable |
| `phi3:mini` | 2.3GB | 5-15s | 45s | ⚡ **Fast** - Balanced performance |
| `llama3.1:8b` | 4.9GB | 10-30s | 60s | 🔄 **Production** - Enhanced analysis |
| `jimscard/whiterabbit-neo` | 13GB | 20-60s | 90s | 🛡️ **Cybersecurity** - Specialized |
| `llama3.1:70b` | 40GB | 60-180s | 300s | 🏢 **Enterprise** - Maximum capability |

## ⚙️ **Configuration Methods**

### **Method 1: Environment-Specific Overlays (Recommended)**

#### **Development Environment**
```yaml
# k8s/overlays/development/kustomization.yaml
patches:
  - target:
      kind: ConfigMap
      name: falco-ai-alerts-config
    patch: |-
      - op: replace
        path: /data/OLLAMA_TIMEOUT
        value: "30"  # Fast timeout for development
      - op: replace
        path: /data/AI_REQUEST_TIMEOUT
        value: "30"
```

#### **Production Environment**
```yaml
# k8s/overlays/production/kustomization.yaml
patches:
  - target:
      kind: ConfigMap
      name: falco-ai-alerts-config
    patch: |-
      - op: replace
        path: /data/OLLAMA_TIMEOUT
        value: "60"  # Extended for production models
      - op: replace
        path: /data/AI_REQUEST_TIMEOUT
        value: "60"
```

#### **Cloud Environment (EKS/GKE/AKS)**
```yaml
# k8s/overlays/eks/kustomization.yaml
patches:
  - target:
      kind: ConfigMap
      name: falco-ai-alerts-config
    patch: |-
      - op: replace
        path: /data/OLLAMA_TIMEOUT
        value: "45"  # Balanced for cloud infrastructure
      - op: replace
        path: /data/AI_REQUEST_TIMEOUT
        value: "45"
```

### **Method 2: Direct ConfigMap Edit**

```bash
# Edit ConfigMap directly
kubectl edit configmap falco-ai-alerts-config -n falco-ai-alerts

# Or patch specific values
kubectl patch configmap falco-ai-alerts-config -n falco-ai-alerts \
  --patch '{"data":{"OLLAMA_TIMEOUT":"90","AI_REQUEST_TIMEOUT":"90"}}'
```

### **Method 3: Ollama Deployment Configuration**

```yaml
# k8s/base/ollama-deployment.yaml
env:
- name: OLLAMA_REQUEST_TIMEOUT
  value: "60"  # Ollama server timeout
- name: OLLAMA_KEEP_ALIVE
  value: "10m"  # Keep model in memory
- name: OLLAMA_NUM_PARALLEL
  value: "1"   # Parallel requests (adjust for resources)
```

## 🔧 **Configuration Parameters Explained**

### **Application-Level Timeouts**
- **`OLLAMA_TIMEOUT`**: Python requests timeout to Ollama API
- **`AI_REQUEST_TIMEOUT`**: Overall application timeout for AI requests
- **Rule**: Keep these values equal or OLLAMA_TIMEOUT slightly higher

### **Ollama Server Timeouts**
- **`OLLAMA_REQUEST_TIMEOUT`**: Server-side request timeout
- **`OLLAMA_KEEP_ALIVE`**: How long to keep model loaded in memory
- **`OLLAMA_NUM_PARALLEL`**: Number of concurrent requests (resource-dependent)

## 📊 **Environment-Specific Configurations**

### **Development Setup**
```yaml
# Optimized for fast iteration and testing
OLLAMA_TIMEOUT: "30"           # Quick feedback
AI_REQUEST_TIMEOUT: "30"       # Fast failure detection
OLLAMA_KEEP_ALIVE: "5m"        # Short memory retention
OLLAMA_NUM_PARALLEL: "1"       # Single request processing
```

### **Production Setup**
```yaml
# Optimized for reliability and performance
OLLAMA_TIMEOUT: "60"           # Allow for larger models
AI_REQUEST_TIMEOUT: "60"       # Production reliability
OLLAMA_KEEP_ALIVE: "10m"       # Extended memory retention
OLLAMA_NUM_PARALLEL: "2"       # Multiple requests (if resources allow)
```

### **High-Performance Setup**
```yaml
# Optimized for cybersecurity models and batch processing
OLLAMA_TIMEOUT: "90"           # Extended for complex analysis
AI_REQUEST_TIMEOUT: "90"       # Long-running analysis
OLLAMA_KEEP_ALIVE: "15m"       # Keep large models loaded
OLLAMA_NUM_PARALLEL: "1"       # Focus on single quality response
```

## 🚀 **Model Upgrade Workflow**

### **Step 1: Check Current Model**
```bash
# Check what model is currently configured
kubectl get configmap falco-ai-alerts-config -n falco-ai-alerts -o yaml | grep MODEL_NAME

# Check available models in Ollama
kubectl exec -it deployment/prod-ollama -n falco-ai-alerts -- ollama list
```

### **Step 2: Upgrade Timeout Before Model Change**
```bash
# Example: Upgrading from tinyllama to llama3.1:8b
kubectl patch configmap falco-ai-alerts-config -n falco-ai-alerts \
  --patch '{"data":{"OLLAMA_TIMEOUT":"60","AI_REQUEST_TIMEOUT":"60"}}'
```

### **Step 3: Update Model Configuration**
```bash
# Update to new model
kubectl patch configmap falco-ai-alerts-config -n falco-ai-alerts \
  --patch '{"data":{"MODEL_NAME":"llama3.1:8b","OLLAMA_MODEL_NAME":"llama3.1:8b"}}'
```

### **Step 4: Restart Application**
```bash
# Restart to pick up new configuration
kubectl rollout restart deployment/prod-falco-ai-alerts -n falco-ai-alerts
kubectl rollout restart deployment/prod-ollama -n falco-ai-alerts
```

## 🛠️ **Troubleshooting Timeout Issues**

### **Symptoms of Incorrect Timeouts**

#### **Timeout Too Short**
```
❌ Symptoms:
- "Read timed out" errors in logs
- Frequent AI analysis failures
- Fast responses but incomplete analysis

✅ Solutions:
- Increase OLLAMA_TIMEOUT by 30s
- Monitor actual response times
- Consider smaller model if timeouts persist
```

#### **Timeout Too Long**
```
❌ Symptoms:
- Alerts delayed for minutes
- High resource usage
- User interface unresponsive

✅ Solutions:
- Decrease timeout to 2x expected response time
- Upgrade to faster model
- Add resource limits
```

### **Diagnostic Commands**

```bash
# Check current timeout configuration
kubectl get configmap falco-ai-alerts-config -n falco-ai-alerts -o jsonpath='{.data.OLLAMA_TIMEOUT}'

# Monitor actual response times
kubectl logs -f deployment/prod-falco-ai-alerts -n falco-ai-alerts | grep "Ollama response"

# Test AI endpoint directly
kubectl exec -it deployment/prod-ollama -n falco-ai-alerts -- \
  curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"tinyllama","prompt":"test","stream":false}' \
  --max-time 30
```

## 📈 **Performance Optimization**

### **Memory vs Timeout Trade-offs**
- **Higher OLLAMA_KEEP_ALIVE**: Faster subsequent requests, higher memory usage
- **Lower OLLAMA_KEEP_ALIVE**: Lower memory usage, slower model loading
- **Sweet Spot**: 5-10 minutes for most environments

### **Parallel Processing**
```yaml
# For high-volume environments with sufficient resources
OLLAMA_NUM_PARALLEL: "2"  # Allow 2 concurrent requests
# Requires: 2x memory allocation in deployment
```

### **Cloud-Specific Optimizations**

#### **AWS EKS**
```yaml
# Optimized for EKS infrastructure latency
OLLAMA_TIMEOUT: "45"           # Account for cloud latency
OLLAMA_KEEP_ALIVE: "8m"        # Balance cost vs performance
```

#### **On-Premises**
```yaml
# Optimized for dedicated hardware
OLLAMA_TIMEOUT: "30"           # Lower latency
OLLAMA_KEEP_ALIVE: "15m"       # Utilize available memory
```

## 🔄 **Dynamic Timeout Adjustment**

### **Runtime Monitoring Script**
```bash
#!/bin/bash
# Monitor and auto-adjust timeouts based on response times

NAMESPACE="falco-ai-alerts"
CONFIGMAP="falco-ai-alerts-config"

while true; do
  # Get average response time from logs (last 10 responses)
  AVG_TIME=$(kubectl logs deployment/prod-falco-ai-alerts -n $NAMESPACE --tail=100 | \
    grep "Ollama response" | tail -10 | \
    awk '{print $NF}' | sed 's/s//' | \
    awk '{sum+=$1} END {print sum/NR}')
  
  if (( $(echo "$AVG_TIME > 25" | bc -l) )); then
    echo "High response time detected: ${AVG_TIME}s, increasing timeout"
    kubectl patch configmap $CONFIGMAP -n $NAMESPACE \
      --patch '{"data":{"OLLAMA_TIMEOUT":"60"}}'
  fi
  
  sleep 300  # Check every 5 minutes
done
```

## 📋 **Best Practices Summary**

1. **Start Conservative**: Begin with recommended timeouts for your model
2. **Monitor Actual Performance**: Track real response times vs timeout settings  
3. **Environment-Specific**: Use different timeouts for dev/staging/production
4. **Model-Aware**: Adjust timeouts when upgrading models
5. **Cloud Considerations**: Add buffer for cloud infrastructure latency
6. **Resource Correlation**: Higher timeouts require adequate CPU/memory
7. **Graceful Degradation**: Ensure system works even with timeout failures
8. **Documentation**: Document timeout changes with reasoning

## 🎯 **Quick Configuration Commands**

```bash
# Tinyllama (default, fast)
kubectl patch configmap falco-ai-alerts-config -n falco-ai-alerts \
  --patch '{"data":{"OLLAMA_TIMEOUT":"30","AI_REQUEST_TIMEOUT":"30"}}'

# Phi3:mini (balanced)
kubectl patch configmap falco-ai-alerts-config -n falco-ai-alerts \
  --patch '{"data":{"OLLAMA_TIMEOUT":"45","AI_REQUEST_TIMEOUT":"45"}}'

# Llama3.1:8b (production)
kubectl patch configmap falco-ai-alerts-config -n falco-ai-alerts \
  --patch '{"data":{"OLLAMA_TIMEOUT":"60","AI_REQUEST_TIMEOUT":"60"}}'

# Cybersecurity models (specialized)
kubectl patch configmap falco-ai-alerts-config -n falco-ai-alerts \
  --patch '{"data":{"OLLAMA_TIMEOUT":"90","AI_REQUEST_TIMEOUT":"90"}}'
```

**After any timeout change, restart the application:**
```bash
kubectl rollout restart deployment/prod-falco-ai-alerts -n falco-ai-alerts
``` 