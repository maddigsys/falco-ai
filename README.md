# Falco AI Alert System with Integrated Web UI

> ⚠️ **WORK IN PROGRESS DISCLAIMER** ⚠️  
> **This project is actively under development.** While the core functionality is operational, some features and configurations may not work as expected. We are continuously improving the system and fixing issues as they arise. Please use with caution in production environments and report any issues you encounter.

🚀 **Complete Integration Ready!** A comprehensive security alert system that combines Falco runtime security with AI-powered analysis and an interactive web dashboard.

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

### 🚀 Deployment Options
- **Docker Compose** - Single-command deployment
- **Kubernetes** - Scalable container orchestration
- **Cloud Deployment** - AWS, GCP, Azure ready

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
- Python 3.9+
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
├── integrated_web_ui.py   # Original web UI module (reference)
├── templates/
│   ├── dashboard.html     # Web UI dashboard template
│   ├── falco_dashboard.html
│   └── system_prompt.txt  # AI system prompt
├── docker-compose.yaml    # Docker deployment
├── Dockerfile            # Container image
├── requirements.txt      # Python dependencies
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