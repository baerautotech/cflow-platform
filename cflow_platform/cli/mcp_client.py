#!/usr/bin/env python3
"""
MCP Client for Cursor IDE Integration
Connects to the cerebral cluster MCP API
"""

import sys
import json
import requests
import argparse
from typing import Dict, Any, List
import os


class CerebralMCPClient:
    """MCP Client for cerebral cluster API"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Cerebral-MCP-Client/1.0'
        })
    
    def initialize(self) -> Dict[str, Any]:
        """Initialize MCP connection"""
        try:
            response = self.session.get(f"{self.server_url}/health")
            if response.status_code == 200:
                health_data = response.json()
                return {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": True,
                        "resources": True,
                        "prompts": True
                    },
                    "serverInfo": {
                        "name": "cerebral-mcp-api",
                        "version": "1.0.0"
                    },
                    "health": health_data
                }
            else:
                raise Exception(f"Health check failed: {response.status_code}")
        except Exception as e:
            return {
                "error": str(e),
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": True,
                    "resources": True,
                    "prompts": True
                },
                "serverInfo": {
                    "name": "cerebral-mcp-api",
                    "version": "1.0.0"
                }
            }
    
    def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        try:
            response = self.session.get(f"{self.server_url}/tools")
            if response.status_code == 200:
                tools_data = response.json()
                return {
                    "tools": tools_data.get("tools", [])
                }
            else:
                raise Exception(f"Tools list failed: {response.status_code}")
        except Exception as e:
            return {"error": str(e), "tools": []}
    
    def call_tool(self, name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a specific tool"""
        try:
            payload = {
                "name": name,
                "arguments": arguments or {}
            }
            response = self.session.post(
                f"{self.server_url}/tools/execute",
                json=payload
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"Tool execution failed: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            return {"error": str(e)}
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP protocol requests"""
        method = request.get("method", "")
        params = request.get("params", {})
        
        if method == "initialize":
            return self.initialize()
        elif method == "tools/list":
            return self.list_tools()
        elif method == "tools/call":
            return self.call_tool(
                params.get("name", ""),
                params.get("arguments", {})
            )
        else:
            return {"error": f"Unknown method: {method}"}


def main():
    """Main MCP client entry point"""
    parser = argparse.ArgumentParser(description="Cerebral MCP Client")
    parser.add_argument("--server-url", required=True, help="MCP API server URL")
    parser.add_argument("--test", action="store_true", help="Test connection")
    args = parser.parse_args()
    
    client = CerebralMCPClient(args.server_url)
    
    if args.test:
        # Test mode - just check health
        print("Testing MCP API connection...")
        result = client.initialize()
        print(json.dumps(result, indent=2))
        return
    
    # MCP protocol mode - read from stdin
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                request = json.loads(line.strip())
                response = client.handle_request(request)
                
                # Send response back to Cursor
                print(json.dumps(response))
                sys.stdout.flush()
                
            except json.JSONDecodeError:
                continue
            except Exception as e:
                error_response = {"error": str(e)}
                print(json.dumps(error_response))
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        pass
    except Exception as e:
        error_response = {"error": f"Client error: {str(e)}"}
        print(json.dumps(error_response))
        sys.stdout.flush()


if __name__ == "__main__":
    main()

