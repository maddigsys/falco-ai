#!/bin/bash
# Setup script for JSON-RPC MCP integration with Falco Vanguard

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_CONFIG_DIR="$HOME/.config/claude-desktop"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/config.json"

echo "🚀 Setting up JSON-RPC MCP integration for Falco Vanguard..."

# Create Claude config directory if it doesn't exist
if [ ! -d "$CLAUDE_CONFIG_DIR" ]; then
    echo "📁 Creating Claude config directory: $CLAUDE_CONFIG_DIR"
    mkdir -p "$CLAUDE_CONFIG_DIR"
fi

# Generate the Claude config with the current script path
cat > "$CLAUDE_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "falco-vanguard": {
      "command": "python3",
      "args": ["$SCRIPT_DIR/jsonrpc_mcp_server.py"],
      "env": {
        "FALCO_API_BASE": "http://localhost:8080"
      }
    }
  }
}
EOF

echo "✅ Claude configuration created at: $CLAUDE_CONFIG_FILE"

# Make the MCP server script executable
chmod +x "$SCRIPT_DIR/jsonrpc_mcp_server.py"
echo "✅ Made jsonrpc_mcp_server.py executable"

# Create VS Code MCP configuration
VSCODE_CONFIG_DIR="$HOME/.config/Code/User"
VSCODE_MCP_CONFIG="$VSCODE_CONFIG_DIR/mcp-servers.json"

if [ -d "$VSCODE_CONFIG_DIR" ]; then
    echo "📁 Creating VS Code MCP configuration..."
    cat > "$VSCODE_MCP_CONFIG" << EOF
{
  "mcpServers": {
    "falco-vanguard": {
      "command": "python3",
      "args": ["$SCRIPT_DIR/jsonrpc_mcp_server.py"],
      "env": {
        "FALCO_API_BASE": "http://localhost:8080"
      },
      "description": "Falco Vanguard - Security monitoring and analysis tools"
    }
  }
}
EOF
    echo "✅ VS Code MCP configuration created at: $VSCODE_MCP_CONFIG"
fi

# Create Cursor MCP configuration
CURSOR_CONFIG_DIR="$HOME/.config/cursor/User"
CURSOR_MCP_CONFIG="$CURSOR_CONFIG_DIR/mcp-servers.json"

if [ -d "$CURSOR_CONFIG_DIR" ]; then
    echo "📁 Creating Cursor MCP configuration..."
    cat > "$CURSOR_MCP_CONFIG" << EOF
{
  "mcpServers": {
    "falco-vanguard": {
      "command": "python3",
      "args": ["$SCRIPT_DIR/jsonrpc_mcp_server.py"],
      "env": {
        "FALCO_API_BASE": "http://localhost:8080"
      },
      "description": "Falco Vanguard - Security monitoring and analysis tools"
    }
  }
}
EOF
    echo "✅ Cursor MCP configuration created at: $CURSOR_MCP_CONFIG"
fi

# Test dependencies
echo "🧪 Testing dependencies..."
if python3 -c "import json, asyncio, requests; print('✅ Python dependencies available')"; then
    echo "✅ Python dependencies are available"
else
    echo "❌ Missing Python dependencies. Please install: requests"
    echo "   Run: pip3 install requests"
    exit 1
fi

# Test the MCP server script
echo "🧪 Testing JSON-RPC MCP server script..."
if python3 -c "
import sys
sys.path.append('$SCRIPT_DIR')
try:
    from jsonrpc_mcp_server import JSONRPCMCPServer
    server = JSONRPCMCPServer()
    print('✅ JSON-RPC MCP server script is valid')
except Exception as e:
    print(f'❌ Error testing server script: {e}')
    sys.exit(1)
"; then
    echo "✅ JSON-RPC MCP server script is working"
else
    echo "❌ JSON-RPC MCP server script has issues"
    exit 1
fi

echo ""
echo "🎉 Setup complete! JSON-RPC MCP integration is ready."
echo ""
echo "📋 Configuration files created:"
echo "   • Claude Desktop: $CLAUDE_CONFIG_FILE"
if [ -f "$VSCODE_MCP_CONFIG" ]; then
    echo "   • VS Code: $VSCODE_MCP_CONFIG"
fi
if [ -f "$CURSOR_MCP_CONFIG" ]; then
    echo "   • Cursor: $CURSOR_MCP_CONFIG"
fi
echo ""
echo "📋 Next steps:"
echo "   1. Ensure your Falco Vanguard is running: python3 app.py"
echo "   2. Restart your AI client (Claude Desktop, VS Code, Cursor)"
echo "   3. Your AI client will now have access to Falco security tools!"
echo ""
echo "🔧 Available tools in your AI client:"
echo "   • get_security_alerts - Retrieve security alerts from Falco"
echo "   • analyze_security_alert - Get AI analysis of specific alerts"
echo "   • get_alert_statistics - Retrieve alert statistics and trends"
echo "   • analyze_system_state - Get system health analysis"
echo ""
echo "💡 Test commands for your AI client:"
echo "   'Show me recent security alerts from Falco'"
echo "   'Analyze the latest critical security alert'"
echo "   'What is the current security status of my system?'"
echo ""
echo "📁 Server script: $SCRIPT_DIR/jsonrpc_mcp_server.py"
echo "🔧 Protocol: JSON-RPC 2.0 over stdin/stdout" 