# Kubernetes Deployment Guide - Falco AI Alert System

This guide provides comprehensive instructions for deploying the Falco AI Alert System on Kubernetes.

## 📋 Prerequisites

### Kubernetes Cluster Requirements
- **Kubernetes Version**: 1.19+
- **Container Runtime**: Docker, containerd, or CRI-O
- **Storage**: Default StorageClass or specific storage configuration
- **Ingress Controller**: NGINX Ingress Controller (recommended)
- **DNS**: CoreDNS or kube-dns

### Required Cluster Add-ons
- **Metrics Server**: For HPA functionality
- **Cert-Manager**: For TLS certificate management (optional)
- **Prometheus**: For monitoring (optional but recommended)

### Tools Required
- `kubectl` (version compatible with your cluster)
- `kustomize` (v3.2.0+) or `kubectl` with kustomize support
- `docker` (for building custom images)
- `helm` (optional, for managing dependencies)

## 🚀 Quick Start

### ⚡ **Automated Installation (Recommended)**

```bash
# Install development environment
./install.sh dev

# Install production environment  
./install.sh prod

# The script will automatically:
# 1. Check prerequisites (kubectl, cluster access)
# 2. Validate configuration
# 3. Deploy all resources
# 4. Wait for readiness
# 5. Show access instructions and next steps
```

### 📋 **Manual Installation (Alternative)**

#### 1. Clone and Build
```bash
# Clone the repository
git clone <repository-url>
cd falco-ai-alerts/k8s

# Use the published image (recommended)
# Image is available at: maddigsys/falco-ai-alerts:latest

# Or build and push your own image
docker build -t your-registry/falco-ai-alerts:latest ..
docker push your-registry/falco-ai-alerts:latest
```

#### 2. Configure Secrets
```bash
# Create the namespace first
kubectl apply -f base/namespace.yaml

# Create secrets manually (recommended for production)
kubectl create secret generic falco-ai-alerts-secrets \
  --from-literal=SLACK_BOT_TOKEN="xoxb-your-actual-slack-token" \
  --from-literal=PORTKEY_API_KEY="your-portkey-api-key" \
  --from-literal=OPENAI_VIRTUAL_KEY="your-openai-virtual-key" \
  --from-literal=GEMINI_VIRTUAL_KEY="your-gemini-virtual-key" \
  --from-literal=DB_ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --namespace falco-ai-alerts

# Note: For Ollama (default), no API keys needed - it runs locally in the cluster!
```

#### 3. Deploy Development Environment
```bash
# Deploy to development
kubectl apply -k overlays/development/

# Check deployment status
kubectl get pods -n falco-ai-alerts-dev
kubectl logs -f deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev

# Access the application
kubectl port-forward svc/dev-falco-ai-alerts 8080:8080 -n falco-ai-alerts-dev
# Open http://localhost:8080/dashboard
```

#### 4. Deploy Production Environment
```bash
# Update image reference in production overlay
sed -i 's|newTag: "1.0.0"|newTag: "your-version"|' overlays/production/kustomization.yaml

# Deploy to production
kubectl apply -k overlays/production/

# Verify deployment
kubectl get all -n falco-ai-alerts
kubectl get hpa -n falco-ai-alerts
```

## 📦 Deployment Structure

```
k8s/
├── base/                          # Base Kubernetes resources
│   ├── namespace.yaml            # Namespace definition
│   ├── serviceaccount.yaml       # RBAC configuration
│   ├── configmap.yaml           # Non-sensitive configuration
│   ├── secret.yaml              # Sensitive configuration template
│   ├── pvc.yaml                 # Persistent storage
│   ├── deployment.yaml          # Main application deployment
│   ├── service.yaml             # Service definitions
│   ├── ingress.yaml             # External access configuration
│   ├── ollama-deployment.yaml   # Local AI provider (Ollama)
│   ├── ollama-init-job.yaml     # Model initialization job
│   └── kustomization.yaml       # Base kustomization
├── overlays/
│   ├── development/             # Development environment
│   │   └── kustomization.yaml   # Dev-specific configurations
│   └── production/              # Production environment
│       ├── kustomization.yaml   # Prod-specific configurations
│       ├── hpa.yaml            # Horizontal Pod Autoscaler
│       └── network-policy.yaml # Network security policies
└── README.md                    # This file
```

## ⚙️ Configuration Management

### Environment-Specific Configurations

#### Development Environment
- **Replicas**: 1
- **Resources**: Low (128Mi memory, 100m CPU)
- **Service Type**: NodePort (easy local access)
- **Log Level**: DEBUG
- **Storage**: 1Gi
- **AI Provider**: Ollama (local)

#### Production Environment
- **Replicas**: 3 (with HPA scaling 3-10)
- **Resources**: High (512Mi-1Gi memory, 500m-1000m CPU)
- **Service Type**: ClusterIP with Ingress
- **Log Level**: INFO
- **Storage**: 10Gi
- **Network Policies**: Enabled
- **TLS**: Enabled via Ingress
- **AI Provider**: Configurable (Ollama/OpenAI/Gemini)

### AI Provider Options

The deployment includes **three AI provider options**:

#### 🤖 Ollama (Default - Included)
- **Deployment**: Automatically deployed in cluster
- **Model**: `jimscard/whiterabbit-neo:latest`
- **Storage**: 20Gi for models
- **Resources**: 2-4Gi memory, 1-2 CPU cores
- **API Keys**: None required (local deployment)
- **Advantages**: Privacy, no external dependencies, cost-effective

#### ☁️ OpenAI (Cloud)
- **Configuration**: Requires Portkey + OpenAI Virtual Key
- **Models**: GPT-3.5-turbo, GPT-4, etc.
- **API Keys**: `PORTKEY_API_KEY` + `OPENAI_VIRTUAL_KEY`
- **Advantages**: High-quality responses, latest models

#### 🧠 Gemini (Cloud)
- **Configuration**: Requires Portkey + Gemini Virtual Key  
- **Models**: Gemini-pro, Gemini-ultra, etc.
- **API Keys**: `PORTKEY_API_KEY` + `GEMINI_VIRTUAL_KEY`
- **Advantages**: Google's advanced AI, competitive pricing

### Customizing Configurations

#### Update ConfigMap Values
```bash
# Edit the configmap
kubectl edit configmap falco-ai-alerts-config -n falco-ai-alerts

# Or patch specific values
kubectl patch configmap falco-ai-alerts-config -n falco-ai-alerts \
  --patch '{"data":{"LOG_LEVEL":"DEBUG","MIN_PRIORITY":"informational"}}'
```

#### Update Secrets
```bash
# Update Slack token
kubectl patch secret falco-ai-alerts-secrets -n falco-ai-alerts \
  --patch '{"stringData":{"SLACK_BOT_TOKEN":"xoxb-new-token"}}'

# Update AI provider keys
kubectl patch secret falco-ai-alerts-secrets -n falco-ai-alerts \
  --patch '{"stringData":{"OPENAI_VIRTUAL_KEY":"new-key"}}'
```

## 🔒 Security Considerations

### RBAC (Role-Based Access Control)
The deployment includes minimal RBAC permissions:
- Read access to pods, services, endpoints
- Read access to deployments and replicasets
- No write permissions to cluster resources

### Network Security
Production deployment includes NetworkPolicy that:
- Restricts ingress to ingress controller, Falco, and monitoring
- Limits egress to DNS, HTTPS (AI providers), and Slack
- Blocks all other network traffic

### Pod Security
- **Non-root user**: Runs as UID 1000
- **Read-only filesystem**: Except for /tmp and /app/data
- **No privilege escalation**: Security context prevents escalation
- **Minimal capabilities**: Drops all unnecessary Linux capabilities

### Secrets Management
- Use external secret management (e.g., HashiCorp Vault, AWS Secrets Manager)
- Rotate secrets regularly
- Never commit secrets to version control

## 📊 Monitoring and Observability

### Health Checks
```bash
# Check application health
kubectl get pods -n falco-ai-alerts
kubectl describe pod <pod-name> -n falco-ai-alerts

# Check health endpoint
kubectl port-forward svc/falco-ai-alerts 8080:8080 -n falco-ai-alerts
curl http://localhost:8080/health
```

### Logs
```bash
# View application logs
kubectl logs -f deployment/falco-ai-alerts -n falco-ai-alerts

# View logs from all pods
kubectl logs -f -l app.kubernetes.io/name=falco-ai-alerts -n falco-ai-alerts

# Filter logs by level
kubectl logs deployment/falco-ai-alerts -n falco-ai-alerts | grep ERROR
```

### Metrics (Prometheus Integration)
The deployment includes Prometheus annotations:
```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8080"
  prometheus.io/path: "/health"
```

### Resource Monitoring
```bash
# Monitor resource usage
kubectl top pods -n falco-ai-alerts
kubectl top nodes

# Check HPA status
kubectl get hpa -n falco-ai-alerts
kubectl describe hpa falco-ai-alerts-hpa -n falco-ai-alerts
```

## 🔧 Operational Procedures

### Scaling
```bash
# Manual scaling
kubectl scale deployment falco-ai-alerts --replicas=5 -n falco-ai-alerts

# Update HPA limits
kubectl patch hpa falco-ai-alerts-hpa -n falco-ai-alerts \
  --patch '{"spec":{"maxReplicas":15}}'
```

### Updates and Rollbacks
```bash
# Update image
kubectl set image deployment/falco-ai-alerts falco-ai-alerts=your-registry/falco-ai-alerts:v1.1.0 -n falco-ai-alerts

# Check rollout status
kubectl rollout status deployment/falco-ai-alerts -n falco-ai-alerts

# Rollback if needed
kubectl rollout undo deployment/falco-ai-alerts -n falco-ai-alerts

# View rollout history
kubectl rollout history deployment/falco-ai-alerts -n falco-ai-alerts
```

### Backup and Recovery
```bash
# Backup configuration
kubectl get configmap falco-ai-alerts-config -n falco-ai-alerts -o yaml > config-backup.yaml
kubectl get secret falco-ai-alerts-secrets -n falco-ai-alerts -o yaml > secrets-backup.yaml

# Backup persistent data (depends on your storage solution)
kubectl get pvc falco-ai-alerts-data -n falco-ai-alerts -o yaml > pvc-backup.yaml
```

### Database Maintenance
```bash
# Access database for maintenance
kubectl exec -it deployment/falco-ai-alerts -n falco-ai-alerts -- /bin/bash

# Inside the container:
# sqlite3 /app/data/alerts.db
# .schema
# SELECT COUNT(*) FROM alerts;
# .quit
```

## 🐛 Troubleshooting

### Common Issues

#### Pods Not Starting
```bash
# Check pod events
kubectl describe pod <pod-name> -n falco-ai-alerts

# Check logs
kubectl logs <pod-name> -n falco-ai-alerts

# Common causes:
# - Image pull errors
# - Resource constraints
# - Configuration errors
# - Storage issues
```

#### Service Not Accessible
```bash
# Check service endpoints
kubectl get endpoints falco-ai-alerts -n falco-ai-alerts

# Test service connectivity
kubectl run debug --image=busybox --rm -it --restart=Never -- \
  wget -qO- http://falco-ai-alerts.falco-ai-alerts.svc.cluster.local:8080/health
```

#### Ingress Issues
```bash
# Check ingress configuration
kubectl describe ingress falco-ai-alerts-ingress -n falco-ai-alerts

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

#### Storage Issues
```bash
# Check PVC status
kubectl get pvc -n falco-ai-alerts
kubectl describe pvc falco-ai-alerts-data -n falco-ai-alerts

# Check storage class
kubectl get storageclass
```

### Debug Mode
Enable debug logging:
```bash
kubectl patch configmap falco-ai-alerts-config -n falco-ai-alerts \
  --patch '{"data":{"LOG_LEVEL":"DEBUG"}}'

kubectl rollout restart deployment/falco-ai-alerts -n falco-ai-alerts
```

## 🗑️ Uninstall and Cleanup

### 🚀 **Quick Install: Use the Installation Script**

We provide an automated installation script for easy deployment:

```bash
# Install development environment
./install.sh dev

# Install production environment  
./install.sh prod

# Validate configuration only
./install.sh dev --validate-only

# Get help with all options
./install.sh --help
```

The script provides:
- ✅ **Prerequisite checking** (kubectl, cluster access, kustomize)
- ✅ **Configuration validation** (syntax and dependency checks)
- ✅ **Automated deployment** (applies manifests and waits for readiness)
- ✅ **Secret setup guidance** (shows commands for API keys)
- ✅ **Access instructions** (port-forward commands and URLs)
- ✅ **Post-install guidance** (configuration and testing steps)

## 🗑️ **Quick Cleanup: Use the Cleanup Script**

We also provide an automated cleanup script for easy uninstallation:

```bash
# Clean up development environment (with backup)
./cleanup.sh dev

# Clean up production environment and delete all data
./cleanup.sh prod --delete-data

# Clean up everything without prompts
./cleanup.sh all --force

# Get help with all options
./cleanup.sh --help
```

The script provides:
- ✅ **Automatic backups** (database and configuration)
- ✅ **Graceful shutdown** (scale to 0 before deletion)
- ✅ **Safety confirmations** (prevents accidental deletion)
- ✅ **Cleanup verification** (ensures complete removal)
- ✅ **Error handling** (robust cleanup even if some resources fail)

### Complete Uninstall Instructions

#### ⚠️ **IMPORTANT: Data Backup First!**
```bash
# 1. Backup your database before cleanup
kubectl exec deployment/falco-ai-alerts -n falco-ai-alerts -- \
  cp /app/data/alerts.db /tmp/alerts-backup-$(date +%Y%m%d).db

# 2. Copy backup to local machine
kubectl cp falco-ai-alerts/$(kubectl get pods -n falco-ai-alerts -l app.kubernetes.io/name=falco-ai-alerts -o jsonpath='{.items[0].metadata.name}'):/tmp/alerts-backup-$(date +%Y%m%d).db ./alerts-backup.db

# 3. Backup configuration (optional)
kubectl get configmap,secret -n falco-ai-alerts -o yaml > config-backup.yaml
```

#### 🧹 **Development Environment Cleanup**
```bash
# Delete development deployment
kubectl delete -k overlays/development/

# Verify removal
kubectl get all -n falco-ai-alerts-dev
# Should show: No resources found in falco-ai-alerts-dev namespace.

# Clean up persistent volumes (⚠️ This deletes all data!)
kubectl delete pvc --all -n falco-ai-alerts-dev

# Remove namespace (this removes everything)
kubectl delete namespace falco-ai-alerts-dev

# Clean up cluster-wide resources
kubectl delete clusterrole dev-falco-ai-alerts
kubectl delete clusterrolebinding dev-falco-ai-alerts
```

#### 🏭 **Production Environment Cleanup**
```bash
# ⚠️ PRODUCTION WARNING: This will delete your production system!
# Make sure you have backups and approval for this operation.

# Step 1: Scale down to prevent new alerts
kubectl scale deployment prod-falco-ai-alerts --replicas=0 -n falco-ai-alerts

# Step 2: Wait for graceful shutdown
kubectl wait --for=delete pod -l app.kubernetes.io/name=falco-ai-alerts -n falco-ai-alerts --timeout=60s

# Step 3: Delete the deployment
kubectl delete -k overlays/production/

# Step 4: Clean up persistent data (⚠️ IRREVERSIBLE!)
kubectl delete pvc --all -n falco-ai-alerts

# Step 5: Remove namespace
kubectl delete namespace falco-ai-alerts

# Step 6: Clean up cluster-wide resources
kubectl delete clusterrole prod-falco-ai-alerts
kubectl delete clusterrolebinding prod-falco-ai-alerts
```

#### 🔍 **Verification Steps**
```bash
# 1. Check no resources remain
kubectl get all,pvc,secrets,configmaps -n falco-ai-alerts
kubectl get all,pvc,secrets,configmaps -n falco-ai-alerts-dev

# 2. Check cluster-wide resources
kubectl get clusterrole | grep falco-ai-alerts
kubectl get clusterrolebinding | grep falco-ai-alerts

# 3. Check for stuck finalizers
kubectl get namespace falco-ai-alerts -o yaml
kubectl get namespace falco-ai-alerts-dev -o yaml

# Should show: Error from server (NotFound) for successful cleanup
```

#### 🚨 **Troubleshooting Stuck Resources**

##### Namespace Stuck in "Terminating"
```bash
# Check what's preventing deletion
kubectl get all -n falco-ai-alerts
kubectl describe namespace falco-ai-alerts

# Force remove finalizers (last resort)
kubectl patch namespace falco-ai-alerts -p '{"metadata":{"finalizers":[]}}' --type=merge
kubectl patch namespace falco-ai-alerts-dev -p '{"metadata":{"finalizers":[]}}' --type=merge
```

##### Persistent Volumes Stuck
```bash
# Check PV status
kubectl get pv | grep falco-ai-alerts

# Force delete PVs if stuck
kubectl patch pv <pv-name> -p '{"metadata":{"finalizers":[]}}' --type=merge
kubectl delete pv <pv-name> --force --grace-period=0
```

##### Pods Stuck in Terminating
```bash
# Check pod status
kubectl get pods -n falco-ai-alerts --field-selector=status.phase!=Running

# Force delete stuck pods
kubectl delete pod <pod-name> -n falco-ai-alerts --force --grace-period=0
```

#### 🔄 **Selective Cleanup (Keep Data)**

If you want to remove the application but keep your data:

```bash
# Remove application but keep PVCs
kubectl delete deployment,service,ingress,hpa,networkpolicy -n falco-ai-alerts
kubectl delete deployment,service,ingress,hpa,networkpolicy -n falco-ai-alerts-dev

# Keep: PVCs, Secrets, ConfigMaps, Namespace
# This preserves your alert database and configuration
```

#### 📦 **Clean Reinstall Process**
```bash
# 1. Complete cleanup (including data)
kubectl delete -k overlays/production/
kubectl delete pvc --all -n falco-ai-alerts
kubectl delete namespace falco-ai-alerts

# 2. Wait for complete removal
kubectl get namespace | grep falco-ai-alerts
# Should show no results

# 3. Fresh install
kubectl apply -k overlays/production/

# 4. Restore data (if you have backups)
kubectl cp ./alerts-backup.db falco-ai-alerts/$(kubectl get pods -n falco-ai-alerts -l app.kubernetes.io/name=falco-ai-alerts -o jsonpath='{.items[0].metadata.name}'):/app/data/alerts.db
```

### 📋 **Cleanup Checklist**

#### Pre-Cleanup
- [ ] **Backup Database**: Export alert data and configuration
- [ ] **Team Notification**: Inform team about planned downtime  
- [ ] **Falco Configuration**: Update Falco to stop sending alerts
- [ ] **Monitoring**: Disable alerts for the cleanup period
- [ ] **Access Verification**: Ensure you have cluster admin access

#### During Cleanup
- [ ] **Scale Down**: Gracefully scale replicas to 0
- [ ] **Wait for Drain**: Allow pods to finish processing
- [ ] **Delete Resources**: Remove application resources
- [ ] **Remove Data**: Delete PVCs and persistent data (if desired)
- [ ] **Clean Cluster Resources**: Remove cluster-wide RBAC

#### Post-Cleanup Verification
- [ ] **No Resources**: Verify no resources remain in namespaces
- [ ] **No Cluster Resources**: Check cluster-wide resources removed
- [ ] **No Stuck Objects**: Ensure no objects stuck in terminating state
- [ ] **Storage Cleanup**: Verify persistent volumes cleaned up
- [ ] **DNS Cleanup**: Ensure service DNS entries removed

### ⚡ **Quick Cleanup Commands**

#### Emergency Full Cleanup
```bash
# ⚠️ DANGER: This removes EVERYTHING immediately
kubectl delete namespace falco-ai-alerts falco-ai-alerts-dev --force --grace-period=0
kubectl delete clusterrole,clusterrolebinding -l app.kubernetes.io/name=falco-ai-alerts
```

#### Development Only
```bash
kubectl delete -k overlays/development/ && kubectl delete namespace falco-ai-alerts-dev
```

#### Production Only  
```bash
kubectl delete -k overlays/production/ && kubectl delete namespace falco-ai-alerts
```

## 🚀 Advanced Deployments

### Multi-Region Setup
For high availability across regions:
1. Deploy in multiple clusters
2. Use external database (PostgreSQL, MySQL)
3. Implement cross-cluster service mesh
4. Configure global load balancing

### GitOps Integration
Use ArgoCD or Flux for GitOps deployment:
```yaml
# argocd-application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: falco-ai-alerts
  namespace: argocd
spec:
  project: default
  source:
    repoURL: <your-git-repo>
    targetRevision: HEAD
    path: k8s/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: falco-ai-alerts
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Helm Chart Alternative
If you prefer Helm, convert the Kustomize manifests:
```bash
helm template falco-ai-alerts ./k8s/base --namespace falco-ai-alerts > helm-output.yaml
```

## 📝 Contributing

To contribute to the Kubernetes deployment:
1. Test changes in development environment
2. Update documentation for any new features
3. Follow Kubernetes best practices
4. Ensure security compliance
5. Submit pull request with deployment tests

## 📞 Support

For deployment issues:
- Check the troubleshooting section
- Review Kubernetes events: `kubectl get events -n falco-ai-alerts`
- Check application logs
- Open an issue with deployment details

---

🎉 **Your Falco AI Alert System is now ready for Kubernetes deployment!**

Start with the development overlay for testing, then move to production when ready. 