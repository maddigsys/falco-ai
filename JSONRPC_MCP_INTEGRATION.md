# JSON-RPC MCP Integration Guide

## Overview

This document provides comprehensive guidance for integrating Falco AI Alert System with AI clients using the **JSON-RPC over stdio protocol** through the Model Context Protocol (MCP). This integration enables AI assistants like Claude Desktop, VS Code, and Cursor to directly access Falco security tools and real-time threat data.

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# 1. Make setup script executable
chmod +x setup_jsonrpc_mcp.sh

# 2. Run auto-setup (detects and configures supported clients)
./setup_jsonrpc_mcp.sh

# 3. Start Falco service
python3 app.py

# 4. Restart your AI client
# Your AI can now access Falco security tools!
```

### Option 2: Web Configuration

1. Start your Falco service: `python3 app.py`
2. Open: http://localhost:8080/jsonrpc-mcp-config
3. Follow the web-based setup instructions
4. Download configurations for your specific AI client

## 📋 Available Security Tools

The JSON-RPC MCP server exposes these Falco security tools to AI clients:

### 1. `get_security_alerts`
**Purpose**: Retrieve recent security alerts from Falco
```json
{
  "name": "get_security_alerts",
  "arguments": {
    "status": "all|active|resolved",
    "limit": 10,
    "priority": "high|medium|low"
  }
}
```

### 2. `analyze_security_alert`
**Purpose**: Deep analysis of specific security alerts
```json
{
  "name": "analyze_security_alert",
  "arguments": {
    "alert_id": "12345",
    "include_context": true,
    "threat_intelligence": true
  }
}
```

### 3. `get_alert_statistics` 
**Purpose**: Security metrics and trend analysis
```json
{
  "name": "get_alert_statistics",
  "arguments": {
    "timeframe": "1h|24h|7d|30d",
    "group_by": "priority|source|type"
  }
}
```

### 4. `analyze_system_state`
**Purpose**: Overall security posture assessment
```json
{
  "name": "analyze_system_state",
  "arguments": {
    "components": ["falco", "kubernetes", "containers"],
    "include_metrics": true
  }
}
```

## 🔧 Client-Specific Setup

### Claude Desktop

**Configuration File**: `~/.config/claude-desktop/config.json`

```json
{
  "mcpServers": {
    "falco-ai-alerts": {
      "command": "python3",
      "args": ["/path/to/falco-rag-ai-gateway/jsonrpc_mcp_server.py"],
      "env": {
        "FALCO_API_BASE": "http://localhost:8080",
        "LOG_LEVEL": "INFO"
      },
      "description": "Falco AI Alert System - Security monitoring and threat analysis tools"
    }
  }
}
```

**Setup Steps**:
1. Create configuration directory: `mkdir -p ~/.config/claude-desktop/`
2. Save the configuration above to the config.json file
3. Update the path to match your installation directory
4. Restart Claude Desktop

### VS Code (with MCP Extension)

**Configuration File**: `~/.config/Code/User/mcp-servers.json`

```json
{
  "mcpServers": {
    "falco-ai-alerts": {
      "command": "python3",
      "args": ["/path/to/falco-rag-ai-gateway/jsonrpc_mcp_server.py"],
      "env": {
        "FALCO_API_BASE": "http://localhost:8080",
        "LOG_LEVEL": "INFO"
      },
      "description": "Falco AI Alert System - Security monitoring tools",
      "capabilities": {
        "tools": true,
        "resources": false,
        "prompts": false
      },
      "metadata": {
        "category": "security",
        "tags": ["falco", "security", "alerts", "monitoring"]
      }
    }
  }
}
```

### Cursor (with MCP Support)

**Configuration File**: `~/.config/cursor/User/mcp-servers.json`

```json
{
  "mcpServers": {
    "falco-ai-alerts": {
      "command": "python3",
      "args": ["/path/to/falco-rag-ai-gateway/jsonrpc_mcp_server.py"],
      "env": {
        "FALCO_API_BASE": "http://localhost:8080",
        "LOG_LEVEL": "INFO"
      },
      "description": "Falco AI Alert System - Security monitoring tools",
      "icon": "🛡️",
      "displayName": "Falco Security Alerts"
    }
  }
}
```

## 🧪 Testing the Integration

### Automated Testing

```bash
# Run comprehensive test suite
python3 test_jsonrpc_mcp.py

# Expected output:
# ✅ Server created with 4 tools
# ✅ Initialize: Falco AI MCP Server (Protocol: 2024-11-05)
# ✅ Found 4 tools
# ✅ Tool call successful
# 🎉 All tests passed!
```

### Manual Testing with AI Clients

Once configured, try these prompts with your AI client:

1. **"Show me recent security alerts from Falco"**
2. **"Analyze the security posture of my system"**
3. **"What are the latest high-priority security threats?"**
4. **"Get statistics on security alerts from the past 24 hours"**

### Command Line Testing

```bash
# Direct server test
python3 jsonrpc_mcp_server.py

# Send a JSON-RPC request
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python3 jsonrpc_mcp_server.py
```

## 🔍 Troubleshooting

### Common Issues

#### 1. "MCP server not responding"
```bash
# Check if server starts correctly
python3 jsonrpc_mcp_server.py
# Should show: "🚀 Falco AI MCP Server started (JSON-RPC over stdio)"

# Check Falco service
curl http://localhost:8080/health
```

#### 2. "Tools not available"
```bash
# Verify Falco API connection
export FALCO_API_BASE=http://localhost:8080
python3 -c "import requests; print(requests.get('$FALCO_API_BASE/health').status_code)"
```

#### 3. "Permission denied" errors
```bash
# Make scripts executable
chmod +x setup_jsonrpc_mcp.sh
chmod +x jsonrpc_mcp_server.py
```

#### 4. Client can't find server
- Verify the full path to `jsonrpc_mcp_server.py` in your client configuration
- Ensure `python3` is in your PATH
- Check client-specific logs for connection details

### Debugging Mode

Enable detailed logging:

```bash
export LOG_LEVEL=DEBUG
export FALCO_API_BASE=http://localhost:8080
python3 jsonrpc_mcp_server.py
```

### Client-Specific Debugging

**Claude Desktop**:
- Check logs in: `~/Library/Logs/Claude/`
- Enable developer tools in Claude settings

**VS Code**:
- Open Developer Tools: `Ctrl+Shift+I` / `Cmd+Option+I`
- Check MCP extension logs

**Cursor**:
- Check cursor logs for MCP connection status
- Verify configuration syntax in settings

## 📁 File Structure

```
falco-rag-ai-gateway/
├── jsonrpc_mcp_server.py          # Main JSON-RPC MCP server
├── setup_jsonrpc_mcp.sh           # Automated setup script  
├── test_jsonrpc_mcp.py            # Integration test suite
├── config_templates/              # Client configuration templates
│   ├── claude_desktop_config.json
│   ├── vscode_mcp_config.json
│   └── cursor_mcp_config.json
├── templates/
│   └── jsonrpc_mcp_config.html    # Web configuration interface
└── JSONRPC_MCP_INTEGRATION.md     # This documentation
```

## 🛡️ Security Considerations

### Environment Variables

- `FALCO_API_BASE`: Falco service endpoint (default: http://localhost:8080)
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `MCP_TIMEOUT`: Tool execution timeout in seconds (default: 30)

### Data Privacy

- All communication uses local stdio (no network exposure)
- Sensitive alert data is transmitted only between local processes
- No external APIs called without explicit configuration

### Access Control

- Server only responds to properly formatted JSON-RPC 2.0 requests
- Invalid requests are safely rejected with appropriate error messages
- Tool access is limited to read-only operations on Falco data

## 🔄 Protocol Details

### JSON-RPC 2.0 Implementation

The server implements the full JSON-RPC 2.0 specification over stdio:

```json
// Request format
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_security_alerts",
    "arguments": {"limit": 5}
  }
}

// Response format  
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"success\": true, \"result\": [...]}"
      }
    ]
  }
}
```

### MCP Protocol Compliance

- **Protocol Version**: 2024-11-05
- **Capabilities**: Tools only (no resources or prompts)
- **Transport**: stdio with line-delimited JSON
- **Initialization**: Standard MCP handshake sequence

## 📈 Performance & Scaling

### Performance Characteristics

- **Startup Time**: <1 second
- **Tool Response Time**: 50-200ms (depending on Falco API)
- **Memory Usage**: ~50MB baseline
- **Concurrent Requests**: Handled sequentially (safe for single-client use)

### Scaling Considerations

- Each AI client gets its own server instance
- No shared state between instances
- Falco API is the primary bottleneck for multiple clients
- Consider Falco API rate limiting for high-volume usage

## 🔮 Advanced Configuration

### Custom Tool Development

To add new security tools, modify `jsonrpc_mcp_server.py`:

```python
def custom_security_tool(self, arguments: dict) -> dict:
    """Custom security analysis tool"""
    try:
        # Your custom logic here
        return {
            "success": True,
            "result": {"custom": "data"}
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Register in __init__
self.tools.append({
    "name": "custom_security_tool",
    "description": "Custom security analysis",
    "inputSchema": {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "Parameter 1"}
        }
    }
})
```

### Environment-Specific Configuration

**Development**:
```bash
export FALCO_API_BASE=http://localhost:8080
export LOG_LEVEL=DEBUG
```

**Production**:
```bash
export FALCO_API_BASE=https://your-falco-service.com
export LOG_LEVEL=WARNING
export MCP_TIMEOUT=10
```

**Kubernetes**:
```bash
export FALCO_API_BASE=http://falco-service.falco-system.svc.cluster.local:8080
export LOG_LEVEL=INFO
```

## 🤝 Support & Contributing

### Getting Help

1. **Web Interface**: Visit `/jsonrpc-mcp-config` for status and diagnostics
2. **Test Suite**: Run `python3 test_jsonrpc_mcp.py` for health checks
3. **Logs**: Enable DEBUG logging for detailed troubleshooting
4. **GitHub Issues**: Report bugs or request features

### Contributing

1. Follow the existing code style and patterns
2. Add tests for new tools or features
3. Update documentation for any changes
4. Test with multiple AI clients before submitting

## 📜 License

This integration is part of the Falco AI Alert System and follows the same licensing terms as the main project.

---

**Happy Securing! 🛡️**

For more information about the Falco AI Alert System, see the main [README.md](README.md). 