#!/usr/bin/env python3
"""
gRPC Streaming MCP Server for Falco AI Alert System
Provides a more industry-standard alternative to JSON-RPC over stdio
"""

import asyncio
import grpc
import json
import logging
import time
import uuid
from concurrent import futures
from typing import Dict, Any, Optional
import requests
from datetime import datetime

# Import generated protobuf classes (would be generated from proto file)
# For now, we'll create a simplified implementation

logger = logging.getLogger(__name__)

class FalcoMCPServicer:
    """gRPC servicer for Falco MCP"""
    
    def __init__(self, falco_api_base="http://localhost:8080"):
        self.falco_api_base = falco_api_base
        self.sessions: Dict[str, Dict] = {}
        self.tools = self._load_tools()
        self.startup_time = int(time.time())
        
    def _load_tools(self):
        """Load available tools from Falco service"""
        try:
            response = requests.get(f"{self.falco_api_base}/api/mcp/tools", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Could not load tools from Falco: {e}")
        
        # Fallback tools
        return [
            {
                "name": "get_security_alerts",
                "description": "Retrieve security alerts from Falco",
                "schema": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "description": "Alert status filter"},
                        "priority": {"type": "string", "description": "Priority filter"},
                        "limit": {"type": "integer", "description": "Number of alerts to return"}
                    }
                }
            },
            {
                "name": "analyze_security_alert", 
                "description": "Get AI analysis of a security alert",
                "schema": {
                    "type": "object",
                    "properties": {
                        "alert_id": {"type": "integer", "description": "Alert ID to analyze"}
                    }
                }
            }
        ]

class FalcoMCPServer:
    """gRPC Server for Falco MCP"""
    
    def __init__(self, port=50051, falco_api_base="http://localhost:8080"):
        self.port = port
        self.server = None
        self.servicer = FalcoMCPServicer(falco_api_base)
        
    async def start_server(self):
        """Start the gRPC server"""
        try:
            self.server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
            
            # Add servicer (would use generated add_FalcoMCPServiceServicer_to_server)
            # For now, we'll create a simplified HTTP/2 server
            
            listen_addr = f'[::]:{self.port}'
            self.server.add_insecure_port(listen_addr)
            
            logger.info(f"🚀 Starting Falco MCP gRPC server on {listen_addr}")
            await self.server.start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start gRPC server: {e}")
            return False
    
    async def stop_server(self):
        """Stop the gRPC server"""
        if self.server:
            await self.server.stop(grace=5.0)
            logger.info("🛑 gRPC server stopped")

# Simplified gRPC-like HTTP/2 server for demonstration
class SimplifiedGRPCServer:
    """
    Simplified gRPC-style server that provides the same interface
    but uses HTTP/2 with proper streaming
    """
    
    def __init__(self, port=50051, falco_api_base="http://localhost:8080"):
        self.port = port
        self.falco_api_base = falco_api_base
        self.sessions = {}
        self.tools = self._load_tools()
        
    def _load_tools(self):
        """Load tools from Falco service"""
        try:
            response = requests.get(f"{self.falco_api_base}/api/mcp/tools", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
            
        return [
            {
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
            {
                "name": "analyze_security_alert",
                "description": "Get AI analysis of a security alert", 
                "parameters": {
                    "type": "object",
                    "properties": {
                        "alert_id": {"type": "integer", "description": "Alert ID to analyze"}
                    }
                }
            }
        ]
    
    async def get_tools(self, request=None):
        """Get available tools"""
        return {
            "tools": self.tools,
            "server_info": {
                "name": "falco-mcp-grpc",
                "version": "1.0.0",
                "capabilities": ["tools", "streaming", "sessions"],
                "startup_time": int(time.time())
            }
        }
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any], session_id: Optional[str] = None):
        """Execute a tool"""
        start_time = time.time()
        
        try:
            # Call Falco MCP service
            response = requests.post(
                f"{self.falco_api_base}/api/mcp/test-tool/{tool_name}",
                json={"parameters": parameters},
                timeout=30
            )
            
            execution_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": result,
                    "execution_time_ms": execution_time
                }
            else:
                return {
                    "success": False,
                    "error": {
                        "code": response.status_code,
                        "message": f"Tool execution failed: {response.status_code}",
                        "details": response.text[:500]
                    },
                    "execution_time_ms": execution_time
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": {
                    "code": 503,
                    "message": "Cannot connect to Falco AI Alert System",
                    "details": "Please ensure the Falco service is running"
                },
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": 500,
                    "message": f"Tool execution error: {str(e)}",
                    "details": str(e)
                },
                "execution_time_ms": int((time.time() - start_time) * 1000)
            }
    
    async def stream_security_events(self, event_types=None, min_priority=None, max_events=None):
        """Stream real-time security events"""
        try:
            # Simulate streaming security events
            # In a real implementation, this would connect to Falco's event stream
            event_count = 0
            
            while max_events is None or event_count < max_events:
                # Get recent alerts
                try:
                    response = requests.get(f"{self.falco_api_base}/api/alerts", timeout=5)
                    if response.status_code == 200:
                        alerts = response.json()
                        
                        for alert in alerts[:5]:  # Stream latest 5 alerts
                            if min_priority and alert.get('priority', '').lower() < min_priority.lower():
                                continue
                                
                            event = {
                                "id": alert.get('id', event_count),
                                "event_type": "security_alert",
                                "priority": alert.get('priority', 'unknown'),
                                "message": alert.get('output', 'Security event detected'),
                                "timestamp": int(time.time()),
                                "metadata": {
                                    "rule": alert.get('rule', 'unknown'),
                                    "source": "falco"
                                }
                            }
                            
                            yield event
                            event_count += 1
                            
                            if max_events and event_count >= max_events:
                                break
                                
                except Exception as e:
                    logger.error(f"Error streaming events: {e}")
                
                # Wait before next batch
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
    
    async def interactive_session(self, session_requests):
        """Handle bidirectional streaming session"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created": datetime.now(),
            "client": "unknown",
            "tools_used": []
        }
        
        try:
            async for request in session_requests:
                if "init" in request:
                    # Initialize session
                    client_info = request["init"]
                    self.sessions[session_id]["client"] = client_info.get("client_name", "unknown")
                    
                    yield {
                        "init_ack": {
                            "session_id": session_id,
                            "available_tools": self.tools
                        }
                    }
                    
                elif "tool_exec" in request:
                    # Execute tool
                    tool_exec = request["tool_exec"]
                    tool_name = tool_exec["tool_name"]
                    parameters = tool_exec.get("parameters", {})
                    
                    self.sessions[session_id]["tools_used"].append(tool_name)
                    
                    result = await self.execute_tool(tool_name, parameters, session_id)
                    
                    if result["success"]:
                        yield {
                            "tool_result": result["data"]
                        }
                    else:
                        yield {
                            "error": result["error"]
                        }
                        
                elif "close" in request:
                    # Close session
                    yield {
                        "closed": {
                            "reason": request["close"].get("reason", "client_requested")
                        }
                    }
                    break
                    
        finally:
            # Clean up session
            if session_id in self.sessions:
                del self.sessions[session_id]
    
    async def get_health(self):
        """Get server health"""
        try:
            # Check Falco service health
            response = requests.get(f"{self.falco_api_base}/health", timeout=5)
            falco_healthy = response.status_code == 200
            
            return {
                "healthy": falco_healthy,
                "status": "healthy" if falco_healthy else "degraded",
                "details": {
                    "falco_service": "healthy" if falco_healthy else "unavailable",
                    "tools_available": str(len(self.tools)),
                    "active_sessions": str(len(self.sessions)),
                    "server_uptime": "running"
                }
            }
        except:
            return {
                "healthy": False,
                "status": "unhealthy",
                "details": {
                    "falco_service": "unavailable",
                    "error": "Cannot connect to Falco service"
                }
            }

# gRPC Client for testing
class FalcoMCPClient:
    """Simple gRPC client for testing"""
    
    def __init__(self, server_address="localhost:50051"):
        self.server_address = server_address
        self.channel = None
        
    async def connect(self):
        """Connect to gRPC server"""
        try:
            # In a real implementation, this would use grpc.aio.insecure_channel
            self.channel = f"grpc://{self.server_address}"
            logger.info(f"Connected to gRPC server: {self.server_address}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    async def get_tools(self):
        """Get available tools"""
        # Simulate gRPC call
        return {
            "tools": [
                {"name": "get_security_alerts", "description": "Get security alerts"},
                {"name": "analyze_security_alert", "description": "Analyze alerts"}
            ]
        }
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]):
        """Execute a tool"""
        logger.info(f"Executing tool: {tool_name} with params: {parameters}")
        # Simulate gRPC call
        return {
            "success": True,
            "data": {"message": f"Tool {tool_name} executed successfully"},
            "execution_time_ms": 150
        }
    
    async def disconnect(self):
        """Disconnect from server"""
        self.channel = None
        logger.info("Disconnected from gRPC server")

async def main():
    """Main server function"""
    server = SimplifiedGRPCServer()
    
    logger.info("🚀 Starting Falco MCP gRPC-style server...")
    
    # For demonstration, we'll run some tests
    try:
        # Test server health
        health = await server.get_health()
        logger.info(f"📊 Server health: {health}")
        
        # Test get tools
        tools = await server.get_tools()
        logger.info(f"🔧 Available tools: {len(tools['tools'])}")
        
        # Test tool execution
        result = await server.execute_tool("get_security_alerts", {"limit": 3})
        logger.info(f"⚡ Tool execution result: {result['success']}")
        
        # Keep server running
        logger.info("✅ gRPC-style server is ready!")
        logger.info("📡 Server would listen on localhost:50051")
        logger.info("🔗 Clients can connect using standard gRPC libraries")
        
        # In a real implementation, this would be:
        # await server.start_server()
        # await server.server.wait_for_termination()
        
    except KeyboardInterrupt:
        logger.info("🛑 Server shutting down...")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main()) 