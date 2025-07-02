# 🐳 Docker Setup Guide for Local Testing

## 🚀 Quick Start

### 1. **Start the System**
```bash
./test-local.sh
```

This will:
- ✅ Check Docker is running
- ✅ Copy `env.example` to `.env` if needed
- ✅ Start all services with Docker Compose
- ✅ Wait for health checks
- ✅ Show you all the URLs to access

### 2. **Send Test Alerts**
```bash
./send-test-alert.sh
```

This sends 4 sample security alerts to test the system.

### 3. **Access the Web UI**
- 📊 **Dashboard**: http://localhost:8080/dashboard
- 🤖 **AI Config**: http://localhost:8080/config/ai
- 📢 **Slack Config**: http://localhost:8080/config/slack

---

## 📋 Manual Setup (Alternative)

### **1. Environment Configuration**
```bash
# Copy template and customize
cp env.example .env

# Edit .env file for your needs (optional for local testing)
vim .env
```

### **2. Start Services**
```bash
# Start main services
docker-compose up -d

# Start with development tools (database admin)
docker-compose --profile dev up -d

# Start with monitoring
docker-compose --profile monitoring up -d

# Start everything
docker-compose --profile dev,monitoring up -d
```

### **3. Verify Services**
```bash
# Check service health
curl http://localhost:8080/health

# Check Ollama
curl http://localhost:11434/api/tags

# View logs
docker-compose logs -f falco-ai-alerts
docker-compose logs -f ollama
```

---

## 🛠️ Service Details

| Service | Port | Purpose | Profile |
|---------|------|---------|---------|
| **falco-ai-alerts** | 8080 | Main application + Web UI | default |
| **ollama** | 11434 | Local LLM service | default |
| **adminer** | 8081 | Database management | dev |
| **prometheus** | 9090 | Monitoring | monitoring |

---

## 🔧 Configuration Options

### **AI Providers**
- **Ollama** (default): Local LLM - no API keys needed
- **OpenAI**: Requires Portkey API key + OpenAI Virtual key
- **Gemini**: Requires Portkey API key + Gemini Virtual key

### **Environment Variables**
```bash
# AI Provider (ollama, openai, gemini)
PROVIDER_NAME=ollama

# Ollama Model (downloaded automatically on first use)
OLLAMA_MODEL_NAME=jimscard/whiterabbit-neo:latest

# Cloud AI (when using OpenAI/Gemini)
PORTKEY_API_KEY=your-portkey-key
OPENAI_VIRTUAL_KEY=your-openai-virtual-key
GEMINI_VIRTUAL_KEY=your-gemini-virtual-key

# Slack Integration (optional)
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_NAME=#security-alerts

# Alert Configuration
MIN_PRIORITY=warning
LOG_LEVEL=INFO
```

---

## 🧪 Testing Scenarios

### **1. Basic Functionality Test**
```bash
# Start system
./test-local.sh

# Send test alerts
./send-test-alert.sh

# Check dashboard
open http://localhost:8080/dashboard
```

### **2. AI Configuration Test**
```bash
# Access AI config
open http://localhost:8080/config/ai

# Test different providers
# 1. Test with Ollama (default)
# 2. Configure OpenAI/Gemini if you have keys
# 3. Use the "Test Connection" button
```

### **3. Slack Integration Test**
```bash
# Configure Slack
open http://localhost:8080/config/slack

# Add your bot token
# Test connection
# Send test alert to verify Slack notifications
```

### **4. Manual Webhook Test**
```bash
# Send custom alert
curl -X POST http://localhost:8080/falco-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "rule": "Custom Test Alert",
    "priority": "warning",
    "output": "This is a test alert",
    "time": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "output_fields": {
      "container.name": "test-container"
    }
  }'
```

---

## 🐛 Troubleshooting

### **Service Won't Start**
```bash
# Check Docker is running
docker info

# Check port conflicts
lsof -i :8080
lsof -i :11434

# View service logs
docker-compose logs falco-ai-alerts
docker-compose logs ollama
```

### **Ollama Model Issues**
```bash
# Check available models
curl http://localhost:11434/api/tags

# Pull model manually
docker-compose exec ollama ollama pull jimscard/whiterabbit-neo:latest

# Check model status
curl http://localhost:8080/api/ollama/status/jimscard%2Fwhiterabbit-neo:latest
```

### **Database Issues**
```bash
# Start with database admin
docker-compose --profile dev up -d

# Access database at http://localhost:8081
# Server: sqlite:///app/alerts.db
```

### **AI Analysis Not Working**
```bash
# Check AI configuration
curl http://localhost:8080/api/ai/config

# Test AI connection
curl -X POST http://localhost:8080/api/ai/test \
  -H "Content-Type: application/json" \
  -d '{}'

# Check logs for AI errors
docker-compose logs falco-ai-alerts | grep -i "ai\|llm\|ollama"
```

---

## 📊 Monitoring & Logs

### **Real-time Logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f falco-ai-alerts
docker-compose logs -f ollama

# Filter for errors
docker-compose logs falco-ai-alerts | grep ERROR
```

### **Prometheus Monitoring**
```bash
# Start with monitoring
docker-compose --profile monitoring up -d

# Access Prometheus at http://localhost:9090
```

### **Health Checks**
```bash
# Main service
curl http://localhost:8080/health

# API endpoints
curl http://localhost:8080/api/stats
curl http://localhost:8080/api/alerts
```

---

## 🧹 Cleanup

### **Stop Services**
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (removes data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

### **Reset Database**
```bash
# Remove database file
rm -f alerts.db

# Restart services (will recreate database)
docker-compose restart falco-ai-alerts
```

---

## 🔄 Development Workflow

### **Code Changes**
```bash
# Rebuild and restart after code changes
docker-compose build falco-ai-alerts
docker-compose restart falco-ai-alerts

# Or rebuild and recreate
docker-compose up -d --build falco-ai-alerts
```

### **Volume Mounts**
- Templates: `./templates` → `/app/templates` (read-only)
- Database: `./alerts.db` → `/app/alerts.db` (persistent)
- Data: `alerts_data` volume → `/app/data` (persistent)

---

## 📚 Next Steps

1. **🔧 Configure AI Provider**: Set up OpenAI/Gemini for cloud AI or use Ollama locally
2. **📢 Set up Slack**: Configure bot token for alert notifications
3. **🚀 Deploy to Production**: Use this setup as base for production deployment
4. **📊 Add Monitoring**: Enable Prometheus profile for production monitoring
5. **🛡️ Security**: Review and harden configuration for production use

---

## 💡 Tips

- **Use Ollama for privacy**: No external API calls, runs locally
- **Use Portkey for security**: Adds security layer to cloud AI providers
- **Enable profiles**: Use `--profile dev,monitoring` for full development environment
- **Persistent data**: Database and Ollama models persist across restarts
- **Health checks**: All services have health checks for reliability 