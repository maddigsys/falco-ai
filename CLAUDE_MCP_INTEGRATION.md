# Claude MCP Integration for Falco AI Alert System

This integration enables Claude to directly access your Falco security tools and data through the Model Context Protocol (MCP), providing enhanced AI-powered threat analysis and real-time security insights.

## 🚀 Features

- **Real-time Security Data Access**: Claude can fetch live security alerts and system status
- **Intelligent Threat Analysis**: Enhanced analysis with context from your Falco deployment  
- **Seamless Integration**: No manual copy-paste required - direct tool access
- **Secure Local Connection**: MCP server runs locally, data stays on your infrastructure
- **Web-based Configuration**: Easy setup through the Falco web interface

## 📁 Files Created

- `claude_mcp_server.py` - MCP server that Claude connects to
- `claude_mcp_config.json` - Sample Claude Desktop configuration
- `setup_claude_mcp.sh` - Automated setup script
- `test_claude_mcp.py` - Test script to verify the integration
- `templates/claude_mcp_config.html` - Web-based configuration page
- `CLAUDE_MCP_INTEGRATION.md` - This documentation

## 🛠 Setup Options

### Option 1: Web Interface (Recommended)

1. **Start Falco Service**:
   ```bash
   python3 app.py
   ```

2. **Open Web Configuration**:
   - Navigate to: `http://localhost:8080/claude-mcp-config`
   - Click "Auto Setup Claude" button
   - Follow the on-screen instructions

3. **Restart Claude Desktop** to load the new configuration

### Option 2: Manual Setup

1. **Run Setup Script**:
   ```bash
   ./setup_claude_mcp.sh
   ```

2. **Restart Claude Desktop**

### Option 3: Manual Configuration

1. **Create Claude config directory**:
   ```bash
   mkdir -p ~/.config/claude-desktop
   ```

2. **Create configuration file** at `~/.config/claude-desktop/config.json`:
   ```json
   {
     "mcpServers": {
       "falco-ai-alerts": {
         "command": "python3",
         "args": ["/path/to/your/falco-rag-ai-gateway/claude_mcp_server.py"],
         "env": {
           "FALCO_API_BASE": "http://localhost:8080"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop**

## 🧪 Testing

### Test the MCP Server
```bash
python3 test_claude_mcp.py
```

### Test in Claude
Ask Claude:
- "Show me recent security alerts from Falco"
- "Analyze the latest critical security alert"
- "What's the current security status of my system?"

## 🔧 Available Tools

Claude will have access to these security tools:

- **`get_security_alerts`** - Retrieve security alerts with filtering
- **`analyze_security_alert`** - Get AI analysis of specific alerts
- **`get_alert_statistics`** - Retrieve alert statistics and trends
- **`analyze_system_state`** - Get system health analysis
- **`get_contextual_information`** - Gather context for alerts
- **`recommend_actions`** - Get action recommendations
- **`search_knowledge_base`** - Search accumulated knowledge

## 📊 Web Dashboard

Access the configuration dashboard at:
- **URL**: `http://localhost:8080/claude-mcp-config`
- **Features**:
  - Real-time status monitoring
  - Automatic setup
  - Configuration download
  - Connection testing
  - Available tools display

## 🔒 Security

- **Local Communication**: MCP server runs locally on your machine
- **No External Dependencies**: Direct connection between Claude and your Falco system
- **Configurable Access**: Control which tools Claude can access
- **Audit Trail**: All tool calls are logged

## 🚨 Troubleshooting

### Claude Can't See MCP Tools

1. **Check Falco Service**: Ensure `python3 app.py` is running
2. **Verify Configuration**: Check `~/.config/claude-desktop/config.json`
3. **Restart Claude**: Close and reopen Claude Desktop
4. **Check Logs**: Look at Claude Desktop logs for MCP errors

### MCP Server Not Starting

1. **Check Dependencies**: Ensure `requests` package is installed
2. **Verify Script Path**: Check the path in Claude configuration
3. **Test Manually**: Run `python3 claude_mcp_server.py` manually

### Connection Errors

1. **Check Falco Port**: Ensure Falco is running on the correct port (default: 8080)
2. **Firewall Settings**: Verify local connections are allowed
3. **Test API**: Try `curl http://localhost:8080/health`

## 🔄 Updates

To update the integration:

1. **Pull Latest Changes**: Update your Falco AI Alert System
2. **Update Configuration**: Re-run the setup script if needed
3. **Restart Services**: Restart both Falco and Claude Desktop

## 📞 Support

- **Web Interface**: Use the built-in diagnostics at `/claude-mcp-config`
- **Test Script**: Run `python3 test_claude_mcp.py` to diagnose issues
- **Logs**: Check Falco application logs for MCP-related errors

---

**Note**: This integration requires Claude Desktop application and a running Falco AI Alert System instance. 