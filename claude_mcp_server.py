#!/usr/bin/env python3
"""
Claude-compatible MCP Server for Falco Vanguard
This script provides a JSON-RPC over stdio interface that Claude can connect to,
while bridging to the existing Falco MCP service.
"""

import asyncio
import json
import sys
import logging
from typing import Dict, Any, List
import requests
from datetime import datetime

# Configure logging to stderr so it doesn't interfere with JSON-RPC
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

class ClaudeMCPServer:
    """MCP Server that Claude can connect to via JSON-RPC over stdio"""
    
    def __init__(self, falco_api_base="http://localhost:8080"):
        self.falco_api_base = falco_api_base
        self.tools = {}
        self.resources = {}
        
    async def initialize(self):
        """Initialize the server and load available tools from Falco"""
        try:
            # Get available tools from Falco MCP service
            response = requests.get(f"{self.falco_api_base}/api/mcp/tools", timeout=5)
            if response.status_code == 200:
                tools_data = response.json()
                if isinstance(tools_data, list):
                    for tool in tools_data:
                        self.tools[tool['name']] = tool
                        logger.info(f"Loaded tool: {tool['name']}")
                else:
                    logger.warning("Invalid tools response format")
            else:
                logger.warning(f"Failed to load tools: {response.status_code}")
                
            # Define fallback tools if Falco service is not available
            if not self.tools:
                self._define_fallback_tools()
                
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            self._define_fallback_tools()
    
    def _define_fallback_tools(self):
        """Define basic tools if Falco service is unavailable"""
        self.tools = {
            "get_security_alerts": {
                "name": "get_security_alerts",
                "description": "Retrieve security alerts from Falco",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "description": "Alert status filter"},
                        "priority": {"type": "string", "description": "Priority filter"},
                        "limit": {"type": "integer", "description": "Number of alerts to return"}
                    }
                }
            },
            "analyze_security_alert": {
                "name": "analyze_security_alert",
                "description": "Get AI analysis of a security alert",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "alert_id": {"type": "integer", "description": "Alert ID to analyze"},
                        "language": {"type": "string", "description": "Analysis language", "default": "en"}
                    }
                }
            }
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-RPC requests from Claude"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {
                                "listChanged": False
                            },
                            "resources": {
                                "subscribe": False,
                                "listChanged": False
                            }
                        },
                        "serverInfo": {
                            "name": "falco-ai-alerts-mcp",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "tools/list":
                tools_list = [
                    {
                        "name": tool["name"],
                        "description": tool["description"],
                        "inputSchema": tool.get("parameters", {})
                    }
                    for tool in self.tools.values()
                ]
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": tools_list
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name not in self.tools:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": f"Tool '{tool_name}' not found"
                        }
                    }
                
                # Call the Falco MCP service
                result = await self._call_falco_tool(tool_name, arguments)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            
            elif method == "resources/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "resources": []
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    async def _call_falco_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the Falco MCP service"""
        try:
            # Try to call the Falco MCP service
            response = requests.post(
                f"{self.falco_api_base}/api/mcp/test-tool/{tool_name}",
                json={"parameters": arguments},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Falco service returned status {response.status_code}",
                    "details": response.text[:500]
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "error": "Cannot connect to Falco Vanguard",
                "message": "Please ensure the Falco service is running on http://localhost:8080",
                "fallback": f"Tool '{tool_name}' called with arguments: {arguments}"
            }
        except Exception as e:
            return {
                "error": f"Failed to call tool: {str(e)}",
                "tool": tool_name,
                "arguments": arguments
            }

async def main():
    """Main event loop for the MCP server"""
    server = ClaudeMCPServer()
    await server.initialize()
    
    logger.info("Falco MCP Server started - waiting for Claude connections...")
    
    try:
        while True:
            # Read JSON-RPC request from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
                
            try:
                request = json.loads(line.strip())
                response = await server.handle_request(request)
                
                # Send response to stdout
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response), flush=True)
                
    except KeyboardInterrupt:
        logger.info("Server shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 