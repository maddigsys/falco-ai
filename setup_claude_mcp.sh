#!/bin/bash
# Setup script for Claude MCP integration with Falco Vanguard

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_CONFIG_DIR="$HOME/.config/claude-desktop"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/config.json"

echo "🚀 Setting up Claude MCP integration for Falco Vanguard..."

# Create Claude config directory if it doesn't exist
if [ ! -d "$CLAUDE_CONFIG_DIR" ]; then
    echo "📁 Creating Claude config directory: $CLAUDE_CONFIG_DIR"
    mkdir -p "$CLAUDE_CONFIG_DIR"
fi

# Generate the Claude config with the current script path
cat > "$CLAUDE_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "falco-ai-alerts": {
      "command": "python3",
      "args": ["$SCRIPT_DIR/claude_mcp_server.py"],
      "env": {
        "FALCO_API_BASE": "http://localhost:8080"
      }
    }
  }
}
EOF

echo "✅ Claude configuration created at: $CLAUDE_CONFIG_FILE"

# Make the MCP server script executable
chmod +x "$SCRIPT_DIR/claude_mcp_server.py"
echo "✅ Made claude_mcp_server.py executable"

# Test the MCP server script
echo "🧪 Testing MCP server script..."
if python3 -c "import asyncio, json, sys, requests; print('✅ Dependencies available')"; then
    echo "✅ Python dependencies are available"
else
    echo "❌ Missing Python dependencies. Please install: requests"
    echo "   Run: pip3 install requests"
    exit 1
fi

echo ""
echo "🎉 Setup complete! Claude is now configured to use Falco MCP server."
echo ""
echo "📋 Next steps:"
echo "   1. Ensure your Falco Vanguard is running: python3 app.py"
echo "   2. Restart Claude Desktop application"
echo "   3. Claude will now have access to Falco security tools!"
echo ""
echo "🔧 Available tools in Claude:"
echo "   • get_security_alerts - Retrieve security alerts from Falco"
echo "   • analyze_security_alert - Get AI analysis of specific alerts"
echo "   • get_alert_statistics - Get alert statistics and trends"
echo "   • analyze_system_state - Get system health analysis"
echo ""
echo "💡 You can test the connection by asking Claude:"
echo "   'Show me recent security alerts from Falco'"
echo "   'Analyze the latest critical security alert'"
echo ""
echo "📁 Configuration file: $CLAUDE_CONFIG_FILE"
echo "🚀 MCP Server script: $SCRIPT_DIR/claude_mcp_server.py" 