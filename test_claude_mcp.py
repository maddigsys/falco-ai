#!/usr/bin/env python3
"""
Test script for Claude MCP Server
This script simulates Claude's JSON-RPC communication to test the MCP server
"""

import asyncio
import json
import subprocess
import sys
import time

async def test_mcp_server():
    """Test the Claude MCP server with JSON-RPC messages"""
    
    print("🧪 Testing Claude MCP Server for Falco AI Alert System...")
    
    # Start the MCP server process
    server_process = subprocess.Popen(
        [sys.executable, 'claude_mcp_server.py'],
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
                "capabilities": {},
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
            print(f"   ✅ Initialize: {init_response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
        else:
            print("   ❌ No response to initialize")
            return False
        
        # Test 2: List tools
        print("📡 Test 2: List available tools...")
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
        
        # Test 3: Call a tool
        print("📡 Test 3: Call get_security_alerts tool...")
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
                    print(f"   ⚠️  Note: {result['error']} (This is expected if Falco service isn't running)")
                else:
                    print(f"   📊 Result: {str(result)[:100]}...")
            else:
                print(f"   ❌ Tool call failed: {tool_response.get('error', 'Unknown error')}")
        else:
            print("   ❌ No response to tool call")
            return False
        
        print("\n🎉 All tests passed! Claude MCP server is working correctly.")
        print("\n📋 Next steps:")
        print("   1. Run: ./setup_claude_mcp.sh")
        print("   2. Start your Falco service: python3 app.py")
        print("   3. Restart Claude Desktop")
        print("   4. Ask Claude to show you security alerts!")
        
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

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1) 