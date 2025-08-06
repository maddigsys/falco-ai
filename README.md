# Falco Vanguard

> **⚠️ EXPERIMENTAL REPOSITORY DISCLAIMER**  
> This repository is currently under active development and is considered experimental. Some features may not work as expected, and breaking changes may occur without notice. Use at your own risk in production environments. Please report issues and contribute feedback to help improve the system.

A comprehensive security alert system that combines Falco runtime security with AI-powered analysis and an interactive web dashboard.

## Features

- **Real-time Falco webhook processing** - Receives and processes security alerts
- **AI-powered alert analysis** - Uses OpenAI, Gemini, or Ollama for intelligent analysis
- **Interactive Web Dashboard** - Real-time alert visualization with dark/light mode
- **Unified MCP Integration** - 15 security tools accessible via 4 MCP protocols (unified dashboard)
- **Slack Integration** - Sends analyzed alerts to Slack channels
- **Multi-Platform Kubernetes** - Auto-detects GKE, EKS, AKS, DOKS, IBM Cloud, and local K8s
- **Dynamic Configuration** - Optimizes storage classes and resources per platform
- **Multi-Architecture Support** - AMD64 and ARM64 Docker images
- **Multilingual Support** - AI analysis in multiple languages
- **Enhanced UI/UX** - Modern interface with responsive design

## System Architecture

![System Architecture](assets/Arch_Diagram.png)

*Comprehensive overview of the Falco Vanguard architecture showing data flow from Falco runtime security through AI analysis to various output channels.*

## Quick Start

> **Note**: This is experimental software. Please test thoroughly before using in production environments.

### Kubernetes (Recommended - Auto-Platform Detection)
```bash
# Clone the repository
git clone https://github.com/maddigsys/falco-vanguard.git
cd falco-vanguard/k8s

# One-command deployment (auto-detects GKE, EKS, AKS, etc.)
./install-dynamic.sh development

# Access Web UI (port-forward)
kubectl port-forward svc/dev-falco-ai-alerts 8080:8080 -n falco-ai-alerts-development
open http://localhost:8080/dashboard
```

### Docker Compose (Local Development)
```bash
# Clone the repository
git clone https://github.com/maddigsys/falco-vanguard.git
cd falco-vanguard

# Start the system
docker-compose up -d

# Access Web UI
open http://localhost:8080/dashboard
```

## Dashboard Features

The interactive web dashboard provides comprehensive security monitoring with multiple analysis views:

### Real-time Security Analysis
![Real-time Analysis](assets/HomeScreen_Realtime_Analysis.png)
*Live monitoring of security events with real-time threat detection and analysis.*

### Threat Intelligence
![Threat Intelligence](assets/HomeScreen_Threat_Intelligence.png)
*Advanced threat intelligence dashboard showing security patterns and indicators.*

### Alert Clustering
![Alert Clustering](assets/HomeScreen_Alert_Clustering.png)
*Intelligent alert clustering to reduce noise and identify related security events.*

### Pattern Analysis
![Pattern Analysis](assets/HomeScreen_Pattern_Analysis.png)
*Deep pattern analysis to detect anomalies and emerging security threats.*

### Docker Run (Quick Test)
```bash
# Run the latest version (multi-architecture: AMD64 + ARM64)
docker run -d -p 8080:8080 --name falco-vanguard maddigsys/falco-vanguard:v2.1.1

# Access Web UI
open http://localhost:8080/dashboard
```

## Multi-Platform Kubernetes Deployment

### 🚀 **Auto-Platform Detection**
The system automatically detects your Kubernetes platform and optimizes configurations:

| Platform | Storage Class | Resource Profile | Optimizations |
|----------|---------------|------------------|---------------|
| **GKE** | `premium-rwo` | 256Mi/100m → 512Mi/500m | Autopilot ready |
| **EKS** | `gp3` | 512Mi/250m → 1Gi/1000m | AWS optimized |
| **AKS** | `managed-premium` | 256Mi/100m → 512Mi/500m | Azure optimized |
| **DOKS** | `do-block-storage` | 256Mi/100m → 512Mi/500m | DO optimized |
| **Local** | `local-path` | 128Mi/50m → 256Mi/250m | Minimal resources |

### 🎯 **One-Command Deployment**
```bash
# Works on ANY Kubernetes platform
./install-dynamic.sh development

# Advanced usage
./install-dynamic.sh development detect    # Just detect platform
./install-dynamic.sh development generate  # Generate optimized config
./install-dynamic.sh development deploy    # Deploy with platform settings
```

### 📋 **Platform Detection Examples**
```bash
# Check your current platform
./detect-platform.sh
# Output: Platform: gke, Storage: premium-rwo, Resources: 256Mi/100m

# Generate platform-specific config
./generate-config.sh generate production
# Creates: overlays/production-auto/kustomization.yaml
```

For detailed documentation: [`k8s/DYNAMIC_DEPLOYMENT_GUIDE.md`](k8s/DYNAMIC_DEPLOYMENT_GUIDE.md)

### Environment Configuration
Create a `.env` file:
```bash
# AI Provider
PROVIDER_NAME=ollama  # or openai, gemini
PORTKEY_API_KEY=your-portkey-key  # Use 'portkey-ai' for OpenAI API Key

# Slack (optional)
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_NAME=#security-alerts

# Alert Configuration
MIN_PRIORITY=warning
```

### Falco Configuration
Configure Falco to send alerts to the webhook:
```yaml
# falco.yaml
json_output: true
http_output:
  enabled: true
  url: "http://your-server:8080/falco-webhook"
```

## Docker Images

### Multi-Architecture Support
The Docker images support both AMD64 and ARM64 architectures:

```bash
# Latest version (recommended)
docker pull maddigsys/falco-vanguard:v2.1.1

# Always latest
docker pull maddigsys/falco-vanguard:latest

# Platform-specific (if needed)
docker pull maddigsys/falco-vanguard:v2.1.1-amd64
```

### Available Tags
- `latest` - Latest stable release (multi-arch)
- `v2.1.1` - Current stable release (multi-arch)
- `v2.1.1-amd64` - AMD64 specific build
- `v2.0.0` - Previous stable release

## Legacy Kubernetes Deployment

```bash
# Static deployment (traditional method)
./k8s/install.sh development

# Dynamic deployment (recommended - auto-detects platform)
./k8s/install-dynamic.sh development
```

## API Endpoints

![API Explorer](assets/API_Explorer.png)
*Interactive API explorer showing available endpoints and their capabilities.*

- `POST /falco-webhook` - Receive Falco alerts
- `GET /dashboard` - Web UI dashboard
- `GET /api/alerts` - Get alerts with filtering
- `POST /api/chat` - AI chat interface
- `GET /mcp-dashboard` - MCP management interface
- `GET /runtime-events` - Enhanced events page with pagination

## MCP Tools

![AI Assistant](assets/AI_Assistant.png)
*AI-powered security assistant providing intelligent analysis and chat capabilities through MCP integration.*

The system includes 15 functional MCP (Model Context Protocol) tools:

- **Security Alerts**: `get_security_alerts`, `analyze_security_alert`, `chat_with_security_ai`
- **Threat Intelligence**: `get_threat_intelligence`, `predict_threats`
- **Analytics**: `cluster_alerts`, `get_alert_statistics`, `search_security_events`
- **Configuration**: `get_ai_config`, `get_slack_config`, `get_system_health`

## Recent Updates (v2.1.1)

### 🎨 **Branding & UI Updates**
- **Unified Branding**: Consistent "Falco Vanguard" branding throughout the application
- **Navigation Improvements**: Enhanced navigation bar with proper visual hierarchy
- **Template Updates**: Updated all templates and configuration files with new branding

### 🚀 **Multi-Platform Kubernetes Support**
- **Auto-Platform Detection**: Automatically detects GKE, EKS, AKS, DOKS, IBM Cloud, and local K8s
- **Dynamic Configuration**: Optimizes storage classes and resource limits per platform
- **One-Command Deployment**: `./install-dynamic.sh development` works everywhere
- **Multi-Architecture Docker**: AMD64 and ARM64 support in single images

### 🎨 **UI/UX Improvements**
- **Enhanced Dark/Light Mode**: Better theme compatibility and consistency
- **Runtime Events**: Fixed pagination and layout issues
- **Notifications**: Improved visibility and styling with dynamic backgrounds
- **Responsive Design**: Better mobile and desktop experience
- **Code Quality**: Removed debug styles and improved maintainability

### 🔧 **Infrastructure Enhancements**
- **Architecture Compatibility**: Fixed Docker image architecture mismatches
- **Storage Class Optimization**: Platform-specific storage class selection
- **Resource Optimization**: Tailored CPU/memory limits per cloud provider
- **Deployment Reliability**: Improved error handling and status monitoring

## Known Limitations & Issues

This is an experimental project with the following known limitations:

- **Experimental Features**: Some advanced features may not work as expected
- **Weaviate Connection**: Vector database connectivity may be unstable
- **AI Provider Configuration**: Complex setup required for cloud AI providers
- **Performance**: Not optimized for high-volume production workloads
- **Documentation**: Some features may lack complete documentation
- **Testing**: Limited test coverage for all features

**Reporting Issues**: Please report bugs and feature requests through GitHub Issues.

## License

MIT License - see LICENSE file for details.