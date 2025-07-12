# Falco AI Alert System with Integrated Web UI

> 🚀 **Production Ready!** A comprehensive security alert system that combines Falco runtime security with AI-powered analysis and an interactive web dashboard.

## ✨ Features

### 🛡️ Core Security Features
- **Real-time Falco webhook processing** - Receives and processes security alerts
- **AI-powered alert analysis** - Uses OpenAI, Gemini, or Ollama for intelligent analysis
- **Priority-based filtering** - Configurable alert priority thresholds
- **Age-based filtering** - Ignore old alerts to reduce noise
- **Deduplication** - Prevents spam from repeated alerts
- **Slack integration** - Sends analyzed alerts to Slack channels

### 🖥️ Web UI Features
- **📊 Interactive Dashboard** - Real-time alert visualization and statistics
- **💬 AI Chat Interface** - Ask questions about your security data
- **🔍 Alert Analysis** - Detailed view of security incidents with AI insights
- **📈 Trend Analysis** - Identify patterns and security trends
- **📤 Export Functionality** - Download analysis reports
- **🎯 Filtering & Search** - Filter alerts by priority, time, and rules
- **⚙️ Configuration Management** - Web-based configuration for all system settings

### 🔧 Configuration Management
- **🤖 AI Provider Configuration** - Setup OpenAI, Gemini, or Ollama providers
- **💬 AI Chat Settings** - Dedicated configuration for chat behavior and preferences
- **📱 Slack Integration** - Configure notifications and message formatting
- **🎛️ General Settings** - System-wide preferences and alert processing options
- **🔍 Smart Feature Detection** - Automatic detection and validation of available features with implementation verification

### 🚀 Deployment Options
- **Docker Compose** - Single-command deployment
- **Kubernetes** - Scalable container orchestration
- **Cloud Deployment** - AWS, GCP, Azure ready
- **Docker Hub** - Pre-built images available

## 🏗️ Architecture

```
┌─────────────┐    ┌───────────────────┐    ┌─────────────┐
│    Falco    │───▶│  Webhook Endpoint │───▶│   Database  │
└─────────────┘    │   (Port 8080)     │    │  (SQLite)   │
                   └───────────────────┘    └─────────────┘
                           │                        │
                           ▼                        │
                   ┌───────────────────┐           │
                   │   AI Analysis     │           │
                   │ (OpenAI/Gemini/   │           │
                   │     Ollama)       │           │
                   └───────────────────┘           │
                           │                        │
                           ▼                        ▼
                   ┌───────────────────┐    ┌─────────────┐
                   │  Slack Notification│    │   Web UI    │
                   └───────────────────┘    │ (Dashboard) │
                                           └─────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for containerized deployment)
- API keys for your chosen AI provider

### 1. Clone and Setup
```bash
git clone <repository-url>
cd falco-rag-ai-gateway
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file:
```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_NAME=#security-alerts

# AI Provider (choose one)
PROVIDER_NAME=openai  # or gemini, ollama
MODEL_NAME=gpt-4      # or gemini-pro, llama3
PORTKEY_API_KEY=your-portkey-key
OPENAI_VIRTUAL_KEY=your-openai-key
# GEMINI_VIRTUAL_KEY=your-gemini-key

# Alert Filtering
MIN_PRIORITY=warning  # debug, informational, notice, warning, error, critical
IGNORE_OLDER=1        # Minutes

# Web UI
WEB_UI_ENABLED=true
```

### 3. Run the Application

#### Option A: Using Docker (Recommended)
```bash
# Pull and run the published image
docker run -d \
  --name falco-ai-alerts \
  -p 8080:8080 \
  -v $(pwd)/.env:/app/.env \
  maddigsys/falco-ai-alerts:latest
```

#### Option B: Development mode
```bash
# Local development
python app.py

# The application will start with:
# - Webhook endpoint: http://localhost:8080/falco-webhook
# - Web UI Dashboard: http://localhost:8080/dashboard
# - Health check: http://localhost:8080/health
```

### 4. Access the Web UI
Open your browser to `http://localhost:8080/dashboard` to access:
- **Real-time alert dashboard**
- **AI-powered chat interface**
- **Security analytics and trends**
- **Alert filtering and search**

## 🐳 Docker Deployment

### Simple Deployment
```bash
# Start the service
docker-compose up -d

# Check logs
docker-compose logs -f falco-ai-alerts

# Access Web UI
open http://localhost:8080/dashboard

# Test webhook
curl -X POST http://localhost:8080/falco-webhook \
  -H "Content-Type: application/json" \
  -d '{"rule": "Test Alert", "priority": "warning", "output": "Test alert"}'
```

### With Ollama (Local AI)
```bash
# Start with Ollama
docker-compose --profile ollama up -d

# Download models
docker-compose exec ollama ollama pull llama3

# Update environment
echo "PROVIDER_NAME=ollama" >> .env
echo "OLLAMA_MODEL_NAME=llama3" >> .env
```

## ☸️ Kubernetes Deployment

Complete production-ready Kubernetes deployment with auto-scaling, monitoring, and security hardening.

### 🔧 **Resource Requirements**

⚠️ **Important**: Ensure your cluster has sufficient resources before deployment!

#### **Development Environment** (Single-node testing)
- **Memory**: 8GB available RAM (6GB for Ollama 7B model + 2GB for app)
- **CPU**: 2 cores minimum  
- **Storage**: 15GB available storage
- **Model**: `llama3.1:7b` (smaller, faster for testing)

#### **Production Environment** (Multi-node cluster)
- **Memory**: 18GB available RAM (16GB for Ollama 13B model + 2GB for app)
- **CPU**: 4 cores minimum
- **Storage**: 30GB available storage
- **Model**: `jimscard/whiterabbit-neo:latest` (13B, optimized for security)
- **Note**: ⚠️ 13B model has slower inference (15-30s), consider 7B for high-volume

#### **Enterprise Environment** (High-performance)
- **Memory**: 24GB+ available RAM (for 30B+ models)
- **CPU**: 8+ cores
- **Storage**: 50GB+ available storage
- **Model**: `llama3.1:70b` or similar large models

📖 **See [k8s/OLLAMA_MODELS.md](k8s/OLLAMA_MODELS.md) for complete model selection and resource planning guide.**

### 🚀 Easy Install
```bash
# Install development environment
./k8s/install.sh dev

# Install production environment  
./k8s/install.sh prod

# Validate configuration only
./k8s/install.sh dev --validate-only

# Get help with all options
./k8s/install.sh --help
```

### Manual Deploy (Alternative)
```bash
# Deploy to development environment
kubectl apply -k k8s/overlays/development/

# Deploy to production environment  
kubectl apply -k k8s/overlays/production/

# Access via port-forward (development)
kubectl port-forward svc/dev-falco-ai-alerts 8080:8080 -n falco-ai-alerts-dev

# Access Web UI
open http://localhost:8080/dashboard
```

### 🗑️ Easy Cleanup
```bash
# Clean up development environment (with backup)
./k8s/cleanup.sh dev

# Clean up production environment and delete all data
./k8s/cleanup.sh prod --delete-data

# Clean up everything without prompts
./k8s/cleanup.sh all --force

# Get help with all options
./k8s/cleanup.sh --help
```

### Kubernetes Features
- 🚀 **Easy installation** (Automated install script with validation)
- 📊 **Progress monitoring** (Real-time AI model download progress with ETA)
- 🔄 **Auto-scaling** (HPA with CPU/memory metrics)
- 🔒 **Security-hardened** (RBAC, Network Policies, Security Contexts)
- 📈 **Monitoring ready** (Prometheus integration, health checks)
- 🏗️ **Multi-environment** (Development and Production overlays)
- 💾 **Persistent storage** (Database and configuration persistence)
- 🌐 **Ingress support** (TLS termination, custom domains)
- 🗑️ **Easy cleanup** (Automated uninstall script with backups)

**📖 Complete Documentation**: See [k8s/README.md](k8s/README.md) for detailed deployment instructions, configuration options, troubleshooting, and advanced deployment scenarios.

## 📊 Web UI Usage

### Dashboard Features
- **Alert Statistics** - Total, critical, and recent alert counts
- **Priority Breakdown** - Visual distribution of alert priorities
- **Rule Frequency** - Most common security rules triggered
- **Timeline View** - Alert activity over time

### AI Chat Interface
Ask questions about your security data:
- *"What are my most critical alerts?"*
- *"Show me trends in container security"*
- *"What should I investigate next?"*
- *"How can I improve my security posture?"*

### Configuration Interface
Access configuration pages at:
- **General Settings**: `http://localhost:8080/config/general`
- **AI Configuration**: `http://localhost:8080/config/ai` 
- **AI Chat Settings**: `http://localhost:8080/config/ai-chat`
- **Slack Integration**: `http://localhost:8080/config/slack`
- **Feature Status**: `http://localhost:8080/config/features` - Smart feature detection with implementation verification

Features include:
- **Real-time validation** - Test configurations before saving
- **Provider-specific settings** - Separate model configurations per AI provider
- **Chat behavior customization** - Response length, tone, and context settings
- **Session management** - Configure timeouts and history limits

### Alert Analysis
- **Detailed Views** - Full alert context and metadata
- **AI Insights** - Security impact analysis and recommendations
- **Command Suggestions** - Investigation and remediation commands
- **Export Options** - JSON reports for external analysis

## 🔧 API Endpoints

### Core Endpoints
- `POST /falco-webhook` - Receive Falco alerts
- `GET /health` - Health check
- `GET /` - Web UI home (redirects to dashboard)

### Web UI API
- `GET /dashboard` - Main dashboard UI
- `GET /api/alerts` - Get alerts with filtering
- `GET /api/stats` - Alert statistics
- `GET /api/rules` - Unique alert rules
- `POST /api/chat` - AI chat interface
- `GET /api/chat/history` - Chat conversation history
- `GET /api/export` - Export analysis data

### API Examples
```bash
# Get alert statistics
curl http://localhost:8080/api/stats

# Filter alerts by priority
curl "http://localhost:8080/api/alerts?priority=critical&time_range=24h"

# Chat with AI
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are my critical alerts?"}'

# Export analysis
curl http://localhost:8080/api/export > security_report.json
```

## ⚙️ Configuration

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `WEB_UI_ENABLED` | Enable/disable web UI | `true` |
| `SLACK_BOT_TOKEN` | Slack bot token | Required |
| `PROVIDER_NAME` | AI provider (openai/gemini/ollama) | `openai` |
| `MIN_PRIORITY` | Minimum alert priority | `warning` |
| `IGNORE_OLDER` | Ignore alerts older than X minutes | `1` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Falco Integration
Configure Falco to send alerts to the webhook:

```yaml
# falco.yaml
json_output: true
json_include_output_property: true
http_output:
  enabled: true
  url: "http://your-server:8080/falco-webhook"
```

## 🔒 Security Considerations

- **Authentication** - Add authentication for production deployments
- **HTTPS** - Use TLS in production environments
- **Network Security** - Restrict webhook access to Falco instances
- **Data Retention** - Configure alert database cleanup policies
- **API Rate Limiting** - Implement rate limiting for public APIs

## 🛠️ Development

### Project Structure
```
falco-rag-ai-gateway/
├── app.py                 # Main application with integrated web UI
├── mcp_alternative.py     # MCP (Model Context Protocol) implementation
├── multilingual_service.py # Multilingual support
├── weaviate_service.py    # Vector database integration
├── slack.py              # Slack integration
├── portkey_config.py     # Portkey AI configuration
├── templates/
│   ├── dashboard.html     # Web UI dashboard template
│   ├── mcp_dashboard.html # MCP management interface
│   └── system_prompt.txt  # AI system prompt
├── static/
│   └── logo.png          # Application logo
├── docker-compose.yaml    # Docker deployment
├── Dockerfile            # Container image
├── requirements.txt      # Python dependencies
├── k8s/                  # Kubernetes deployment files
└── README.md            # This file
```

### Running Tests
```bash
# Test webhook endpoint
python -c "
import requests
import json
payload = {
    'rule': 'Test Alert',
    'priority': 'warning',
    'output': 'Test alert for development',
    'output_fields': {'container.name': 'test'}
}
response = requests.post('http://localhost:8080/falco-webhook', 
                        json=payload, 
                        headers={'Content-Type': 'application/json'})
print(f'Status: {response.status_code}')
print(f'Response: {response.json()}')
"
```

## 📈 Monitoring & Observability

### Health Checks
```bash
# Application health
curl http://localhost:8080/health

# Database health (check if alerts are being stored)
curl http://localhost:8080/api/stats
```

### Logs
```bash
# View application logs
docker-compose logs -f falco-ai-alerts

# Filter for specific log levels
docker-compose logs falco-ai-alerts | grep ERROR
```

## 🚀 MCP (Model Context Protocol) Integration

The Falco AI Gateway includes comprehensive MCP (Model Context Protocol) integration, enabling enhanced AI capabilities through external data sources and tools.

### 🎯 MCP Features

#### **MCP Server Implementation**
- **15 Security Tools**: Complete set of security analysis and management tools
- **Real-time Integration**: Direct access to security data and AI models
- **Alternative Implementation**: Lightweight, dependency-free MCP server

#### **Available MCP Tools**

##### **Security Alerts (8 tools)**
- `get_security_alerts` - Retrieve alerts with filtering options
- `analyze_security_alert` - AI analysis for specific alerts
- `chat_with_security_ai` - Chat with security AI assistant
- `get_security_dashboard` - Generate security dashboard data
- `search_security_events` - Semantic search across security events
- `get_alert_statistics` - Get comprehensive alert statistics
- `reprocess_alert` - Reprocess alerts with fresh AI analysis
- `bulk_generate_ai_analysis` - Generate AI analysis for missing alerts

##### **Threat Intelligence (1 tool)**
- `get_threat_intelligence` - AI-powered threat intelligence analysis

##### **Configuration (3 tools)**
- `get_ai_config` - Get current AI configuration
- `get_slack_config` - Get Slack integration configuration
- `get_system_health` - Get system health status

##### **Advanced Analytics (2 tools)**
- `cluster_alerts` - Cluster similar alerts using AI
- `predict_threats` - Predict potential threats based on patterns

##### **System Analysis (1 tool)**
- `analyze_system_state` - Analyze system state for security vulnerabilities

### 🎨 MCP Dashboard

Access the MCP Dashboard at `/mcp-dashboard` to:

1. **Monitor Status**: View real-time status of all MCP components
2. **Manage Tools**: View and test all available MCP tools
3. **Configure Settings**: Update MCP configuration dynamically
4. **View Logs**: Monitor MCP activity and troubleshoot issues

### 🔌 MCP API Endpoints

#### **Status & Health**
- `GET /api/mcp/status` - Get MCP integration status
- `GET /api/mcp/system-health` - Comprehensive system health

#### **Configuration**
- `GET /api/mcp/config` - Get MCP configuration
- `POST /api/mcp/config` - Update MCP configuration
- `GET /api/mcp/export-config` - Export configuration

#### **Enhanced Features**
- `POST /api/mcp/enhanced-chat` - Enhanced AI chat with MCP context
- `GET /api/mcp/enrich-alert/{id}` - Enrich alert with MCP data
- `GET /api/mcp/threat-intelligence` - Get threat intelligence

### 🚀 Getting Started with MCP

#### **1. Access MCP Dashboard**
```bash
# Navigate to the MCP Dashboard
http://localhost:8080/mcp-dashboard
```

#### **2. Check MCP Status**
```bash
# Check if MCP is available
curl http://localhost:8080/api/mcp/status
```

#### **3. Use Enhanced Chat**
```bash
# Enhanced chat with MCP context
curl -X POST http://localhost:8080/api/mcp/enhanced-chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze recent security threats",
    "context": {"alert_id": 123}
  }'
```

#### **4. Enrich Alerts**
```bash
# Enrich an alert with external data
curl http://localhost:8080/api/mcp/enrich-alert/123
```

### 🔧 MCP Configuration

#### **AI Provider Configuration**
```json
{
  "ai_provider": "ollama",
  "ai_model": "tinyllama",
  "ai_api_url": "http://ollama:11434",
  "mcp_enabled": "true"
}
```

### 📊 MCP Metrics

The MCP Dashboard provides real-time metrics:

- **Total Tools**: Number of available MCP tools (15)
- **Server Status**: MCP server availability
- **Active Integrations**: Number of active integrations
- **Context Enrichments**: Number of context enrichments performed

## 🐳 Docker Hub Publishing

### Building and Publishing

#### **1. Build the Image**
```bash
# Build the Docker image
docker build -t maddigsys/falco-ai-alerts:latest .

# Tag for versioning
docker tag maddigsys/falco-ai-alerts:latest maddigsys/falco-ai-alerts:v1.0.0
```

#### **2. Push to Docker Hub**
```bash
# Login to Docker Hub
docker login

# Push the image
docker push maddigsys/falco-ai-alerts:latest
docker push maddigsys/falco-ai-alerts:v1.0.0
```

#### **3. Automated Build**
```bash
# Use the provided build script
./scripts/build-and-push.sh v1.0.0
```

### Available Tags
- `latest` - Latest stable release
- `v1.0.0` - Specific version
- `dev` - Development build

### Pull and Run
```bash
# Pull the latest image
docker pull maddigsys/falco-ai-alerts:latest

# Run with environment file
docker run -d \
  --name falco-ai-alerts \
  -p 8080:8080 \
  -v $(pwd)/.env:/app/.env \
  maddigsys/falco-ai-alerts:latest
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test the integration
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues** - Report bugs and feature requests
- **Documentation** - Check the `/templates/system_prompt.txt` for AI behavior customization
- **Community** - Join our discussions for help and best practices

---

🎉 **Your Falco AI Alert System with Web UI is now fully integrated and ready for deployment!**

Access your dashboard at `http://localhost:8080/dashboard` and start monitoring your security alerts with AI-powered insights.