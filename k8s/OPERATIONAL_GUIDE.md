# Operational Guide - Falco Vanguard v2.1.12

## 🚀 Quick Access Commands

Once your Falco Vanguard is deployed, use these commands for day-to-day operations.

## 🌐 Access Methods

### **Production Environment (with Ingress)**
```bash
# Access via ingress (production setups)
echo "Main Dashboard:      https://your-domain.com/"
echo "Enhanced Chat:       https://your-domain.com/enhanced-chat"
echo "MCP Hub:            https://your-domain.com/mcp-dashboard"
echo "Audit Dashboard:     https://your-domain.com/audit"
echo "AI Configuration:    https://your-domain.com/config/ai"
echo "Weaviate Analytics:  https://your-domain.com/weaviate-analytics"
```

### **Development Environment (Port Forward)**
```bash
# Port forward to main application
kubectl port-forward svc/falco-ai-alerts 8080:8080 -n falco-ai-alerts

# Alternative: Direct pod access
kubectl port-forward deployment/falco-ai-alerts 8080:8080 -n falco-ai-alerts

# Access URLs after port-forward:
# Main Dashboard:     http://localhost:8080/
# Enhanced Chat:      http://localhost:8080/enhanced-chat
# MCP Hub:           http://localhost:8080/mcp-dashboard
# Audit Dashboard:    http://localhost:8080/audit
# AI Config:         http://localhost:8080/config/ai
# Analytics:         http://localhost:8080/weaviate-analytics
```

### **Component Access**
```bash
# Ollama LLM Service
kubectl port-forward svc/ollama 11434:11434 -n falco-ai-alerts
# Access: http://localhost:11434/

# Weaviate Vector Database
kubectl port-forward svc/weaviate 8082:8080 -n falco-ai-alerts
# Access: http://localhost:8082/v1/

# Database Management (if enabled)
kubectl port-forward svc/adminer 8081:8080 -n falco-ai-alerts
# Access: http://localhost:8081/
```

## 📊 Monitoring & Status

### **Deployment Status**
```bash
# Check all pods status
kubectl get pods -n falco-ai-alerts

# Detailed pod information
kubectl describe pods -n falco-ai-alerts

# Check deployment status
kubectl get deployments -n falco-ai-alerts

# Watch deployment rollout
kubectl rollout status deployment/falco-ai-alerts -n falco-ai-alerts
```

### **Health Checks**
```bash
# Application health check
kubectl exec deployment/falco-ai-alerts -n falco-ai-alerts -- curl -f http://localhost:8080/health

# Ollama health check
kubectl exec deployment/ollama -n falco-ai-alerts -- curl -f http://localhost:11434/api/tags

# Weaviate health check
kubectl exec deployment/weaviate -n falco-ai-alerts -- curl -f http://localhost:8080/v1/.well-known/ready
```

### **Resource Monitoring**
```bash
# Pod resource usage
kubectl top pods -n falco-ai-alerts

# Node resource usage
kubectl top nodes

# Check resource requests/limits
kubectl describe pods -n falco-ai-alerts | grep -A 5 "Requests:"
```

## 📋 Log Management

### **Application Logs**
```bash
# Main application logs
kubectl logs deployment/falco-ai-alerts -n falco-ai-alerts -f

# Logs from specific container
kubectl logs deployment/falco-ai-alerts -c falco-ai-alerts -n falco-ai-alerts -f

# Previous pod logs (after restart)
kubectl logs deployment/falco-ai-alerts -n falco-ai-alerts -p

# Logs with timestamps
kubectl logs deployment/falco-ai-alerts -n falco-ai-alerts --timestamps=true
```

### **Component Logs**
```bash
# Ollama model download and serving logs
kubectl logs deployment/ollama -n falco-ai-alerts -f

# Weaviate vector database logs
kubectl logs deployment/weaviate -n falco-ai-alerts -f

# Init container logs (model download)
kubectl logs job/ollama-model-init -n falco-ai-alerts
```

### **Centralized Logging**
```bash
# All logs with labels
kubectl logs -l app.kubernetes.io/name=falco-ai-alerts -n falco-ai-alerts --tail=100

# Follow all component logs
kubectl logs -l app.kubernetes.io/part-of=falco-ecosystem -n falco-ai-alerts -f
```

## 🔧 Configuration Management

### **View Current Configuration**
```bash
# Check ConfigMap
kubectl get configmap falco-ai-alerts-config -n falco-ai-alerts -o yaml

# Check Secrets
kubectl get secret falco-ai-alerts-secrets -n falco-ai-alerts -o yaml

# Decode secret values
kubectl get secret falco-ai-alerts-secrets -n falco-ai-alerts -o jsonpath='{.data.SLACK_BOT_TOKEN}' | base64 -d
```

### **Update Configuration**
```bash
# Update ConfigMap
kubectl patch configmap falco-ai-alerts-config -n falco-ai-alerts -p '{"data":{"LOG_LEVEL":"DEBUG"}}'

# Update Secret
kubectl patch secret falco-ai-alerts-secrets -n falco-ai-alerts -p '{"data":{"SLACK_BOT_TOKEN":"'$(echo -n 'new-token' | base64)'"}}'

# Restart deployment to pick up changes
kubectl rollout restart deployment/falco-ai-alerts -n falco-ai-alerts
```

### **Environment-Specific Configuration**
```bash
# Switch to production configuration
kubectl patch deployment falco-ai-alerts -n falco-ai-alerts -p '{"spec":{"template":{"spec":{"containers":[{"name":"falco-ai-alerts","env":[{"name":"LOG_LEVEL","value":"INFO"}]}]}}}}'

# Enable debug mode
kubectl patch deployment falco-ai-alerts -n falco-ai-alerts -p '{"spec":{"template":{"spec":{"containers":[{"name":"falco-ai-alerts","env":[{"name":"LOG_LEVEL","value":"DEBUG"}]}]}}}}'
```

## 🔄 Update Operations

### **Rolling Updates**
```bash
# Update to new version
kubectl set image deployment/falco-ai-alerts falco-ai-alerts=maddigsys/falco-ai-alerts:v2.1.12 -n falco-ai-alerts

# Check rollout progress
kubectl rollout status deployment/falco-ai-alerts -n falco-ai-alerts

# Check rollout history
kubectl rollout history deployment/falco-ai-alerts -n falco-ai-alerts
```

### **Rollback Operations**
```bash
# Rollback to previous version
kubectl rollout undo deployment/falco-ai-alerts -n falco-ai-alerts

# Rollback to specific revision
kubectl rollout undo deployment/falco-ai-alerts -n falco-ai-alerts --to-revision=2

# Check rollback status
kubectl rollout status deployment/falco-ai-alerts -n falco-ai-alerts
```

## 🎯 Scaling Operations

### **Manual Scaling**
```bash
# Scale up deployment
kubectl scale deployment falco-ai-alerts --replicas=3 -n falco-ai-alerts

# Scale down deployment
kubectl scale deployment falco-ai-alerts --replicas=1 -n falco-ai-alerts

# Check scaling status
kubectl get deployment falco-ai-alerts -n falco-ai-alerts
```

### **Horizontal Pod Autoscaling (HPA)**
```bash
# Check HPA status (if enabled)
kubectl get hpa -n falco-ai-alerts

# Describe HPA metrics
kubectl describe hpa falco-ai-alerts -n falco-ai-alerts

# Create HPA manually
kubectl autoscale deployment falco-ai-alerts --cpu-percent=70 --min=2 --max=10 -n falco-ai-alerts
```

## 🚨 Troubleshooting Guide

### **Common Issues**

#### **Pods Stuck in Pending State**
```bash
# Check node resources
kubectl top nodes
kubectl describe nodes

# Check events
kubectl get events -n falco-ai-alerts --sort-by='.lastTimestamp'

# Check pod scheduling
kubectl describe pod <pod-name> -n falco-ai-alerts
```

#### **Application Not Responding**
```bash
# Check pod status
kubectl get pods -n falco-ai-alerts -o wide

# Check application logs
kubectl logs deployment/falco-ai-alerts -n falco-ai-alerts --tail=50

# Test application endpoint
kubectl exec deployment/falco-ai-alerts -n falco-ai-alerts -- curl -f http://localhost:8080/health
```

#### **Ollama Model Issues**
```bash
# Check model download progress
kubectl logs job/ollama-model-init -n falco-ai-alerts

# Check available models
kubectl exec deployment/ollama -n falco-ai-alerts -- ollama list

# Force model re-download
kubectl delete job ollama-model-init -n falco-ai-alerts
kubectl apply -f k8s/base/ollama-init-job.yaml
```

#### **Storage Issues**
```bash
# Check PVC status
kubectl get pvc -n falco-ai-alerts

# Check storage class
kubectl get storageclass

# Describe PVC for events
kubectl describe pvc data-falco-ai-alerts-0 -n falco-ai-alerts
```

### **Performance Tuning**

#### **Resource Optimization**
```bash
# Check current resource usage
kubectl top pods -n falco-ai-alerts

# Update resource requests/limits
kubectl patch deployment falco-ai-alerts -n falco-ai-alerts -p '{"spec":{"template":{"spec":{"containers":[{"name":"falco-ai-alerts","resources":{"requests":{"memory":"1Gi","cpu":"500m"},"limits":{"memory":"2Gi","cpu":"1000m"}}}]}}}}'

# Check node capacity
kubectl describe nodes | grep -A 5 "Allocated resources"
```

#### **Model Performance Tuning**
```bash
# Switch to faster model
kubectl patch configmap falco-ai-alerts-config -n falco-ai-alerts -p '{"data":{"OLLAMA_MODEL_NAME":"phi3:mini"}}'

# Increase timeout for larger models
kubectl patch configmap falco-ai-alerts-config -n falco-ai-alerts -p '{"data":{"OLLAMA_TIMEOUT":"300"}}'

# Restart to apply changes
kubectl rollout restart deployment/falco-ai-alerts -n falco-ai-alerts
```

## 🧹 Maintenance Operations

### **Regular Maintenance**
```bash
# Restart all components (weekly maintenance)
kubectl rollout restart deployment/falco-ai-alerts -n falco-ai-alerts
kubectl rollout restart deployment/ollama -n falco-ai-alerts
kubectl rollout restart deployment/weaviate -n falco-ai-alerts

# Clean up old ReplicaSets
kubectl delete replicaset -l app.kubernetes.io/name=falco-ai-alerts -n falco-ai-alerts

# Update all images to latest
kubectl set image deployment/falco-ai-alerts falco-ai-alerts=maddigsys/falco-ai-alerts:latest -n falco-ai-alerts
```

### **Data Backup**
```bash
# Backup database
kubectl exec deployment/falco-ai-alerts -n falco-ai-alerts -- tar -czf /tmp/backup-$(date +%Y%m%d).tar.gz /app/data/

# Copy backup to local machine
kubectl cp falco-ai-alerts/falco-ai-alerts-xxx:/tmp/backup-$(date +%Y%m%d).tar.gz ./backup-$(date +%Y%m%d).tar.gz

# Backup Weaviate data
kubectl exec deployment/weaviate -n falco-ai-alerts -- tar -czf /tmp/weaviate-backup-$(date +%Y%m%d).tar.gz /var/lib/weaviate/
```

### **Cleanup Operations**
```bash
# Remove old deployments
kubectl delete deployment old-deployment-name -n falco-ai-alerts

# Clean up unused ConfigMaps
kubectl delete configmap unused-config -n falco-ai-alerts

# Clean up unused Secrets
kubectl delete secret unused-secret -n falco-ai-alerts
```

## 📈 Monitoring Integration

### **Prometheus Metrics**
```bash
# Check if metrics are exposed
kubectl exec deployment/falco-ai-alerts -n falco-ai-alerts -- curl http://localhost:8080/metrics

# Port forward to Prometheus (if deployed)
kubectl port-forward svc/prometheus 9090:9090 -n monitoring
```

### **Health Dashboard**
```bash
# Create monitoring dashboard
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboard
  namespace: falco-ai-alerts
data:
  dashboard.json: |
    {
      "dashboard": {
        "title": "Falco AI Alerts",
        "panels": [...monitoring panels...]
      }
    }
EOF
``` 