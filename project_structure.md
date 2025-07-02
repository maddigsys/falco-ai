# Falco AI Security Alert System - Project Structure

## Overview

This document outlines the complete project structure for the Falco AI Security Alert System, a Flask-based webhook service that enriches Falco security alerts with AI-powered explanations and sends them to Slack.

## Directory Structure

```
falco-ai-alerts/
├── .github/
│   └── workflows/
│       └── ci.yml                      # GitHub Actions CI/CD pipeline
├── templates/
│   ├── README.md                       # Templates directory documentation
│   └── falco_alert_template.json      # Slack message template (created by setup)
├── tests/                              # Test directory (to be created)
│   └── __init__.py
├── .env.example                        # Environment variables template
├── .gitignore                          # Git ignore patterns
├── app.py                              # Main Flask application
├── docker-compose.yml                 # Docker Compose configuration
├── Dockerfile                          # Docker image definition
├── gemini_parser.py                   # Gemini LLM response parser
├── LICENSE                             # MIT License
├── Makefile                            # Build and development commands
├── ollama_test.py                      # Ollama connectivity testing
├── openai_parser.py                   # OpenAI LLM response parser
├── portkey_config.py                  # Portkey client configuration
├── portkey_test.py                    # Portkey connectivity testing
├── pytest.ini                         # Pytest configuration
├── README.md                           # Main project documentation
├── requirements.txt                   # Python dependencies
├── setup.sh                           # Automated setup script
├── slack.py                           # Slack integration module
└── test_webhook.py                    # Webhook testing utility
```

## Core Components

### Application Core
- **app.py**: Main Flask application with webhook endpoint, alert processing, and routing
- **requirements.txt**: Python package dependencies
- **.env.example**: Template for environment variables configuration

### LLM Integration
- **portkey_config.py**: Portkey client initialization for OpenAI and Gemini
- **openai_parser.py**: Parser for OpenAI response formatting
- **gemini_parser.py**: Parser for Gemini response formatting
- **ollama_test.py**: Local Ollama connectivity and testing utilities

### Slack Integration
- **slack.py**: Slack WebClient integration, message formatting, and template processing
- **templates/falco_alert_template.json**: Configurable Slack message template

### Testing & Development
- **test_webhook.py**: Comprehensive webhook testing with sample alerts
- **portkey_test.py**: Portkey API connectivity testing
- **setup.sh**: Automated project setup and environment configuration
- **Makefile**: Development workflow automation

### Deployment
- **Dockerfile**: Multi-stage Docker build for production deployment
- **docker-compose.yml**: Complete service orchestration including optional Ollama
- **.github/workflows/ci.yml**: Automated CI/CD pipeline

### Configuration
- **pytest.ini**: Test framework configuration
- **.gitignore**: Git exclusion patterns for Python projects
- **LICENSE**: MIT License for open source distribution

## Key Features

### Alert Processing Pipeline
1. **Webhook Reception**: Receives Falco alerts via HTTP POST to `/falco-webhook`
2. **Priority Filtering**: Configurable minimum priority levels (debug → emergency)
3. **Age Validation**: Ignore alerts older than specified threshold
4. **Deduplication**: Intelligent duplicate alert detection and counting
5. **AI Analysis**: Generate security impact and remediation recommendations
6. **Slack Notification**: Formatted rich messages with actionable insights

### LLM Provider Support
- **OpenAI**: Via Portkey API gateway with custom virtual keys
- **Gemini**: Via Portkey API gateway with custom virtual keys  
- **Ollama**: Direct HTTP API integration for local/self-hosted models

### Security Features
- **Input Validation**: JSON payload validation and sanitization
- **Error Handling**: Graceful degradation when AI analysis fails
- **Logging**: Comprehensive logging with configurable levels
- **Health Checks**: Built-in health endpoint for monitoring

## Environment Configuration

### Required Variables
```bash
SLACK_BOT_TOKEN=xoxb-your-token-here
PROVIDER_NAME=openai|gemini|ollama
MODEL_NAME=gpt-4|gemini-pro|llama3
```

### Optional Variables
```bash
SLACK_CHANNEL_NAME=#security-alerts
MIN_PRIORITY=warning
IGNORE_OLDER=1
FALCO_AI_PORT=8080
LOG_LEVEL=INFO
```

### Provider-Specific Variables
```bash
# For OpenAI/Gemini via Portkey
PORTKEY_API_KEY=your-portkey-key
OPENAI_VIRTUAL_KEY=your-openai-vkey
GEMINI_VIRTUAL_KEY=your-gemini-vkey

# For Ollama
OLLAMA_MODEL_NAME=llama3
OLLAMA_API_URL=http://localhost:11434/api/generate
```

## Quick Start Commands

```bash
# Initial setup
chmod +x setup.sh && ./setup.sh

# Development workflow
make dev-setup          # Setup with development tools
make run                # Start the application
make test-webhook       # Send test alerts
make test-health        # Check service health

# Docker deployment
make docker-build       # Build container image
make docker-run         # Start with docker-compose

# Testing and validation
make test               # Run test suite
make lint               # Code quality checks
```

## Integration Points

### Falco Configuration
Add to your `falco.yaml`:
```yaml
http_output:
  enabled: true
  url: "http://your-server:8080/falco-webhook"
  user_agent: "falcosecurity/falco"
```

### Slack App Setup
1. Create Slack app with `chat:write` permissions
2. Install app to workspace
3. Copy bot token to `SLACK_BOT_TOKEN`
4. Invite bot to target channel

### Kubernetes Deployment
- Service mesh integration for webhook exposure
- ConfigMap/Secret management for sensitive configuration
- RBAC policies for security isolation
- Resource limits and monitoring

## Monitoring & Observability

### Health Endpoints
- `GET /health`: Service health status
- Built-in Docker health checks
- Prometheus metrics ready (extensible)

### Logging Structure
- Structured JSON logging available
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Alert processing pipeline visibility
- Error tracking and debugging support

## Security Considerations

### Production Deployment
- TLS/SSL termination at load balancer
- Network policies for webhook access restriction
- API key rotation and secrets management
- Rate limiting and authentication (extensible)

### Development Security
- Environment variable isolation
- No secrets in version control
- Input validation and sanitization
- Secure defaults for all configurations

## Extension Points

### Adding New LLM Providers
1. Create `{provider}_parser.py` with response parsing logic
2. Add provider configuration in `portkey_config.py`
3. Update provider selection in `app.py`
4. Add environment variables to `.env.example`

### Custom Alert Processing
- Modify filter logic in `falco_webhook()` function
- Extend deduplication logic in `generate_alert_key()`
- Add custom notification channels alongside Slack

### Template Customization
- Modify `templates/falco_alert_template.json` for different Slack layouts
- Add new template variables in `slack.py`
- Create provider-specific templates if needed

This architecture supports scalable, secure, and maintainable security alert processing with AI enhancement capabilities.