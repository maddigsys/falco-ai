# Falco AI Alert System

> **⚠️ EXPERIMENTAL REPOSITORY DISCLAIMER**  
> This repository is currently under active development and is considered experimental. Some features may not work as expected, and breaking changes may occur without notice. Use at your own risk in production environments. Please report issues and contribute feedback to help improve the system.

A comprehensive security alert system that combines Falco runtime security with AI-powered analysis and an interactive web dashboard.

## Features

- **Real-time Falco webhook processing** - Receives and processes security alerts
- **AI-powered alert analysis** - Uses OpenAI, Gemini, or Ollama for intelligent analysis
- **Interactive Web Dashboard** - Real-time alert visualization with dark/light mode
- **MCP Integration** - 15 security tools with Model Context Protocol support
- **Slack Integration** - Sends analyzed alerts to Slack channels
- **Kubernetes Ready** - Production-ready deployment with auto-scaling
- **Multilingual Support** - AI analysis in multiple languages
- **Enhanced UI/UX** - Modern interface with responsive design

## Quick Start

> **Note**: This is experimental software. Please test thoroughly before using in production environments.

### Docker Compose (Recommended)
```bash
# Clone the repository
git clone https://github.com/maddigsys/falco-ai.git
cd falco-ai

# Start the system
docker-compose up -d

# Access Web UI
open http://localhost:8080/dashboard
```

### Docker Run (Quick Start)
```bash
# Run the latest version
docker run -d -p 8080:8080 --name falco-ai-alerts maddigsys/falco-ai-alerts:v2.0.0

# Access Web UI
open http://localhost:8080/dashboard
```

### Environment Configuration
Create a `.env` file:
```bash
# AI Provider
PROVIDER_NAME=ollama  # or openai, gemini
PORTKEY_API_KEY=your-portkey-key

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

## Kubernetes Deployment

```bash
# Development environment
./k8s/install.sh dev

# Production environment
./k8s/install.sh prod
```

## API Endpoints

- `POST /falco-webhook` - Receive Falco alerts
- `GET /dashboard` - Web UI dashboard
- `GET /api/alerts` - Get alerts with filtering
- `POST /api/chat` - AI chat interface
- `GET /mcp-dashboard` - MCP management interface
- `GET /runtime-events` - Enhanced events page with pagination

## MCP Tools

The system includes 15 functional MCP (Model Context Protocol) tools:

- **Security Alerts**: `get_security_alerts`, `analyze_security_alert`, `chat_with_security_ai`
- **Threat Intelligence**: `get_threat_intelligence`, `predict_threats`
- **Analytics**: `cluster_alerts`, `get_alert_statistics`, `search_security_events`
- **Configuration**: `get_ai_config`, `get_slack_config`, `get_system_health`

## Recent Updates (v2.0.0)

- **UI/UX Improvements**: Enhanced dark/light mode compatibility
- **Runtime Events**: Fixed pagination and layout issues
- **Notifications**: Improved visibility and styling
- **Responsive Design**: Better mobile and desktop experience
- **Code Quality**: Removed debug styles and improved maintainability

## Known Limitations & Issues

This is an experimental project with the following known limitations:

- **MCP Integration**: Some MCP features may not work as expected
- **Weaviate Connection**: Vector database connectivity may be unstable
- **AI Provider Configuration**: Complex setup required for cloud AI providers
- **Performance**: Not optimized for high-volume production workloads
- **Documentation**: Some features may lack complete documentation
- **Testing**: Limited test coverage for all features

**Reporting Issues**: Please report bugs and feature requests through GitHub Issues.

## License

MIT License - see LICENSE file for details.