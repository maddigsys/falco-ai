# Deployment & Testing Guide - Falco Vanguard v2.1.12

**Release Date**: January 30, 2025  
**Docker Image**: `maddigsys/falco-ai-alerts:v2.1.12`  
**Branch**: `main` (latest)

## 🚀 Quick Deployment Commands

### **Production Deployment (Recommended)**

```bash
# One-command deployment (auto-detects your cluster)
cd k8s && ./install-dynamic.sh

# Manual production deployment
kubectl apply -k k8s/overlays/production

# Verify deployment
kubectl get pods -n falco-ai-alerts
kubectl logs -f deployment/prod-falco-ai-alerts -n falco-ai-alerts
```

### **Development Deployment**

```bash
# Development environment
kubectl apply -k k8s/overlays/dev-auto

# Check status
kubectl get pods -n falco-ai-alerts-dev
kubectl port-forward deployment/dev-falco-ai-alerts 8080:8080 -n falco-ai-alerts-dev
```

### **Cloud-Optimized Deployments**

```bash
# AWS EKS (optimized for Graviton2/3 ARM instances)
kubectl apply -k k8s/overlays/eks

# Google GKE (optimized for GCP infrastructure)
kubectl apply -k k8s/overlays/gke

# Azure AKS (optimized for Azure infrastructure)
kubectl apply -k k8s/overlays/aks
```

## 🏗️ Infrastructure Components

### **Core Services**
- **falco-ai-alerts**: Main application (`maddigsys/falco-ai-alerts:v2.1.12`)
- **ollama**: Local LLM service for AI analysis
- **weaviate**: Vector database for enhanced search and analytics

### **Architecture**
- **Multi-architecture**: AMD64 + ARM64 support
- **Container Orchestration**: Kubernetes-native
- **Storage**: Persistent volumes for data retention
- **Networking**: Service mesh ready with ingress support

### **Resource Requirements**

| Component | CPU Request | Memory Request | CPU Limit | Memory Limit |
|-----------|-------------|----------------|-----------|--------------|
| Falco Vanguard | 250m | 256Mi | 500m | 512Mi |
| Ollama | 1000m | 2Gi | 2000m | 4Gi |
| Weaviate | 500m | 1Gi | 1000m | 2Gi |

## 🧪 Testing Your Deployment

### **1. Health Check Tests**

```bash
# Basic health check
curl http://localhost:8080/health

# Detailed system status
curl http://localhost:8080/api/system/status

# MCP integration status
curl http://localhost:8080/api/mcp/status
```

### **2. Dashboard Access Tests**

```bash
# Main dashboard
open http://localhost:8080/dashboard

# Analytics dashboard
open http://localhost:8080/weaviate-analytics

# MCP Hub
open http://localhost:8080/mcp-dashboard

# Configuration pages
open http://localhost:8080/config/general
open http://localhost:8080/config/slack
```

### **3. API Functionality Tests**

```bash
# Test alert retrieval
curl "http://localhost:8080/api/alerts?limit=5"

# Test AI configuration
curl http://localhost:8080/api/ai/config

# Test webhook functionality
curl -X POST http://localhost:8080/api/test-alert \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

### **4. Filtering and Navigation Tests**

```bash
# Test Processing Queue filtering
open "http://localhost:8080/runtime-events?aiAnalysis=without_ai&time_range=24h"

# Test priority filtering
open "http://localhost:8080/runtime-events?priority=critical&status=unread"

# Test container filtering
open "http://localhost:8080/runtime-events?container=nginx&time_range=6h"

# Test complex filtering
open "http://localhost:8080/runtime-events?priority=critical&container=test&aiAnalysis=with_ai"
```

### **5. MCP Integration Tests**

```bash
# Test MCP tools endpoint
curl http://localhost:8080/api/mcp/tools

# Test JSON-RPC MCP setup
./setup_jsonrpc_mcp.sh
python3 test_jsonrpc_mcp.py

# Test Claude MCP setup
./setup_claude_mcp.sh  
python3 test_claude_mcp.py
```

## 📊 Performance Testing

### **Load Testing Commands**

```bash
# Generate test alerts (if Falco is running)
for i in {1..10}; do
  curl -X POST http://localhost:8080/api/test-alert \
    -H "Content-Type: application/json" \
    -d "{\"test_id\": $i, \"priority\": \"warning\"}"
  sleep 1
done

# Monitor resource usage
kubectl top pods -n falco-ai-alerts
kubectl top nodes

# Check processing performance
curl http://localhost:8080/api/alert-statistics
```

### **Stress Testing Filters**

```bash
# Test with large result sets
curl "http://localhost:8080/api/alerts?limit=1000&time_range=7d"

# Test complex filtering
curl "http://localhost:8080/api/alerts?priority=all&status=all&limit=500"

# Test search functionality
curl "http://localhost:8080/api/search?query=test&limit=100"
```

## 🔧 Troubleshooting Common Issues

### **1. Pod Not Starting**

```bash
# Check pod status
kubectl describe pod <pod-name> -n falco-ai-alerts

# Check logs
kubectl logs <pod-name> -n falco-ai-alerts --previous

# Check events
kubectl get events -n falco-ai-alerts --sort-by='.lastTimestamp'
```

### **2. Service Not Accessible**

```bash
# Check service status
kubectl get svc -n falco-ai-alerts

# Test internal connectivity
kubectl exec -it <pod-name> -n falco-ai-alerts -- curl localhost:8080/health

# Check port forwarding
kubectl port-forward service/falco-ai-alerts 8080:8080 -n falco-ai-alerts
```

### **3. Storage Issues**

```bash
# Check PVC status
kubectl get pvc -n falco-ai-alerts

# Check storage class
kubectl get storageclass

# Check volume mounts
kubectl describe pod <pod-name> -n falco-ai-alerts | grep -A 10 Mounts
```

### **4. Dashboard Loading Issues**

```bash
# Check static file serving
curl -I http://localhost:8080/static/logo.png

# Check JavaScript console for errors
# Open browser dev tools on dashboard pages

# Test specific functionality
curl http://localhost:8080/api/alerts | head -20
```

### **5. Filtering Not Working**

```bash
# Test direct API filtering
curl "http://localhost:8080/api/alerts?priority=critical"

# Check URL parameter handling
curl "http://localhost:8080/runtime-events?test=1" | grep -o "test"

# Verify filter state in UI
# Check browser dev tools -> Network tab for parameter passing
```

## 🔄 Update Procedures

### **Rolling Update**

```bash
# Update to new version
kubectl set image deployment/falco-ai-alerts falco-ai-alerts=maddigsys/falco-ai-alerts:v2.1.12 -n falco-ai-alerts

# Monitor rollout
kubectl rollout status deployment/falco-ai-alerts -n falco-ai-alerts

# Rollback if needed
kubectl rollout undo deployment/falco-ai-alerts -n falco-ai-alerts
```

### **Configuration Updates**

```bash
# Update ConfigMap
kubectl create configmap falco-ai-alerts-config --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f -

# Restart deployment to pick up changes
kubectl rollout restart deployment/falco-ai-alerts -n falco-ai-alerts
```

## 📈 Monitoring & Metrics

### **Health Monitoring**

```bash
# Continuous health check
watch -n 5 'curl -s http://localhost:8080/health | jq'

# Resource monitoring
watch -n 10 'kubectl top pods -n falco-ai-alerts'

# Log monitoring
kubectl logs -f deployment/falco-ai-alerts -n falco-ai-alerts | grep -E "(ERROR|WARN|SUCCESS)"
```

### **Performance Metrics**

```bash
# Alert processing metrics
curl http://localhost:8080/api/alert-statistics | jq

# System performance
curl http://localhost:8080/api/system/performance | jq

# Database metrics (if available)
curl http://localhost:8080/api/weaviate/status | jq
```

## 🎯 Success Criteria

Your deployment is successful when:

✅ **All pods are running**: `kubectl get pods -n falco-ai-alerts`  
✅ **Health check passes**: `curl http://localhost:8080/health`  
✅ **Dashboard loads**: Access http://localhost:8080/dashboard  
✅ **API responds**: `curl http://localhost:8080/api/alerts`  
✅ **Filtering works**: Test URL parameters on runtime events  
✅ **MCP integration**: All MCP endpoints return 200 status  
✅ **Configuration saves**: Test config pages work properly  

## 🏷️ Version Information

### **Latest Release: v2.1.12**

**Key Features:**
- Comprehensive dashboard filtering improvements
- Enhanced MCP API endpoints  
- Fixed button styling inconsistencies
- Complete URL parameter support
- Deep-linking capabilities for all dashboards

**Previous Versions:**
- **v2.1.1** - Enhanced configuration system, fixed Slack loading
- **v2.1.0** - MCP Hub integration, enhanced chat, audit system
- **v2.0.0** - Multi-architecture support, dynamic deployment

---

**🚀 Your Falco Vanguard is ready for production!**