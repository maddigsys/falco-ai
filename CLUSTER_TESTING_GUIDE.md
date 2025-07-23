# Cluster Testing Guide - Falco AI Alert System v2.1.0

## 🚀 Ready for Cluster Testing!

**Container Status:** ✅ Multi-architecture container built and pushed to Docker Hub  
**Image:** `maddigsys/falco-ai-alerts:v2.1.0`  
**Platforms:** AMD64 + ARM64 (automatically selected by Kubernetes)  
**Latest Changes:** All v2.1.0 features + runtime events fixes included  

---

## 🎯 Quick Deployment Commands

### **Production Deployment (Recommended for Testing)**

```bash
# Generic production deployment (works on any Kubernetes cluster)
kubectl apply -k https://github.com/maddigsys/falco-ai.git//k8s/overlays/production

# Verify deployment
kubectl get pods -n falco-ai-alerts
kubectl logs -f deployment/prod-falco-ai-alerts -n falco-ai-alerts
```

### **Cloud-Optimized Deployments**

```bash
# AWS EKS (optimized for Graviton2/3 ARM instances)
kubectl apply -k https://github.com/maddigsys/falco-ai.git//k8s/overlays/eks

# Google GKE (optimized for Tau T2A ARM instances)  
kubectl apply -k https://github.com/maddigsys/falco-ai.git//k8s/overlays/gke

# Azure AKS (optimized for Ampere Altra ARM instances)
kubectl apply -k https://github.com/maddigsys/falco-ai.git//k8s/overlays/aks
```

### **Development Deployment (Latest Features)**

```bash
# Development environment (uses :latest tag for rapid iteration)
kubectl apply -k https://github.com/maddigsys/falco-ai.git//k8s/overlays/development

# Check status
kubectl get pods -n falco-ai-alerts-dev
kubectl logs -f deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev
```

---

## 🔍 Verification Steps

### **1. Pod Status Check**
```bash
# Check all pods are running
kubectl get pods -n falco-ai-alerts -o wide

# Expected output: All pods in Running status
# NAME                                   READY   STATUS    ARCH
# prod-falco-ai-alerts-xxx               1/1     Running   amd64 or arm64
# prod-ollama-xxx                        1/1     Running   amd64 or arm64  
# prod-weaviate-xxx                      1/1     Running   amd64 or arm64
```

### **2. Service Access**
```bash
# Port forward to access the web UI
kubectl port-forward svc/prod-falco-ai-alerts 8080:8080 -n falco-ai-alerts

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:8080/api/alerts
```

### **3. Web UI Testing**
Open browser to `http://localhost:8080` and test:

- ✅ **Dashboard:** Main security dashboard
- ✅ **Enhanced Chat:** `http://localhost:8080/enhanced-chat`
- ✅ **Runtime Events:** `http://localhost:8080/runtime-events`
- ✅ **Audit System:** `http://localhost:8080/audit`
- ✅ **MCP Hub:** `http://localhost:8080/mcp-dashboard`
- ✅ **Analytics:** `http://localhost:8080/weaviate-analytics`

### **4. Test Alert Generation**
```bash
# Send test alert via API
curl -X POST http://localhost:8080/api/test-alert

# Or use the "Send Test Alert" button in the Runtime Events page
```

### **5. Multi-Architecture Verification**
```bash
# Check which architecture is running
kubectl get pods -n falco-ai-alerts -o jsonpath='{.items[*].spec.nodeSelector}'

# View container image details
kubectl describe pod -l app.kubernetes.io/name=falco-ai-alerts -n falco-ai-alerts | grep Image:
```

---

## 🛠️ Troubleshooting

### **Common Issues**

**Pods Stuck in Pending:**
```bash
# Check node resources and taints
kubectl describe nodes
kubectl get nodes -o wide

# Check events for scheduling issues  
kubectl get events -n falco-ai-alerts --sort-by='.lastTimestamp'
```

**Image Pull Errors:**
```bash
# Check if image exists and is accessible
docker manifest inspect maddigsys/falco-ai-alerts:v2.1.0

# Verify cluster can pull from Docker Hub
kubectl run test-pull --image=maddigsys/falco-ai-alerts:v2.1.0 --rm -it --restart=Never -- echo "Pull successful"
```

**Storage Issues:**
```bash
# Check storage classes
kubectl get storageclass

# Check PVC status
kubectl get pvc -n falco-ai-alerts
kubectl describe pvc -n falco-ai-alerts
```

### **Performance Monitoring**
```bash
# Monitor resource usage
kubectl top pods -n falco-ai-alerts
kubectl top nodes

# Check HPA status (if using cloud overlays)
kubectl get hpa -n falco-ai-alerts
kubectl describe hpa -n falco-ai-alerts
```

---

## 🔧 Configuration

### **Required Secrets**
```bash
# Production secrets (customize values)
kubectl create secret generic prod-falco-ai-alerts-secrets \
  --from-literal=SLACK_BOT_TOKEN="xoxb-your-slack-bot-token" \
  --from-literal=PORTKEY_API_KEY="pk-your-portkey-api-key" \
  --from-literal=OPENAI_VIRTUAL_KEY="openai-your-virtual-key" \
  --from-literal=GEMINI_VIRTUAL_KEY="gemini-your-virtual-key" \
  --from-literal=DB_ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --namespace falco-ai-alerts

# Development secrets (for dev overlay)
kubectl create secret generic dev-falco-ai-alerts-secrets \
  --from-literal=SLACK_BOT_TOKEN="xoxb-your-slack-bot-token" \
  --from-literal=PORTKEY_API_KEY="pk-your-portkey-api-key" \
  --from-literal=OPENAI_VIRTUAL_KEY="openai-your-virtual-key" \
  --from-literal=GEMINI_VIRTUAL_KEY="gemini-your-virtual-key" \
  --from-literal=DB_ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --namespace falco-ai-alerts-dev
```

### **Falco Integration**
```bash
# Configure Falco to send alerts (adjust URL based on your setup)
# Internal cluster URL:
# http://prod-falco-ai-alerts.falco-ai-alerts.svc.cluster.local:8080/falco-webhook

# External URL (with ingress):
# https://your-domain.com/falco-webhook
```

---

## 📊 Feature Testing Checklist

### **v2.1.0 Features to Test:**

- [ ] **Enhanced Chat Interface**
  - [ ] Server-side conversation sync
  - [ ] Real-time search functionality  
  - [ ] Export chat history (Text/Markdown/JSON)
  - [ ] Multi-language support
  - [ ] Persona selection (Security Analyst, Incident Responder, Threat Hunter)

- [ ] **Comprehensive Audit System**
  - [ ] Activity tracking and logging
  - [ ] Advanced filtering capabilities
  - [ ] Export audit logs (CSV/JSON)
  - [ ] User session analytics

- [ ] **Real-Time Features**
  - [ ] Server-Sent Events (SSE) connectivity
  - [ ] Multi-client synchronization
  - [ ] Live status updates
  - [ ] Visual indicators and animations

- [ ] **MCP Hub (Model Context Protocol)**
  - [ ] JSON-RPC MCP interface
  - [ ] Claude Desktop integration
  - [ ] gRPC MCP (high-performance)
  - [ ] 15 security tools accessibility

- [ ] **Enhanced Dashboard**
  - [ ] Advanced filtering with save/load
  - [ ] Keyboard shortcuts (R=read, D=dismiss, arrows=navigate)
  - [ ] Bulk operations with confirmations
  - [ ] Real-time alert synchronization

- [ ] **Runtime Events Fixes**
  - [ ] Proper empty state display
  - [ ] Test alert generation
  - [ ] Improved error handling
  - [ ] Enhanced debugging

---

## 🎯 Success Criteria

**Deployment is successful when:**
- ✅ All pods are Running and Ready
- ✅ Web UI is accessible and responsive
- ✅ Test alerts can be generated and displayed
- ✅ Multi-architecture container runs on cluster nodes
- ✅ Real-time features work (SSE connections)
- ✅ Chat interface syncs to server
- ✅ Audit system tracks activities

**Performance expectations:**
- **Memory usage:** ~1GB per main pod (2GB with Ollama)
- **CPU usage:** ~500m per main pod (2000m with Ollama)
- **Startup time:** ~30-60 seconds for full system
- **Response time:** <2s for web UI, <10s for AI analysis

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review pod logs: `kubectl logs -f deployment/prod-falco-ai-alerts -n falco-ai-alerts`
3. Check events: `kubectl get events -n falco-ai-alerts --sort-by='.lastTimestamp'`
4. Verify image accessibility: `docker manifest inspect maddigsys/falco-ai-alerts:v2.1.0`

**Container is ready for production cluster testing with full v2.1.0 feature set!** 🚀 