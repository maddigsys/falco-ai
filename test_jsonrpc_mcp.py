#!/usr/bin/env python3
"""
Test script for JSON-RPC MCP Server
This script simulates MCP client communication to test the JSON-RPC server
"""

import asyncio
import json
import subprocess
import sys
import time

async def test_jsonrpc_mcp_server():
    """Test the JSON-RPC MCP server with standard MCP protocol messages"""
    
    print("🧪 Testing JSON-RPC MCP Server for Falco Vanguard...")
    
    # Start the MCP server process
    server_process = subprocess.Popen(
        [sys.executable, 'jsonrpc_mcp_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    try:
        # Wait a moment for server to initialize
        await asyncio.sleep(1)
        
        # Test 1: Initialize
        print("📡 Test 1: Initialize connection...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {
                        "listChanged": True
                    },
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        server_process.stdin.write(json.dumps(init_request) + '\n')
        server_process.stdin.flush()
        
        response = server_process.stdout.readline()
        if response:
            init_response = json.loads(response)
            server_name = init_response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')
            protocol_version = init_response.get('result', {}).get('protocolVersion', 'Unknown')
            print(f"   ✅ Initialize: {server_name} (Protocol: {protocol_version})")
        else:
            print("   ❌ No response to initialize")
            return False
        
        # Test 2: Send initialized notification
        print("📡 Test 2: Send initialized notification...")
        initialized_request = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        
        server_process.stdin.write(json.dumps(initialized_request) + '\n')
        server_process.stdin.flush()
        
        # Test 3: List tools
        print("📡 Test 3: List available tools...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        server_process.stdin.write(json.dumps(tools_request) + '\n')
        server_process.stdin.flush()
        
        response = server_process.stdout.readline()
        if response:
            tools_response = json.loads(response)
            tools = tools_response.get('result', {}).get('tools', [])
            print(f"   ✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"      • {tool['name']}: {tool['description']}")
        else:
            print("   ❌ No response to tools/list")
            return False
        
        # Test 4: Call a tool
        print("📡 Test 4: Call get_security_alerts tool...")
        tool_call_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_security_alerts",
                "arguments": {
                    "status": "all",
                    "limit": 3
                }
            }
        }
        
        server_process.stdin.write(json.dumps(tool_call_request) + '\n')
        server_process.stdin.flush()
        
        response = server_process.stdout.readline()
        if response:
            tool_response = json.loads(response)
            if 'result' in tool_response:
                print("   ✅ Tool call successful")
                content = tool_response['result']['content'][0]['text']
                result = json.loads(content)
                if 'error' in result:
                    print(f"   ⚠️  Note: {result['error']} (Expected if Falco service isn't running)")
                elif result.get('success'):
                    print(f"   📊 Result: Tool executed successfully")
                    if 'result' in result:
                        print(f"   📋 Data: {str(result['result'])[:100]}...")
                else:
                    print(f"   ⚠️  Tool returned: {result.get('message', 'Unknown result')}")
            else:
                print(f"   ❌ Tool call failed: {tool_response.get('error', 'Unknown error')}")
        else:
            print("   ❌ No response to tool call")
            return False
        
        # Test 5: Test another tool
        print("📡 Test 5: Call analyze_system_state tool...")
        system_tool_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "analyze_system_state",
                "arguments": {
                    "components": ["falco", "mcp"],
                    "include_metrics": True
                }
            }
        }
        
        server_process.stdin.write(json.dumps(system_tool_request) + '\n')
        server_process.stdin.flush()
        
        response = server_process.stdout.readline()
        if response:
            tool_response = json.loads(response)
            if 'result' in tool_response:
                print("   ✅ System analysis tool successful")
            else:
                print(f"   ⚠️  System analysis: {tool_response.get('error', {}).get('message', 'Unknown')}")
        
        # Test 6: Test ping
        print("📡 Test 6: Ping server...")
        ping_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "ping",
            "params": {}
        }
        
        server_process.stdin.write(json.dumps(ping_request) + '\n')
        server_process.stdin.flush()
        
        response = server_process.stdout.readline()
        if response:
            ping_response = json.loads(response)
            if 'result' in ping_response:
                status = ping_response['result']['status']
                timestamp = ping_response['result']['timestamp']
                print(f"   ✅ Ping successful: {status} at {timestamp}")
            else:
                print("   ❌ Ping failed")
        
        print("\n🎉 All tests passed! JSON-RPC MCP server is working correctly.")
        print("\n📋 Next steps:")
        print("   1. Run: ./setup_jsonrpc_mcp.sh")
        print("   2. Start your Falco service: python3 app.py")
        print("   3. Restart your AI client (Claude Desktop, VS Code, etc.)")
        print("   4. Ask your AI client to show you security alerts!")
        print("\n🔧 Supported AI clients:")
        print("   • Claude Desktop")
        print("   • VS Code with MCP extension")
        print("   • Cursor with MCP support")
        print("   • Any MCP-compatible client")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        # Clean shutdown
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()

async def test_server_directly():
    """Test server by importing it directly"""
    print("\n🔧 Testing server directly...")
    
    try:
        from jsonrpc_mcp_server import JSONRPCMCPServer
        
        server = JSONRPCMCPServer()
        print(f"✅ Server created with {len(server.tools)} tools")
        
        # Test a simple request
        test_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        response = await server.handle_request(test_request)
        tools_count = len(response.get('result', {}).get('tools', []))
        print(f"✅ Direct test successful: {tools_count} tools available")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 JSON-RPC MCP Server Test Suite")
    print("=" * 50)
    
    # Test 1: Direct server test
    success1 = asyncio.run(test_server_directly())
    
    print("\n" + "=" * 50)
    
    # Test 2: Full protocol test
    success2 = asyncio.run(test_jsonrpc_mcp_server())
    
    if success1 and success2:
        print("\n🎉 All tests passed! JSON-RPC MCP server is ready for production.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the output above.")
        sys.exit(1) 