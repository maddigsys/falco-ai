# Deployment Guide - Falco AI Alert System

## 🎉 Project Cleanup Complete!

The project has been cleaned and optimized for production deployment. Here's what was accomplished:

### ✅ **Files Removed**
- **Unused MCP modules**: `mcp_integration.py`, `mcp_client.py`, `mcp_config.py`, `mcp_ai_enhancement.py`
- **Test artifacts**: `test_report.json`
- **Obsolete documentation**: `AI_CHAT_FIX_SUMMARY.md`, `AI_CHAT_RESPONSE_IMPROVEMENTS.md`, `COLOR_SCHEME_REFERENCE.md`, `project_structure.md`, `MCP_IMPLEMENTATION_SUMMARY.md`
- **Development artifacts**: `__pycache__/`, `venv/`, `data/`, `alerts.db/`, `.DS_Store`, `k8s/backups/`

### ✅ **Files Preserved**
- **Core application**: `app.py`, `mcp_alternative.py`, `multilingual_service.py`, `weaviate_service.py`, `slack.py`, `portkey_config.py`
- **AI parsers**: `ollama_parser.py`, `gemini_parser.py`, `openai_parser.py` (all used in app.py)
- **Templates and static**: All UI templates and static assets
- **Configuration**: `docker-compose.yaml`, `Dockerfile`, `requirements.txt`, `.gitignore`, `env.example`
- **Kubernetes**: Complete k8s deployment files
- **Documentation**: Updated `README.md` and essential deployment guides
- **Test scripts**: `test-local.sh`, `send-test-alert.sh`, `check-ollama-status.sh` (referenced in docs)

### ✅ **Updated Documentation**
- **README.md**: Updated to reflect current state, removed references to deleted files
- **MCP section**: Updated to reflect the current 15-tool implementation
- **Docker Hub**: Added publishing instructions and build script
- **Project structure**: Updated to show actual files

## 🚀 **Ready for Deployment**

### **1. GitHub Commit**

```bash
# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Production-ready Falco AI Alert System

- Complete MCP integration with 15 security tools
- Cleaned codebase with only essential files
- Updated documentation and deployment guides
- Ready for Docker Hub publishing and Kubernetes deployment"

# Add remote repository
git remote add origin <your-github-repo-url>

# Push to GitHub
git push -u origin main
```

### **2. Docker Hub Publishing**

#### **Option A: Using the Build Script**
```bash
# Build and push latest version
./scripts/build-and-push.sh latest --push

# Build and push specific version
./scripts/build-and-push.sh v1.0.0 --push

# Build only (without pushing)
./scripts/build-and-push.sh v1.0.0 --no-push
```

#### **Option B: Manual Build**
```bash
# Login to Docker Hub
docker login

# Build the image
docker build -t maddigsys/falco-ai-alerts:latest .
docker build -t maddigsys/falco-ai-alerts:v1.0.0 .

# Push to Docker Hub
docker push maddigsys/falco-ai-alerts:latest
docker push maddigsys/falco-ai-alerts:v1.0.0
```

### **3. Kubernetes Deployment**

#### **Development Environment**
```bash
# Install development environment
./k8s/install.sh dev

# Access the application
kubectl port-forward svc/dev-falco-ai-alerts 8080:8080 -n falco-ai-alerts-dev
```

#### **Production Environment**
```bash
# Install production environment
./k8s/install.sh prod

# Access the application
kubectl port-forward svc/prod-falco-ai-alerts 8080:8080 -n falco-ai-alerts-prod
```

## 📁 **Final Project Structure**

```
falco-rag-ai-gateway/
├── app.py                    # Main application
├── mcp_alternative.py        # MCP implementation (15 tools)
├── multilingual_service.py   # Multilingual support
├── weaviate_service.py       # Vector database integration
├── slack.py                  # Slack integration
├── portkey_config.py         # Portkey AI configuration
├── ollama_parser.py          # Ollama response parser
├── gemini_parser.py          # Gemini response parser
├── openai_parser.py          # OpenAI response parser
├── generate_events.py        # Test event generator
├── templates/                # Web UI templates
│   ├── dashboard.html
│   ├── mcp_dashboard.html
│   ├── falco_dashboard.html
│   └── system_prompt.txt
├── static/                   # Static assets
│   └── logo.png
├── k8s/                      # Kubernetes deployment
│   ├── base/
│   ├── overlays/
│   ├── install.sh
│   └── cleanup.sh
├── test scripts/             # Test utilities
│   ├── test-local.sh
│   ├── send-test-alert.sh
│   └── check-ollama-status.sh
├── scripts/                  # Build scripts
│   └── build-and-push.sh
├── docker-compose.yaml       # Docker deployment
├── Dockerfile               # Container image
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
├── env.example             # Environment template
├── README.md               # Main documentation
├── CHANGELOG.md            # Change history
├── DEPLOYMENT_CHECKLIST.md # Deployment guide
├── DOCKER_SETUP.md         # Docker setup guide
├── MULTILINGUAL_DEPLOYMENT_GUIDE.md # i18n guide
├── SLACK_CONFIG_INTEGRATION.md # Slack setup
├── AI_CONFIG_INTEGRATION.md # AI setup guide
├── LOGO_INSTRUCTIONS.md    # Logo guidelines
└── k8s/                    # Kubernetes files
    ├── OLLAMA_MODELS.md    # Model selection guide
    ├── OLLAMA_TIMEOUT_GUIDE.md # Timeout configuration
    ├── CLOUD_DEPLOYMENT_GUIDE.md # Cloud deployment
    └── README.md           # K8s documentation
```

## 🔧 **Configuration Files**

### **Environment Variables** (`.env`)
```bash
# Core Configuration
FALCO_AI_PORT=8080
WEB_UI_ENABLED=true
LOG_LEVEL=INFO

# AI Provider Configuration
PROVIDER_NAME=ollama  # or openai, gemini
MODEL_NAME=tinyllama  # or gpt-4, gemini-pro
PORTKEY_API_KEY=your-portkey-key
OPENAI_VIRTUAL_KEY=your-openai-key
GEMINI_VIRTUAL_KEY=your-gemini-key

# Ollama Configuration
OLLAMA_API_URL=http://ollama:11434/api/generate
OLLAMA_MODEL_NAME=tinyllama

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_NAME=#security-alerts

# Alert Configuration
MIN_PRIORITY=warning
IGNORE_OLDER=1

# Weaviate Configuration
WEAVIATE_ENABLED=true
WEAVIATE_HOST=weaviate
WEAVIATE_PORT=8080
WEAVIATE_GRPC_PORT=50051
```

### **Falco Configuration** (`falco.yaml`)
```yaml
json_output: true
json_include_output_property: true
http_output:
  enabled: true
  url: "http://your-server:8080/falco-webhook"
```

## 🎯 **MCP Tools Available**

The system includes **15 functional MCP tools**:

### **Security Alerts (8 tools)**
- `get_security_alerts` - Retrieve alerts with filtering
- `analyze_security_alert` - AI analysis for specific alerts
- `chat_with_security_ai` - Chat with security AI assistant
- `get_security_dashboard` - Generate security dashboard data
- `search_security_events` - Semantic search across security events
- `get_alert_statistics` - Get comprehensive alert statistics
- `reprocess_alert` - Reprocess alerts with fresh AI analysis
- `bulk_generate_ai_analysis` - Generate AI analysis for missing alerts

### **Threat Intelligence (1 tool)**
- `get_threat_intelligence` - AI-powered threat intelligence analysis

### **Configuration (3 tools)**
- `get_ai_config` - Get current AI configuration
- `get_slack_config` - Get Slack integration configuration
- `get_system_health` - Get system health status

### **Advanced Analytics (2 tools)**
- `cluster_alerts` - Cluster similar alerts using AI
- `predict_threats` - Predict potential threats based on patterns

### **System Analysis (1 tool)**
- `analyze_system_state` - Analyze system state for security vulnerabilities

## 🚀 **Quick Start Commands**

### **Docker Compose**
```bash
# Start the system
docker-compose up -d

# Access Web UI
open http://localhost:8080/dashboard

# Check logs
docker-compose logs -f falco-ai-alerts
```

### **Kubernetes**
```bash
# Install development environment
./k8s/install.sh dev

# Access via port-forward
kubectl port-forward svc/dev-falco-ai-alerts 8080:8080 -n falco-ai-alerts-dev
```

### **Local Development**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## 🎉 **Success!**

Your Falco AI Alert System is now:
- ✅ **Clean and optimized** for production
- ✅ **Fully documented** with updated README
- ✅ **Ready for GitHub** commit
- ✅ **Ready for Docker Hub** publishing
- ✅ **Ready for Kubernetes** deployment
- ✅ **MCP-enabled** with 15 functional tools

**Next steps:**
1. Commit to GitHub
2. Build and push to Docker Hub
3. Deploy to Kubernetes
4. Start monitoring your security alerts with AI-powered insights!

---

**Access your dashboard at `http://localhost:8080/dashboard`** 🚀 