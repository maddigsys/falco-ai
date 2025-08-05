#!/usr/bin/env python3
"""
JSON-RPC over stdio MCP Server for Falco Vanguard
Provides standard MCP compatibility with JSON-RPC protocol over stdin/stdout
"""

import asyncio
import json
import sys
import logging
import time
import uuid
from typing import Dict, Any, Optional, AsyncIterator
import requests
from datetime import datetime

# Configure logging to stderr so it doesn't interfere with JSON-RPC
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

class JSONRPCMCPServer:
    """JSON-RPC MCP Server that communicates over stdin/stdout"""
    
    def __init__(self, falco_api_base="http://localhost:8080"):
        self.falco_api_base = falco_api_base
        self.sessions: Dict[str, Dict] = {}
        self.tools = []
        self.resources = []
        self.server_info = {
            "name": "falco-ai-alerts-mcp",
            "version": "1.0.0",
            "protocol_version": "2024-11-05"
        }
        self.initialize_tools()
        
    def initialize_tools(self):
        """Initialize available tools from Falco service"""
        try:
            response = requests.get(f"{self.falco_api_base}/api/mcp/tools", timeout=5)
            if response.status_code == 200:
                tools_data = response.json()
                if isinstance(tools_data, list):
                    for tool in tools_data:
                        self.tools.append({
                            "name": tool["name"],
                            "description": tool["description"],
                            "inputSchema": tool.get("parameters", {
                                "type": "object",
                                "properties": {},
                                "required": []
                            })
                        })
                    logger.info(f"Loaded {len(self.tools)} tools from Falco service")
                    return
        except Exception as e:
            logger.warning(f"Could not load tools from Falco service: {e}")
        
        # Fallback tools if Falco service is not available
        self.tools = [
            {
                "name": "get_security_alerts",
                "description": "Retrieve security alerts from Falco with filtering options",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string", 
                            "description": "Alert status filter (all, unread, read, dismissed)",
                            "enum": ["all", "unread", "read", "dismissed"]
                        },
                        "priority": {
                            "type": "string",
                            "description": "Priority filter (all, critical, error, warning, info)",
                            "enum": ["all", "critical", "error", "warning", "info"]
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of alerts to return (default: 10, max: 100)",
                            "minimum": 1,
                            "maximum": 100,
                            "default": 10
                        },
                        "time_range": {
                            "type": "string",
                            "description": "Time range filter",
                            "enum": ["1h", "24h", "7d", "30d"],
                            "default": "24h"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "analyze_security_alert",
                "description": "Get AI-powered analysis for a specific security alert",
                "inputSchema": {
                    "type": "object", 
                    "properties": {
                        "alert_id": {
                            "type": "integer",
                            "description": "Alert ID to analyze",
                            "minimum": 1
                        },
                        "language": {
                            "type": "string",
                            "description": "Analysis language (default: en)",
                            "enum": ["en", "es", "fr", "de", "pt", "zh", "hi", "ar"],
                            "default": "en"
                        },
                        "include_recommendations": {
                            "type": "boolean",
                            "description": "Include remediation recommendations",
                            "default": true
                        }
                    },
                    "required": ["alert_id"]
                }
            },
            {
                "name": "get_alert_statistics",
                "description": "Retrieve alert statistics and trends",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "time_range": {
                            "type": "string",
                            "description": "Time range for statistics",
                            "enum": ["1h", "24h", "7d", "30d"],
                            "default": "24h"
                        },
                        "include_breakdown": {
                            "type": "boolean", 
                            "description": "Include breakdown by priority and rule",
                            "default": true
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "analyze_system_state",
                "description": "Get comprehensive system health and security status",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "components": {
                            "type": "array",
                            "description": "System components to analyze",
                            "items": {
                                "type": "string",
                                "enum": ["falco", "weaviate", "ollama", "mcp", "all"]
                            },
                            "default": ["all"]
                        },
                        "include_metrics": {
                            "type": "boolean",
                            "description": "Include detailed metrics",
                            "default": true
                        }
                    },
                    "required": []
                }
            }
        ]
        logger.info(f"Using {len(self.tools)} fallback tools")

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle JSON-RPC requests"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            logger.info(f"Handling request: {method}")
            
            if method == "initialize":
                return await self._handle_initialize(request_id, params)
            elif method == "initialized":
                return await self._handle_initialized(request_id)
            elif method == "tools/list":
                return await self._handle_tools_list(request_id)
            elif method == "tools/call":
                return await self._handle_tools_call(request_id, params)
            elif method == "resources/list":
                return await self._handle_resources_list(request_id)
            elif method == "resources/read":
                return await self._handle_resources_read(request_id, params)
            elif method == "ping":
                return await self._handle_ping(request_id)
            else:
                return self._error_response(request_id, -32601, f"Method not found: {method}")
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self._error_response(request.get("id"), -32603, f"Internal error: {str(e)}")

    async def _handle_initialize(self, request_id, params):
        """Handle initialize request"""
        client_info = params.get("clientInfo", {})
        logger.info(f"Initializing connection for client: {client_info.get('name', 'unknown')}")
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": self.server_info["protocol_version"],
                "capabilities": {
                    "tools": {
                        "listChanged": False
                    },
                    "resources": {
                        "subscribe": False,
                        "listChanged": False
                    },
                    "prompts": {
                        "listChanged": False
                    },
                    "logging": {}
                },
                "serverInfo": self.server_info,
                "instructions": "Falco Vanguard MCP Server - Access security alerts and analysis tools"
            }
        }

    async def _handle_initialized(self, request_id):
        """Handle initialized notification"""
        logger.info("Client initialization completed")
        return None  # No response for notifications

    async def _handle_tools_list(self, request_id):
        """Handle tools/list request"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": self.tools
            }
        }

    async def _handle_tools_call(self, request_id, params):
        """Handle tools/call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            return self._error_response(request_id, -32602, "Tool name is required")
        
        # Find the tool
        tool = next((t for t in self.tools if t["name"] == tool_name), None)
        if not tool:
            return self._error_response(request_id, -32602, f"Tool '{tool_name}' not found")
        
        try:
            # Execute the tool
            result = await self._execute_tool(tool_name, arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ],
                    "isError": result.get("success", True) is False
                }
            }
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return self._error_response(request_id, -32603, f"Tool execution failed: {str(e)}")

    async def _handle_resources_list(self, request_id):
        """Handle resources/list request"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": self.resources
            }
        }

    async def _handle_resources_read(self, request_id, params):
        """Handle resources/read request"""
        uri = params.get("uri")
        if not uri:
            return self._error_response(request_id, -32602, "Resource URI is required")
        
        # For now, return empty content
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "text/plain",
                        "text": "Resource not implemented"
                    }
                ]
            }
        }

    async def _handle_ping(self, request_id):
        """Handle ping request"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "server": self.server_info["name"]
            }
        }

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool via Falco API"""
        try:
            # Try to call the Falco MCP service
            response = requests.post(
                f"{self.falco_api_base}/api/mcp/test-tool/{tool_name}",
                json={"parameters": arguments},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "tool": tool_name,
                    "arguments": arguments,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"Falco service returned status {response.status_code}",
                    "details": response.text[:500],
                    "tool": tool_name,
                    "arguments": arguments
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Cannot connect to Falco Vanguard",
                "message": "Please ensure the Falco service is running on http://localhost:8080",
                "tool": tool_name,
                "arguments": arguments,
                "fallback_data": self._get_fallback_data(tool_name, arguments)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution error: {str(e)}",
                "tool": tool_name,
                "arguments": arguments
            }

    def _get_fallback_data(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback data when Falco service is unavailable"""
        if tool_name == "get_security_alerts":
            return {
                "alerts": [
                    {
                        "id": 1,
                        "rule": "Terminal shell in container",
                        "priority": "warning",
                        "output": "A shell was used as the entrypoint/exec point into a container",
                        "timestamp": datetime.now().isoformat()
                    }
                ],
                "total_count": 1,
                "note": "Sample data - Falco service not available"
            }
        elif tool_name == "analyze_security_alert":
            return {
                "analysis": "Alert analysis not available - Falco service not running",
                "recommendations": [],
                "severity": "unknown"
            }
        elif tool_name == "get_alert_statistics":
            return {
                "total_alerts": 0,
                "by_priority": {"critical": 0, "warning": 0, "info": 0},
                "note": "Statistics not available - Falco service not running"
            }
        else:
            return {"message": f"Tool {tool_name} executed (offline mode)"}

    def _error_response(self, request_id, code: int, message: str) -> Dict[str, Any]:
        """Create JSON-RPC error response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

async def main():
    """Main event loop for the JSON-RPC MCP server"""
    server = JSONRPCMCPServer()
    
    logger.info("🚀 Falco JSON-RPC MCP Server started - waiting for client connections...")
    logger.info("📡 Protocol: JSON-RPC 2.0 over stdin/stdout")
    logger.info("🔧 Available tools: " + ", ".join([tool["name"] for tool in server.tools]))
    
    try:
        while True:
            # Read JSON-RPC request from stdin
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    logger.info("📨 End of input stream - shutting down")
                    break
                    
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    request = json.loads(line)
                    logger.debug(f"📥 Received request: {request.get('method', 'unknown')}")
                    
                    response = await server.handle_request(request)
                    
                    if response is not None:  # Don't send response for notifications
                        response_str = json.dumps(response)
                        print(response_str, flush=True)
                        logger.debug(f"📤 Sent response for {request.get('method', 'unknown')}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Invalid JSON received: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                    
            except EOFError:
                logger.info("📨 EOF reached - shutting down")
                break
                
    except KeyboardInterrupt:
        logger.info("🛑 Server shutting down...")
    except Exception as e:
        logger.error(f"💥 Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 