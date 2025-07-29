# Operational Commands Guide - Falco AI Alert System

## 🚀 Quick Access Commands

Once your Falco AI Alert System is deployed, use these commands for day-to-day operations.

---

## 🌐 Port Forwarding & UI Access

### **Development Environment**

#### **Main Application Access**
```bash
# Port forward to main application (port 8080)
kubectl port-forward svc/dev-falco-ai-alerts 8080:8080 -n falco-ai-alerts-dev

# Alternative: Direct pod access
kubectl port-forward deployment/dev-falco-ai-alerts 8080:8080 -n falco-ai-alerts-dev

# Access URLs after port-forward:
# Main Dashboard:     http://localhost:8080/
# Enhanced Chat:      http://localhost:8080/enhanced-chat
# MCP Hub:           http://localhost:8080/mcp-dashboard
# Audit Dashboard:    http://localhost:8080/audit
# AI Config:         http://localhost:8080/ai-config
# Analytics:         http://localhost:8080/weaviate-analytics
```

#### **Webhook Access (for testing)**
```bash
# Port forward webhook service
kubectl port-forward svc/dev-falco-ai-alerts-webhook 8081:80 -n falco-ai-alerts-dev

# Test webhook endpoint
curl -X POST http://localhost:8081/falco-webhook \
  -H "Content-Type: application/json" \
  -d '{"priority": "Warning", "rule": "Test Alert", "message": "This is a test"}'
```

#### **Ollama API Access**
```bash
# Port forward to Ollama service
kubectl port-forward svc/dev-ollama 11434:11434 -n falco-ai-alerts-dev

# Test Ollama API
curl http://localhost:11434/api/tags
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "tinyllama", "prompt": "Hello", "stream": false}'
```

#### **Weaviate Vector Database Access**
```bash
# Port forward to Weaviate
kubectl port-forward svc/dev-weaviate 8090:8080 -n falco-ai-alerts-dev

# Access Weaviate console: http://localhost:8090/v1
# Test connection:
curl http://localhost:8090/v1/meta
```

### **Production Environment**

#### **Main Application Access**
```bash
# Port forward to production application
kubectl port-forward svc/prod-falco-ai-alerts 8080:8080 -n falco-ai-alerts

# Access URLs (same as development):
# Main Dashboard:     http://localhost:8080/
# Enhanced Chat:      http://localhost:8080/enhanced-chat
# MCP Hub:           http://localhost:8080/mcp-dashboard
# Audit Dashboard:    http://localhost:8080/audit
# AI Config:         http://localhost:8080/ai-config
# Analytics:         http://localhost:8080/weaviate-analytics
```

#### **Webhook Access**
```bash
# Port forward webhook service
kubectl port-forward svc/prod-falco-ai-alerts-webhook 8081:80 -n falco-ai-alerts

# Test webhook endpoint
curl -X POST http://localhost:8081/falco-webhook \
  -H "Content-Type: application/json" \
  -d '{"priority": "Critical", "rule": "Production Test", "message": "This is a production test"}'
```

#### **Ollama API Access**
```bash
# Port forward to production Ollama
kubectl port-forward svc/prod-ollama 11434:11434 -n falco-ai-alerts

# Check available models
curl http://localhost:11434/api/tags
```

#### **Weaviate Access**
```bash
# Port forward to production Weaviate
kubectl port-forward svc/prod-weaviate 8090:8080 -n falco-ai-alerts

# Access Weaviate console: http://localhost:8090/v1
```

### **Cloud-Specific Access (EKS/GKE/AKS)**

#### **AWS EKS Multi-Architecture Support**
```bash
# Deploy to EKS with multi-architecture support (AMD64 + ARM64)
kubectl apply -k overlays/eks/

# Check node architecture in your EKS cluster
kubectl get nodes -o custom-columns=NAME:.metadata.name,ARCH:.status.nodeInfo.architecture,INSTANCE:.metadata.labels.node\.kubernetes\.io/instance-type

# Port forward to EKS deployment
kubectl port-forward svc/prod-falco-ai-alerts 8080:8080 -n falco-ai-alerts

# Check which architecture your pods are running on
kubectl get pods -n falco-ai-alerts -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName,ARCH:.spec.nodeSelector.kubernetes\.io/arch

# Access via Application Load Balancer (if configured)
kubectl get ingress -n falco-ai-alerts
# Look for ALB endpoint in the ingress output

# Test EKS-specific features
kubectl describe deployment prod-falco-ai-alerts -n falco-ai-alerts | grep -A10 "Node-Selectors\|Affinity"
kubectl describe deployment prod-ollama -n falco-ai-alerts | grep -A10 "Node-Selectors\|Affinity"
```

#### **EKS Cost Optimization (ARM64 Graviton)**
```bash
# Check if you're using cost-effective ARM64 instances
kubectl get nodes -l kubernetes.io/arch=arm64

# Verify Graviton instance types
kubectl get nodes -o custom-columns=NAME:.metadata.name,INSTANCE:.metadata.labels.node\.kubernetes\.io/instance-type | grep t4g

# Monitor resource costs (if AWS Cost Explorer is configured)
kubectl top nodes --sort-by=memory
kubectl top pods -n falco-ai-alerts --sort-by=memory
```

#### **Google GKE**
```bash
# GKE-specific port forwarding
kubectl port-forward svc/prod-falco-ai-alerts 8080:8080 -n falco-ai-alerts
# Access via Google Cloud Load Balancer if configured
```

#### **Azure AKS**
```bash
# AKS-specific port forwarding
kubectl port-forward svc/prod-falco-ai-alerts 8080:8080 -n falco-ai-alerts
# Access via Azure Load Balancer if configured
```

---

## 📊 Log Checking Commands

### **Application Logs**

#### **Development Environment**
```bash
# Follow main application logs
kubectl logs -f deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev

# Get recent logs (last 100 lines)
kubectl logs deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev --tail=100

# Logs with timestamps
kubectl logs deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev --timestamps=true

# Filter logs by level
kubectl logs deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev | grep ERROR
kubectl logs deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev | grep WARNING
kubectl logs deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev | grep INFO

# All pods logs (in case of multiple replicas)
kubectl logs -f -l app.kubernetes.io/name=falco-ai-alerts -n falco-ai-alerts-dev

# Get logs from specific pod
kubectl get pods -n falco-ai-alerts-dev
kubectl logs dev-falco-ai-alerts-<pod-id> -n falco-ai-alerts-dev
```

#### **Production Environment**
```bash
# Follow production logs (all replicas)
kubectl logs -f -l app.kubernetes.io/name=falco-ai-alerts -n falco-ai-alerts

# Individual production pod logs
kubectl logs -f deployment/prod-falco-ai-alerts -n falco-ai-alerts

# Production logs with context (previous terminated containers)
kubectl logs deployment/prod-falco-ai-alerts -n falco-ai-alerts --previous

# Export logs to file
kubectl logs deployment/prod-falco-ai-alerts -n falco-ai-alerts > falco-ai-alerts-$(date +%Y%m%d).log
```

### **Component-Specific Logs**

#### **Ollama Logs**
```bash
# Development Ollama
kubectl logs -f deployment/dev-ollama -n falco-ai-alerts-dev

# Production Ollama
kubectl logs -f deployment/prod-ollama -n falco-ai-alerts

# Ollama model initialization logs
kubectl logs job/dev-ollama-model-init -n falco-ai-alerts-dev
kubectl logs job/prod-ollama-model-init -n falco-ai-alerts
```

#### **Weaviate Logs**
```bash
# Development Weaviate
kubectl logs -f deployment/dev-weaviate -n falco-ai-alerts-dev

# Production Weaviate
kubectl logs -f deployment/prod-weaviate -n falco-ai-alerts
```

### **Event Logs and Troubleshooting**
```bash
# Check Kubernetes events for issues
kubectl get events -n falco-ai-alerts-dev --sort-by=.metadata.creationTimestamp
kubectl get events -n falco-ai-alerts --sort-by=.metadata.creationTimestamp

# Check events for specific deployment
kubectl describe deployment dev-falco-ai-alerts -n falco-ai-alerts-dev
kubectl describe deployment prod-falco-ai-alerts -n falco-ai-alerts

# Check pod events and status
kubectl describe pod <pod-name> -n falco-ai-alerts-dev
kubectl describe pod <pod-name> -n falco-ai-alerts
```

---

## 🔍 Status Checking Commands

### **Deployment Status**

#### **Quick Status Check**
```bash
# Development environment status
kubectl get all -n falco-ai-alerts-dev

# Production environment status
kubectl get all -n falco-ai-alerts

# Specific deployment status
kubectl get deployment dev-falco-ai-alerts -n falco-ai-alerts-dev
kubectl get deployment prod-falco-ai-alerts -n falco-ai-alerts

# Rollout status
kubectl rollout status deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev
kubectl rollout status deployment/prod-falco-ai-alerts -n falco-ai-alerts
```

#### **Detailed Status**
```bash
# Comprehensive status check
kubectl describe deployment dev-falco-ai-alerts -n falco-ai-alerts-dev
kubectl describe deployment prod-falco-ai-alerts -n falco-ai-alerts

# Pod status and resource usage
kubectl top pods -n falco-ai-alerts-dev
kubectl top pods -n falco-ai-alerts

# Node resource usage
kubectl top nodes
```

### **Health Checks**
```bash
# Check application health endpoint
kubectl port-forward svc/dev-falco-ai-alerts 8080:8080 -n falco-ai-alerts-dev &
curl http://localhost:8080/health
kill %1  # Stop port-forward

# Check all health endpoints
kubectl get pods -n falco-ai-alerts-dev -o wide
kubectl exec deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev -- curl http://localhost:8080/health

# Check readiness and liveness probes
kubectl describe pod <pod-name> -n falco-ai-alerts-dev | grep -A5 "Liveness\|Readiness"
```

### **Service Status**
```bash
# Check service endpoints
kubectl get endpoints -n falco-ai-alerts-dev
kubectl get endpoints -n falco-ai-alerts

# Service details
kubectl describe service dev-falco-ai-alerts -n falco-ai-alerts-dev
kubectl describe service prod-falco-ai-alerts -n falco-ai-alerts

# Test service connectivity
kubectl run debug --image=busybox --rm -it --restart=Never -- \
  wget -qO- http://dev-falco-ai-alerts.falco-ai-alerts-dev.svc.cluster.local:8080/health
```

### **Storage Status**
```bash
# Check persistent volumes
kubectl get pv
kubectl get pvc -n falco-ai-alerts-dev
kubectl get pvc -n falco-ai-alerts

# Storage details
kubectl describe pvc dev-falco-ai-alerts-data -n falco-ai-alerts-dev
kubectl describe pvc prod-falco-ai-alerts-data -n falco-ai-alerts

# Check storage usage (if metrics available)
kubectl exec deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev -- df -h /app/data
```

---

## ⚙️ Configuration Management

### **View Configuration**
```bash
# View ConfigMap
kubectl get configmap dev-falco-ai-alerts-config -n falco-ai-alerts-dev -o yaml
kubectl get configmap prod-falco-ai-alerts-config -n falco-ai-alerts -o yaml

# View Secrets (base64 encoded)
kubectl get secret dev-falco-ai-alerts-secrets -n falco-ai-alerts-dev -o yaml
kubectl get secret prod-falco-ai-alerts-secrets -n falco-ai-alerts -o yaml

# Decode specific secret values
kubectl get secret dev-falco-ai-alerts-secrets -n falco-ai-alerts-dev -o jsonpath="{.data.SLACK_BOT_TOKEN}" | base64 --decode
```

### **Update Configuration**
```bash
# Update ConfigMap values
kubectl patch configmap dev-falco-ai-alerts-config -n falco-ai-alerts-dev \
  --patch '{"data":{"LOG_LEVEL":"DEBUG"}}'

# Update Secret values
kubectl patch secret dev-falco-ai-alerts-secrets -n falco-ai-alerts-dev \
  --patch '{"stringData":{"SLACK_BOT_TOKEN":"xoxb-new-token"}}'

# Restart deployment after config changes
kubectl rollout restart deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev
kubectl rollout restart deployment/prod-falco-ai-alerts -n falco-ai-alerts
```

---

## 🔧 Scaling and Resource Management

### **Manual Scaling**
```bash
# Scale development deployment
kubectl scale deployment dev-falco-ai-alerts --replicas=2 -n falco-ai-alerts-dev

# Scale production deployment
kubectl scale deployment prod-falco-ai-alerts --replicas=5 -n falco-ai-alerts

# Check HPA (Horizontal Pod Autoscaler) status
kubectl get hpa -n falco-ai-alerts
kubectl describe hpa prod-falco-ai-alerts-hpa -n falco-ai-alerts
```

### **Resource Monitoring**
```bash
# Monitor resource usage
kubectl top pods -n falco-ai-alerts-dev --sort-by=memory
kubectl top pods -n falco-ai-alerts --sort-by=cpu

# Check resource limits and requests
kubectl describe deployment dev-falco-ai-alerts -n falco-ai-alerts-dev | grep -A10 "Limits\|Requests"
kubectl describe deployment prod-falco-ai-alerts -n falco-ai-alerts | grep -A10 "Limits\|Requests"
```

---

## 🗄️ Database Operations

### **Database Access**
```bash
# Connect to application database
kubectl exec -it deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev -- /bin/bash

# Inside the container, access SQLite database:
# sqlite3 /app/data/alerts.db
# .schema
# SELECT COUNT(*) FROM alerts;
# SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 10;
# .quit
```

### **Database Backup**
```bash
# Backup development database
kubectl exec deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev -- \
  cp /app/data/alerts.db /tmp/alerts-backup-$(date +%Y%m%d).db

kubectl cp falco-ai-alerts-dev/$(kubectl get pods -n falco-ai-alerts-dev -l app.kubernetes.io/name=falco-ai-alerts -o jsonpath='{.items[0].metadata.name}'):/tmp/alerts-backup-$(date +%Y%m%d).db \
  ./alerts-backup-dev-$(date +%Y%m%d).db

# Backup production database
kubectl exec deployment/prod-falco-ai-alerts -n falco-ai-alerts -- \
  cp /app/data/alerts.db /tmp/alerts-backup-$(date +%Y%m%d).db

kubectl cp falco-ai-alerts/$(kubectl get pods -n falco-ai-alerts -l app.kubernetes.io/name=falco-ai-alerts -o jsonpath='{.items[0].metadata.name}'):/tmp/alerts-backup-$(date +%Y%m%d).db \
  ./alerts-backup-prod-$(date +%Y%m%d).db
```

### **Database Restore**
```bash
# Restore database (example)
kubectl cp ./alerts-backup.db falco-ai-alerts-dev/$(kubectl get pods -n falco-ai-alerts-dev -l app.kubernetes.io/name=falco-ai-alerts -o jsonpath='{.items[0].metadata.name}'):/tmp/restore.db

kubectl exec deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev -- \
  cp /tmp/restore.db /app/data/alerts.db

# Restart deployment after restore
kubectl rollout restart deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev
```

---

## 🚨 Troubleshooting Commands

### **Common Issues**

#### **Pods Not Starting**
```bash
# Check pod status and events
kubectl get pods -n falco-ai-alerts-dev
kubectl describe pod <pod-name> -n falco-ai-alerts-dev

# Check image pull issues
kubectl get events -n falco-ai-alerts-dev --field-selector reason=Failed
kubectl get events -n falco-ai-alerts-dev --field-selector reason=FailedMount
```

#### **Storage Issues**
```bash
# Check PVC binding
kubectl get pvc -n falco-ai-alerts-dev
kubectl describe pvc <pvc-name> -n falco-ai-alerts-dev

# Check storage class
kubectl get storageclass
kubectl describe storageclass <storage-class-name>
```

#### **Network Connectivity Issues**
```bash
# Test pod-to-pod connectivity
kubectl exec -it deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev -- \
  wget -qO- http://dev-ollama:11434/api/tags

# Test external connectivity
kubectl exec -it deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev -- \
  wget -qO- https://api.slack.com/api/test
```

#### **Performance Issues**
```bash
# Check resource constraints
kubectl top pods -n falco-ai-alerts-dev
kubectl describe node <node-name>

# Check if pods are being throttled
kubectl describe pod <pod-name> -n falco-ai-alerts-dev | grep -i throttl
```

#### **EKS-Specific Troubleshooting**
```bash
# Check EKS cluster version and compatibility
kubectl version --short

# Verify EKS-specific storage classes
kubectl get storageclass | grep gp3

# Check AWS Load Balancer Controller (if using ALB)
kubectl get pods -n kube-system | grep aws-load-balancer

# Verify EKS node groups and instance types
kubectl describe nodes | grep -E "instance-type|kubernetes.io/arch"

# Check if Graviton ARM64 nodes are being used
kubectl get nodes -l kubernetes.io/arch=arm64 -o wide

# Debug multi-architecture image pulls
kubectl describe pod <pod-name> -n falco-ai-alerts | grep -A5 -B5 "image"

# Check EKS-specific annotations and labels
kubectl get deployment prod-falco-ai-alerts -n falco-ai-alerts -o yaml | grep -A5 -B5 "eks.amazonaws.com"

# Verify Security Groups for Pods (if using VPC CNI)
kubectl describe pod <pod-name> -n falco-ai-alerts | grep -i "security-group"
```

---

## 🔄 Deployment Management

### **Updates and Rollbacks**
```bash
# Update to new image version
kubectl set image deployment/dev-falco-ai-alerts falco-ai-alerts=maddigsys/falco-ai-alerts:v2.2.0 -n falco-ai-alerts-dev

# Check rollout status
kubectl rollout status deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev

# View rollout history
kubectl rollout history deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev

# Rollback to previous version
kubectl rollout undo deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev

# Rollback to specific revision
kubectl rollout undo deployment/dev-falco-ai-alerts --to-revision=2 -n falco-ai-alerts-dev
```

### **Configuration Reloads**
```bash
# Restart deployment (triggers rolling update)
kubectl rollout restart deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev
kubectl rollout restart deployment/prod-falco-ai-alerts -n falco-ai-alerts

# Force pod recreation
kubectl delete pod -l app.kubernetes.io/name=falco-ai-alerts -n falco-ai-alerts-dev
```

---

## 📋 Cleanup Commands

### **Selective Cleanup**
```bash
# Remove specific deployment
kubectl delete deployment dev-falco-ai-alerts -n falco-ai-alerts-dev
kubectl delete deployment prod-falco-ai-alerts -n falco-ai-alerts

# Remove services but keep data
kubectl delete service dev-falco-ai-alerts dev-falco-ai-alerts-webhook -n falco-ai-alerts-dev

# Remove jobs (model initialization)
kubectl delete job dev-ollama-model-init -n falco-ai-alerts-dev
kubectl delete job prod-ollama-model-init -n falco-ai-alerts
```

### **Complete Environment Cleanup**
```bash
# Development environment
kubectl delete namespace falco-ai-alerts-dev

# Production environment (⚠️ USE WITH CAUTION)
kubectl delete namespace falco-ai-alerts

# Check cleanup completion
kubectl get namespace | grep falco-ai-alerts
```

---

## 🔗 Integration Commands

### **Falco Integration**
```bash
# Check if Falco is sending alerts
kubectl logs -n falco-ai-alerts-dev deployment/dev-falco-ai-alerts | grep "Falco alert received"

# Test webhook manually
curl -X POST http://localhost:8081/falco-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "time": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "rule": "Terminal shell in container",
    "priority": "Warning",
    "message": "A shell was spawned in container test-container",
    "output_fields": {
      "container.name": "test-container",
      "evt.time": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
      "proc.cmdline": "/bin/bash"
    }
  }'
```

### **Slack Integration Test**
```bash
# Check Slack integration logs
kubectl logs deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev | grep -i slack

# Test Slack notification manually via API
kubectl port-forward svc/dev-falco-ai-alerts 8080:8080 -n falco-ai-alerts-dev &
curl -X POST http://localhost:8080/api/test-slack
kill %1
```

---

## 📊 Monitoring and Metrics

### **Prometheus Integration**
```bash
# Check if metrics endpoint is available
kubectl port-forward svc/dev-falco-ai-alerts 8080:8080 -n falco-ai-alerts-dev &
curl http://localhost:8080/health
curl http://localhost:8080/metrics  # If metrics endpoint exists
kill %1
```

### **Performance Metrics**
```bash
# Application performance metrics
kubectl exec deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev -- \
  ps aux | head -n 20

# Memory usage breakdown
kubectl exec deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev -- \
  cat /proc/meminfo | head -n 10

# Disk usage
kubectl exec deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev -- \
  df -h
```

---

## 🚀 **EKS Testing Quick Start**

### **Multi-Architecture EKS Deployment**
```bash
# 1. Verify your EKS cluster supports multi-architecture
kubectl get nodes -o custom-columns=NAME:.metadata.name,ARCH:.status.nodeInfo.architecture,INSTANCE:.metadata.labels.node\.kubernetes\.io/instance-type

# 2. Deploy using EKS-optimized configuration
kubectl apply -k overlays/eks/

# 3. Monitor deployment progress
kubectl get pods -n falco-ai-alerts -w

# 4. Check which architecture your pods landed on
kubectl get pods -n falco-ai-alerts -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName
kubectl get nodes -o custom-columns=NAME:.metadata.name,ARCH:.status.nodeInfo.architecture

# 5. Access the application
kubectl port-forward svc/prod-falco-ai-alerts 8080:8080 -n falco-ai-alerts
# Open: http://localhost:8080/

# 6. Test with a Falco alert
curl -X POST http://localhost:8080/falco-webhook \
  -H "Content-Type: application/json" \
  -d '{"priority": "Warning", "rule": "EKS Test Alert", "message": "Testing multi-arch deployment"}'
```

### **Cost Optimization Verification**
```bash
# Check if you're getting ARM64 cost savings
kubectl get nodes -l kubernetes.io/arch=arm64 --show-labels

# Verify Graviton instances (20-40% cost savings)
kubectl get nodes -o custom-columns=NAME:.metadata.name,INSTANCE:.metadata.labels.node\.kubernetes\.io/instance-type | grep -E "t4g|m6g|c6g"

# Monitor resource efficiency
kubectl top nodes
kubectl top pods -n falco-ai-alerts --sort-by=memory
```

---

## 🎯 Quick Reference Summary

### **Essential Commands for Daily Operations**
```bash
# 1. Quick status check
kubectl get all -n falco-ai-alerts-dev

# 2. Access application
kubectl port-forward svc/dev-falco-ai-alerts 8080:8080 -n falco-ai-alerts-dev

# 3. Check logs
kubectl logs -f deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev

# 4. Check health
curl http://localhost:8080/health

# 5. Restart if needed
kubectl rollout restart deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev
```

### **Emergency Commands**
```bash
# Scale down immediately
kubectl scale deployment dev-falco-ai-alerts --replicas=0 -n falco-ai-alerts-dev

# Get immediate diagnostics
kubectl describe pod <failing-pod> -n falco-ai-alerts-dev
kubectl logs <failing-pod> -n falco-ai-alerts-dev --previous

# Force pod restart
kubectl delete pod <pod-name> -n falco-ai-alerts-dev
```

---

**🎉 You now have comprehensive operational commands for managing your Falco AI Alert System deployment!**

Save this guide for quick reference during development and production operations. 