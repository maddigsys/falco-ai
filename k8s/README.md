# Kubernetes Deployment Guide - Falco AI Alert System

**Version: v2.1.0** (with enhanced chat features, audit system, and MCP Hub)

This guide provides comprehensive instructions for deploying the Falco AI Alert System on Kubernetes.

## 📋 Prerequisites

### Kubernetes Cluster Requirements
- **Kubernetes Version**: 1.19+
- **Container Runtime**: Docker, containerd, or CRI-O
- **Storage**: Default StorageClass or specific storage configuration
- **Ingress Controller**: NGINX Ingress Controller (recommended)
- **DNS**: CoreDNS or kube-dns

### ☁️ **Cloud Deployment**
For cloud-specific deployments (EKS, GKE, AKS), see the **[Cloud Deployment Guide](CLOUD_DEPLOYMENT_GUIDE.md)** for platform-specific constraints and solutions.

> **⚠️ CRITICAL**: Cloud deployments require minimum **8GB RAM nodes** and **SSD storage classes**. Standard/small nodes will cause deployment failures.

### 🔧 **Resource Requirements**

#### **Development Environment** (Single-node testing)
- **Memory**: 8GB available RAM (6GB for Ollama 8B model + 2GB for app)
- **CPU**: 2 cores minimum
- **Storage**: 15GB available storage
- **Model**: `phi3:mini` (default, fastest, most reliable)

#### **Production Environment** (Multi-node cluster)
- **Memory**: 10GB available RAM (8GB for Ollama 8B model + 2GB for app)
- **CPU**: 4 cores minimum
- **Storage**: 20GB available storage
- **Model**: `phi3:mini` (default for speed and reliability)
- **Cybersecurity Upgrade**: `jimscard/whiterabbit-neo:latest` (optional, requires 18GB RAM)

#### **Enterprise Environment** (High-performance cybersecurity)
- **Memory**: 18GB+ available RAM (for cybersecurity-specialized models)
- **CPU**: 8+ cores
- **Storage**: 30GB+ available storage
- **Model**: `jimscard/whiterabbit-neo:latest` (cybersecurity-optimized 13B model)
- **Note**: Slower inference (15-30s) but superior security analysis

📖 **See [OLLAMA_MODELS.md](OLLAMA_MODELS.md) for detailed model selection and resource planning guide.**
📖 **See [OLLAMA_TIMEOUT_GUIDE.md](OLLAMA_TIMEOUT_GUIDE.md) for configuring timeouts based on model size and environment.**

### Required Cluster Add-ons
- **Metrics Server**: For HPA functionality
- **Cert-Manager**: For TLS certificate management (optional)
- **Prometheus**: For monitoring (optional but recommended)

### Tools Required
- `kubectl` (version compatible with your cluster)
- `kustomize` (v3.2.0+) or `kubectl` with kustomize support
- `docker` (for building custom images)
- `helm` (optional, for managing dependencies)

## ✨ New Features in v2.1.0

### 💬 Enhanced Chat Interface
- **Standard Chat Features**: Clear history, message search, export (Text/Markdown/JSON)
- **Server-Side Synchronization**: Chat history automatically synced to backend database
- **Real-Time Search**: Find previous conversations with highlighting
- **Message Management**: Copy messages, timestamps, persistent storage
- **Multi-Language Support**: Chat in any language with AI responses in same language
- **Persona Selection**: Switch between Security Analyst, Incident Responder, Threat Hunter

### 🔒 Comprehensive Audit System
- **Complete Activity Tracking**: All user actions logged with full audit trails
- **Advanced Filtering**: Filter by user, action type, time range, resource type
- **Real-Time Statistics**: Activity summaries and performance monitoring
- **Export Capabilities**: Export audit logs in CSV/JSON formats with pagination
- **Anonymous User Identification**: Track users via IP+User-Agent hashing
- **Session Analytics**: Session correlation and detailed event inspection

### ⚡ Real-Time Features
- **Server-Sent Events (SSE)**: Live status updates across all connected clients
- **Multi-Client Synchronization**: Real-time collaboration for security teams
- **Enhanced Visual Indicators**: Glowing borders, animations, and status notifications
- **Keyboard Shortcuts**: Efficient navigation (R=read, D=dismiss, arrows=navigate)
- **Connection Status**: Real-time indicators for SSE connectivity

### 🎛️ MCP Hub (Model Context Protocol)
- **Unified Dashboard**: Renamed from "MCP Integration Hub" to "MCP Hub" for simplicity
- **Multi-Protocol Support**: JSON-RPC, Claude-optimized, gRPC, and Standard MCP
- **Auto-Setup Scripts**: One-click configuration for Claude Desktop, VS Code, Cursor
- **Web Configuration**: Real-time testing and setup interface
- **15 Security Tools**: Direct access to Falco security capabilities via MCP

### 🛠️ Technical Improvements
- **Enhanced Database Schema**: New audit tables and optimized indexes
- **Thread-Safe Operations**: Improved client management with auto-cleanup
- **Better Error Handling**: Enhanced user feedback and notification system
- **Performance Optimizations**: Memory management and efficient data handling
- **Responsive Design**: Improved mobile and tablet compatibility

### 📊 Advanced Filtering & Analytics
- **Debounced Text Filtering**: Smooth performance with automatic filtering
- **Filter Save/Load**: Save frequently used filter configurations
- **Bulk Operations**: Enhanced bulk actions with confirmation dialogs
- **Enhanced Semantic Search**: Better integration with Weaviate
- **Session Management**: Improved conversation persistence and retrieval

## 🏗️ Multi-Architecture & Cloud Support

### 🔧 **Multi-Architecture Container Support**

The v2.1.0 container images are built for **multiple architectures** to support diverse cloud environments:

| Architecture | Cloud Platforms | Instance Types |
|--------------|-----------------|----------------|
| **AMD64 (x86_64)** | All cloud providers | Standard compute instances |
| **ARM64 (aarch64)** | AWS Graviton2/3, GCP Tau T2A, Azure Ampere | Cost-optimized ARM instances |

**Benefits of Multi-Architecture Support:**
- 📉 **Cost Savings**: ARM instances offer 20-40% cost reduction
- ⚡ **Performance**: Native ARM execution eliminates emulation overhead
- 🌍 **Compatibility**: Single deployment works across all architectures
- 🔄 **Future-Proof**: Ready for emerging ARM-based cloud offerings

### ☁️ **Cloud-Specific Optimizations**

#### **AWS EKS (`overlays/eks/`)** - **✅ MULTI-ARCHITECTURE READY**
- **Storage**: GP3 volumes for cost-effective SSD performance
- **Load Balancer**: AWS ALB with SSL termination
- **Instance Types**: **Multi-architecture support** (AMD64: t3/m5, ARM64: t4g/m6g)
- **Cost Optimization**: ARM64 Graviton instances provide 20-40% cost savings
- **Networking**: VPC CNI integration with Security Groups for Pods
- **IAM**: IRSA (IAM Roles for Service Accounts) support
- **Testing**: Fully tested on both x86_64 and arm64 architectures

#### **Google GKE (`overlays/gke/`)**
- **Storage**: Premium-RWO (SSD) for performance-critical workloads
- **Load Balancer**: Google Cloud Load Balancer with NEG
- **Instance Types**: Optimized for standard and Tau T2A ARM instances
- **Networking**: VPC-native networking
- **Identity**: Workload Identity integration

#### **Azure AKS (`overlays/aks/`)**
- **Storage**: Managed-CSI-Premium for SSD performance
- **Load Balancer**: Azure Load Balancer with health probes
- **Instance Types**: Optimized for standard and Ampere Altra ARM instances
- **Networking**: Azure CNI integration
- **Identity**: Managed Identity support

### 🏷️ **Container Image Tags**

```bash
# Multi-architecture manifest (recommended)
maddigsys/falco-ai-alerts:v2.1.0  # Production deployments
maddigsys/falco-ai-alerts:latest  # Development deployments

# Architecture-specific (if needed)
maddigsys/falco-ai-alerts:v2.1.0-amd64
maddigsys/falco-ai-alerts:v2.1.0-arm64
```

**Image Tag Strategy:**
- 🔧 **Development environments** (`overlays/development/`, `dev-*`, `development-*`): Use `:latest` tag for rapid iteration
- 🚀 **Production environments** (`overlays/production/`, `eks/`, `gke/`, `aks/`): Use specific version tags (e.g., `v2.1.0`) for stability

**Kubernetes automatically selects the correct architecture** based on your node's CPU architecture.

### 🚀 **Cloud Deployment Recommendations**

#### **Cost-Optimized Deployment (ARM64)**
```bash
# Use ARM64 node pools for 20-40% cost savings
# AWS: t4g, m6g, c6g instance families
# GCP: t2a instance family  
# Azure: Dpsv5, Epsv5 instance families

kubectl apply -k overlays/eks/    # AWS EKS
kubectl apply -k overlays/gke/    # Google GKE  
kubectl apply -k overlays/aks/    # Azure AKS
```

#### **Performance-Optimized Deployment (AMD64)**
```bash
# Use high-performance AMD64 instances
# AWS: c5, m5, r5 instance families
# GCP: c2, n2 instance families
# Azure: Fsv2, Dsv3 instance families

kubectl apply -k overlays/production/  # Generic high-performance
```

#### **Hybrid Deployment (Mixed Architecture)**
```bash
# Deploy with node affinity for specific workloads
# AI inference: ARM64 (cost-effective)
# Vector database: AMD64 (performance)
# Web frontend: Either architecture
```

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

**For Development Environment:**
```bash
# Create the namespace first
kubectl apply -f base/namespace.yaml

# Create secrets for development environment
kubectl create secret generic dev-falco-ai-alerts-secrets \
  --from-literal=SLACK_BOT_TOKEN="xoxb-your-slack-bot-token" \
  --from-literal=PORTKEY_API_KEY="pk-your-portkey-api-key" \
  --from-literal=OPENAI_VIRTUAL_KEY="openai-your-virtual-key" \
  --from-literal=GEMINI_VIRTUAL_KEY="gemini-your-virtual-key" \
  --from-literal=DB_ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --namespace falco-ai-alerts-dev
```

**For Production Environment:**
```bash
# Create the namespace first  
kubectl apply -f base/namespace.yaml

# Create secrets for production environment
kubectl create secret generic prod-falco-ai-alerts-secrets \
  --from-literal=SLACK_BOT_TOKEN="xoxb-your-slack-bot-token" \
  --from-literal=PORTKEY_API_KEY="pk-your-portkey-api-key" \
  --from-literal=OPENAI_VIRTUAL_KEY="openai-your-virtual-key" \
  --from-literal=GEMINI_VIRTUAL_KEY="gemini-your-virtual-key" \
  --from-literal=DB_ENCRYPTION_KEY="$(openssl rand -base64 32)" \
  --namespace falco-ai-alerts

# Note: For Ollama (default), no API keys needed - it runs locally in the cluster!
```

**🔑 Secret Key Reference:**
| Key Name | Required | Description | Example Format |
|----------|----------|-------------|----------------|
| `SLACK_BOT_TOKEN` | ✅ Yes | Slack bot token | `xoxb-1234-5678-abcd` |
| `PORTKEY_API_KEY` | ☁️ Cloud AI | Portkey security layer key | `pk-abc123...` |
| `OPENAI_VIRTUAL_KEY` | ☁️ OpenAI | OpenAI virtual key via Portkey | `openai_vk_abc123...` |
| `GEMINI_VIRTUAL_KEY` | ☁️ Gemini | Gemini virtual key via Portkey | `gemini_vk_abc123...` |
| `DB_ENCRYPTION_KEY` | 🔐 Security | Database encryption | `$(openssl rand -base64 32)` |

**📝 Setup Guide:**
1. **Slack**: Create bot at https://api.slack.com/apps
2. **Portkey**: Sign up at https://portkey.ai for cloud AI security
3. **OpenAI**: Add OpenAI to Portkey, get virtual key
4. **Gemini**: Add Gemini to Portkey, get virtual key
5. **Ollama**: No setup needed (included in deployment)

#### 3. Deploy Development Environment
```bash
# Deploy to development (uses :latest tag automatically)
kubectl apply -k overlays/development/

# Check deployment status
kubectl get pods -n falco-ai-alerts-dev
kubectl logs -f deployment/dev-falco-ai-alerts -n falco-ai-alerts-dev

# Access the application
kubectl port-forward svc/dev-falco-ai-alerts 8080:8080 -n falco-ai-alerts-dev
# Open http://localhost:8080/dashboard
```

#### 4. Deploy Production Environment

**🌩️ Cloud-Managed Kubernetes Deployment (Recommended)**

For cloud-managed Kubernetes services, use the cloud-specific optimized overlays:

```bash
# AWS EKS (with Graviton2/ARM64 support) - RECOMMENDED FOR TESTING
kubectl apply -k overlays/eks/

# Google GKE (with Tau T2A/ARM64 support) 
kubectl apply -k overlays/gke/

# Azure AKS (with Ampere Altra/ARM64 support)
kubectl apply -k overlays/aks/

# Verify deployment
kubectl get all -n falco-ai-alerts
kubectl get hpa -n falco-ai-alerts

# EKS-specific: Verify multi-architecture deployment
kubectl get nodes -o custom-columns=NAME:.metadata.name,ARCH:.status.nodeInfo.architecture,INSTANCE:.metadata.labels.node\.kubernetes\.io/instance-type
kubectl get pods -n falco-ai-alerts -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName
```

**🖥️ Generic Production Deployment**

```bash
# Generic production deployment
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
- **Default Model**: `phi3:mini` (fastest, most reliable, 2.3GB)
- **Performance Upgrades**: `llama3.1:8b` (8B, balanced), `jimscard/whiterabbit-neo:latest` (13B, cybersecurity specialist)
- **Storage**: 15Gi for default model (30Gi for cybersecurity model)
- **Resources**: 6-8Gi memory for 8B (14-16Gi for 13B cybersecurity model)
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

## 🌐 Accessing v2.1.0 Features

Once deployed, you can access all the new v2.1.0 features through the web interface:

### **1. 💬 Enhanced Chat Interface**
```bash
# Access the AI Security Assistant
kubectl port-forward svc/falco-ai-alerts 8080:8080 -n falco-ai-alerts
# Open: http://localhost:8080/enhanced-chat
```

**New Features Available:**
- **Standard Chat Controls**: Clear, search, export, history management
- **Server-Side Sync**: Your conversations persist across sessions
- **Real-Time Search**: Find any previous conversation instantly
- **Export Options**: Download chat history in Text, Markdown, or JSON
- **Multi-Language Support**: Chat in any language, AI responds in kind
- **Persona Selection**: Choose from Security Analyst, Incident Responder, or Threat Hunter

### **2. 🔒 Comprehensive Audit System**
```bash
# Access the audit dashboard
# Open: http://localhost:8080/audit
```

**Audit Capabilities:**
- **Complete Activity Tracking**: Every user action logged with full context
- **Advanced Filtering**: Filter by user, action type, time range, resource
- **Real-Time Statistics**: Live activity summaries and performance monitoring
- **Export Functions**: Download audit logs in CSV or JSON formats
- **Anonymous User Tracking**: Users identified via IP+User-Agent hashing
- **Session Analytics**: Detailed session correlation and event inspection

### **3. ⚡ Real-Time Collaboration**
**Server-Sent Events (SSE)** for live updates:
- **Multi-Client Sync**: All connected users see updates instantly
- **Real-Time Status**: Alert status changes broadcast to all clients
- **Live Notifications**: New alerts appear immediately across all sessions
- **Connection Status**: Visual indicators show SSE connectivity

### **4. 🎛️ MCP Hub (Model Context Protocol)**
```bash
# Access the unified MCP Hub
# Open: http://localhost:8080/mcp-dashboard
```

**Available Protocols:**
- **JSON-RPC MCP**: Universal AI client compatibility (Claude Desktop, VS Code, Cursor)
- **Claude-Optimized MCP**: Enhanced Claude Desktop experience
- **gRPC MCP**: High-performance streaming (10x faster throughput)
- **Standard MCP**: Traditional HTTP/WebSocket implementations

**15 Security Tools Available:**
- Alert retrieval and analysis
- AI-powered threat assessment
- Interactive security chat
- Dashboard data access
- Semantic search capabilities
- And 10+ more security tools

### **5. 📊 Enhanced Dashboard Features**
```bash
# Access the improved dashboard
# Open: http://localhost:8080/
```

**New Dashboard Capabilities:**
- **Advanced Filtering**: Comprehensive alert filtering with save/load
- **Keyboard Shortcuts**: Efficient navigation (R=read, D=dismiss, arrows=navigate)
- **Visual Enhancements**: Glowing borders, animations, status indicators
- **Bulk Operations**: Enhanced bulk actions with confirmation dialogs
- **Real-Time Updates**: Live alert status synchronization

### **6. 🔍 Advanced Analytics**
```bash
# Access AI-powered analytics
# Open: http://localhost:8080/weaviate-analytics
```

**Analytics Features:**
- **ML-Driven Clustering**: Automatic threat pattern detection
- **Semantic Search**: Natural language security event queries
- **Threat Intelligence**: AI-powered security insights
- **Real-Time Insights**: Live security analytics and reporting

### **Post-Deployment Quick Start Guide**

1. **Configure Slack Integration** (if not done during install):
   ```bash
   # Update Slack token in secret
   kubectl patch secret falco-ai-alerts-secrets -n falco-ai-alerts \
     --patch='{"data":{"SLACK_BOT_TOKEN":"'$(echo -n "xoxb-your-token" | base64)'"}}'
   ```

2. **Set Up Falco Webhook** (point Falco to your deployment):
   ```yaml
   # In your falco.yaml
   http_output:
     enabled: true
     url: http://falco-ai-alerts.falco-ai-alerts.svc.cluster.local:8080/falco-webhook
   ```

3. **Test the System**:
   ```bash
   # Send a test alert
   curl -X POST http://localhost:8080/api/test-alert
   ```

4. **Explore the MCP Hub** (for AI client integration):
   - Visit the MCP Hub dashboard
   - Choose your preferred protocol (JSON-RPC recommended)
   - Follow auto-setup instructions for your AI client

5. **Enable Advanced Features**:
   - Configure audit system for compliance requirements
   - Set up real-time SSE connections for team collaboration
   - Customize chat personas for different security analysis needs

### **📋 Operational Commands Reference**

For comprehensive day-to-day operational commands including port forwarding, UI access, log checking, and troubleshooting, see the **[Operational Commands Guide](OPERATIONAL_COMMANDS.md)**.

This guide includes:
- 🌐 **Port forwarding commands** for all environments and components
- 📊 **Log checking** for applications, Ollama, Weaviate, and Kubernetes events
- 🔍 **Status monitoring** for deployments, health checks, and resource usage
- ⚙️ **Configuration management** for ConfigMaps and Secrets
- 🔧 **Scaling and resource management** commands
- 🗄️ **Database operations** including backup and restore
- 🚨 **Troubleshooting** for common deployment issues
- 🔄 **Deployment management** for updates and rollbacks

**Quick Access Example:**
```bash
# Port forward and access the UI
kubectl port-forward svc/dev-falco-ai-alerts 8080:8080 -n falco-ai-alerts-dev
# Then open: http://localhost:8080/
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
- ✅ **Progress monitoring** (real-time AI model download with progress bar and ETA)
- ✅ **Secret setup guidance** (shows commands for API keys)
- ✅ **Access instructions** (port-forward commands and URLs)
- ✅ **Post-install guidance** (configuration and testing steps)

## 🔐 **Standardized Secret Creation**

**Important**: All deployment methods (script, manual, README) now use consistent secret naming and key structures.

### **Secret Naming Convention**
- **Development**: `dev-falco-ai-alerts-secrets` in `falco-ai-alerts-dev` namespace
- **Production**: `prod-falco-ai-alerts-secrets` in `falco-ai-alerts` namespace

### **Required Secret Keys** 
All environments use the same key structure:
```bash
SLACK_BOT_TOKEN="xoxb-your-slack-bot-token"
PORTKEY_API_KEY="pk-your-portkey-api-key"  
OPENAI_VIRTUAL_KEY="openai-your-virtual-key"
GEMINI_VIRTUAL_KEY="gemini-your-virtual-key"
DB_ENCRYPTION_KEY="$(openssl rand -base64 32)"
```

### **Automated Secret Creation**
The install script will guide you through creating secrets with the correct names and keys.

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

## 🌗 Dark/Light Mode Toggle

- The UI now includes a theme toggle button (moon/sun icon) in the top navigation bar.
- Click to instantly switch between dark and light mode.
- Your preference is saved and persists across sessions.
- All major UI elements are styled for both themes.

--- 