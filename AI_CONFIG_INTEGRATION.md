# AI Configuration Integration Documentation

## Overview

The Falco AI Alert System now includes a comprehensive AI configuration management system that allows users to configure OpenAI, Google Gemini, or Ollama providers through a professional web interface. This integration features Portkey as a central security layer for cloud AI providers, replaces environment variable configuration with a database-driven approach, and includes real-time testing, model selection, parameter tuning, and Ollama model download management.

## Features

### 🛡️ Portkey Security Layer
- **Centralized Security**: Single configuration for all cloud AI providers
- **AI Sanitization**: Automatic content filtering and monitoring
- **Enterprise Security**: Professional-grade API management
- **Unified Protection**: One security layer for OpenAI and Gemini

### 🤖 AI Provider Support
- **OpenAI via Portkey**: GPT models with enterprise-grade security
- **Google Gemini via Portkey**: Google's advanced AI models  
- **Ollama**: Local AI deployment for privacy and control

### ⚙️ Configuration Management
- Web-based configuration interface with security layer separation
- Real-time connection testing
- Model parameter tuning (temperature, max tokens)
- Configuration validation and error handling
- Persistent database storage

### 🎯 Advanced Features
- Model suggestions with clickable chips
- Sample AI response generation
- Provider-specific configuration sections
- Real-time status monitoring
- Professional tabbed interface
- Ollama model download with progress tracking
- Local model availability checking

## Database Schema

### AI Configuration Table
```sql
CREATE TABLE ai_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_name TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type TEXT DEFAULT 'string',
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Default Configuration
| Setting Name | Default Value | Type | Description |
|-------------|---------------|------|-------------|
| provider_name | openai | select | AI Provider (openai, gemini, ollama) |
| model_name | gpt-3.5-turbo | string | Model Name |
| portkey_api_key | '' | password | Portkey API Key (Security Layer for Cloud AI) |
| openai_virtual_key | '' | password | OpenAI Virtual Key (Portkey) |
| gemini_virtual_key | '' | password | Gemini Virtual Key (Portkey) |
| ollama_api_url | http://localhost:11434/api/generate | string | Ollama API URL |
| ollama_model_name | jimscard/whiterabbit-neo:latest | string | Ollama Model Name |
| max_tokens | 500 | number | Maximum Response Tokens |
| temperature | 0.7 | number | Response Temperature (0.0-1.0) |
| enabled | true | boolean | Enable AI Analysis |

## API Endpoints

### Configuration Management

#### GET `/api/ai/config`
Retrieve current AI configuration
```json
{
  "provider_name": {"value": "openai", "type": "select", "description": "AI Provider"},
  "model_name": {"value": "gpt-3.5-turbo", "type": "string", "description": "Model Name"},
  "enabled": {"value": "true", "type": "boolean", "description": "Enable AI Analysis"}
}
```

#### POST `/api/ai/config`
Update AI configuration
```json
{
  "provider_name": "openai",
  "model_name": "gpt-4",
  "portkey_api_key": "pk_...",
  "openai_virtual_key": "openai_...",
  "max_tokens": "750",
  "temperature": "0.8",
  "enabled": "true"
}
```

#### POST `/api/ai/test`
Test AI provider connection
```json
{
  "provider_name": "openai",
  "portkey_api_key": "pk_...",
  "openai_virtual_key": "openai_...",
  "model_name": "gpt-3.5-turbo"
}
```

Response:
```json
{
  "success": true,
  "message": "OpenAI connection successful!",
  "response_preview": "Connection successful! I'm ready to analyze...",
  "model_used": "gpt-3.5-turbo"
}
```

### Model Information

#### GET `/api/ai/models`
Get available models for each provider
```json
{
  "openai": ["gpt-4o", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
  "gemini": ["gemini-pro", "gemini-pro-vision", "gemini-1.5-pro"],
  "ollama": ["jimscard/whiterabbit-neo:latest", "llama3", "llama2", "mistral", "codellama"]
}
```

#### POST `/api/ai/generate-sample`
Generate sample AI response for testing
```json
{
  "provider_name": "openai"
}
```

Response:
```json
{
  "success": true,
  "sample_response": {
    "Security Impact": "This alert indicates...",
    "Next Steps": "Investigate the container...",
    "Remediation Steps": "Review container security..."
  },
  "provider_used": "openai"
}
```

### Ollama Management

#### GET `/api/ollama/models`
Get locally available Ollama models
```json
{
  "success": true,
  "models": ["jimscard/whiterabbit-neo:latest", "llama3", "mistral"],
  "count": 3
}
```

#### POST `/api/ollama/pull`
Download/pull an Ollama model
```json
{
  "model_name": "jimscard/whiterabbit-neo:latest"
}
```

Response:
```json
{
  "success": true,
  "message": "Download started for jimscard/whiterabbit-neo:latest",
  "model_name": "jimscard/whiterabbit-neo:latest"
}
```

#### GET `/api/ollama/status/<model_name>`
Check if a specific Ollama model is available
Response:
```json
{
  "model_name": "jimscard/whiterabbit-neo:latest",
  "available": true,
  "status": "downloaded"
}
```

## Web Interface

### Access
- **URL**: `http://localhost:8080/config/ai`
- **Navigation**: Available from dashboard header "🤖 AI Config"

### Interface Sections

#### 1. General Configuration
- Enable/disable AI analysis toggle
- Max Tokens configuration (50-2000)
- Temperature settings (0.0-1.0)
- Real-time status indicator

#### 2. Portkey Security Layer
- **Centralized Security Configuration**: Single API key for all cloud providers
- **Security Information**: Clear explanation of Portkey's role
- **Setup Guidance**: Direct link to Portkey registration
- **Enterprise Protection**: Unified security for OpenAI and Gemini

#### 3. AI Provider Selection
- Provider selection dropdown with security indicators
- Provider-specific configuration tabs
- Clear distinction between cloud (secured) and local providers

#### 4. Provider-Specific Settings

**OpenAI Configuration**:
- OpenAI Virtual Key (secure password field)  
- Model selection with suggestions
- Secured via Portkey layer

**Gemini Configuration**:
- Gemini Virtual Key (secure password field)
- Model selection with suggestions
- Secured via Portkey layer

**Ollama Configuration**:
- Ollama API URL configuration
- Local model selection with download status
- Model download functionality with progress tracking
- Available/Downloaded model indicators
- One-click model downloads

#### 5. Testing & Validation
- **Test Connection**: Validate provider credentials and security layer
- **Generate Sample**: Test AI response quality
- **Real-time Status**: Configuration completeness with security status

#### 6. Status Panel
- Current configuration status
- Security layer status (Portkey vs Local)
- Provider readiness indicator
- Model and parameter display

## Configuration Functions

### Core Functions

```python
def get_ai_config():
    """Get all AI configuration settings from database."""
    
def update_ai_config(setting_name, setting_value):
    """Update specific AI configuration setting."""
    
def test_ai_connection(provider_name, config_data):
    """Test AI provider connection with provided configuration."""
```

### Integration with Main System
The `generate_explanation_portkey()` function now automatically uses database configuration:

```python
def generate_explanation_portkey(alert_payload):
    """Generate explanation using configured AI provider from database."""
    # Get AI configuration from database
    ai_config = get_ai_config()
    
    # Check if AI is enabled
    if ai_config.get('enabled', {}).get('value') != 'true':
        return {"error": "AI analysis is disabled"}
    
    # Use configured provider, model, and parameters
    provider_name = ai_config.get('provider_name', {}).get('value', 'openai').lower()
    # ... dynamic configuration usage
```

## Provider Setup Guides

### Step 1: Portkey Security Layer (Required for Cloud Providers)

1. **Sign up at [Portkey.ai](https://portkey.ai)**
2. **Get your Portkey API Key**: `pk_...`
3. **Configure in Falco AI System**:
   - Navigate to "🛡️ Portkey Security Layer" section
   - Enter your Portkey API Key
   - This key will secure all cloud AI providers

### Step 2A: OpenAI via Portkey

1. **Add OpenAI to Portkey**:
   - Log into Portkey dashboard
   - Add your OpenAI API key
   - Generate virtual key for OpenAI
2. **Configure in Falco AI System**:
   - Select "OpenAI (Cloud via Portkey)" as provider
   - Enter OpenAI Virtual Key: `openai_...`
   - Choose model: `gpt-3.5-turbo` or `gpt-4`

### Step 2B: Google Gemini via Portkey

1. **Add Gemini to Portkey**:
   - Log into Portkey dashboard  
   - Add your Google AI API key
   - Generate virtual key for Gemini
2. **Configure in Falco AI System**:
   - Select "Google Gemini (Cloud via Portkey)" as provider
   - Enter Gemini Virtual Key: `gemini_...`
   - Choose model: `gemini-pro`

### Step 2C: Ollama (Local - No Portkey Required)

1. **Install Ollama**: `curl -fsSL https://ollama.ai/install.sh | sh`
2. **Start Ollama service**: `ollama serve`
3. **Configure in Falco AI System**:
   - Select "Ollama (Local Deployment)" as provider
   - API URL: `http://localhost:11434/api/generate`
   - Model Name: `jimscard/whiterabbit-neo:latest`
4. **Download model via UI**:
   - Click "📥 Download Model" button
   - Monitor progress bar
   - Model ready when showing ✅ status

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "AI analysis is disabled" | AI functionality turned off | Enable AI in configuration |
| "Configuration incomplete - missing API keys" | API keys not set | Configure provider credentials |
| "Portkey API key and OpenAI virtual key are required" | Missing Portkey setup | Complete Portkey configuration |
| "Ollama API URL not configured" | Ollama URL missing | Set correct Ollama API endpoint |
| "Connection refused" | Service not running | Start Ollama/check network |

## Security Considerations

### Data Protection
- API keys stored securely in database
- Password fields masked in interface
- No API keys in logs or error messages

### Access Control
- Web UI can be disabled via environment variable
- Database access controlled by file permissions
- Configuration changes logged

### Network Security
- Ollama: Local processing, no external calls
- Portkey: Enterprise-grade API security
- HTTPS recommended for production

## Performance Optimization

### Configuration Caching
- Settings loaded per request (no caching for security)
- Database queries optimized for single-key lookups
- Minimal overhead for disabled AI

### Provider Selection
- **OpenAI**: Best general performance, moderate cost
- **Gemini**: Competitive performance, Google integration
- **Ollama**: Local processing, privacy-focused, hardware dependent

## Monitoring and Troubleshooting

### Logs to Monitor
```
2025-07-01 14:11:22 - INFO - 🤖 Using AI provider: openai with model: gpt-3.5-turbo
2025-07-01 14:11:22 - INFO - 🤖 Calling OpenAI via Portkey...
2025-07-01 14:11:23 - INFO - ✅ Extracted via object access: This alert indicates...
```

### Health Checks
- Test connection before processing alerts
- Validate configuration on startup
- Monitor response times and success rates

### Troubleshooting Steps
1. **Check configuration completeness**
2. **Test provider connection**
3. **Verify API key validity**
4. **Check service availability**
5. **Review logs for specific errors**

## Production Deployment

### Environment Considerations
- Use environment variables for initial setup
- Migrate to database configuration via UI
- Backup configuration regularly

### Scaling Considerations  
- Database connection pooling for high volume
- Consider API rate limits for cloud providers
- Local Ollama for high-throughput scenarios

### Maintenance
- Regular API key rotation
- Model updates and testing
- Performance monitoring and optimization

## Integration Testing

The system has been tested with:

✅ **OpenAI Configuration**: Complete setup and testing workflow
✅ **Gemini Configuration**: Full provider configuration  
✅ **Ollama Configuration**: Local deployment testing
✅ **Database Operations**: CRUD operations for all settings
✅ **API Endpoints**: All configuration and testing endpoints
✅ **Web Interface**: Complete UI functionality
✅ **Error Handling**: Comprehensive error scenarios
✅ **Security**: API key protection and validation

This AI configuration system provides enterprise-ready AI management capabilities while maintaining the simplicity and reliability of the core Falco Alert System. 