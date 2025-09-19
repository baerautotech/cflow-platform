#!/bin/bash

# Cerebral Platform One-Touch Installer
# Generated for user: test_user_123
# Expires: 2025-09-20T18:42:09.989517

set -e

echo "🚀 Installing Cerebral Platform..."

# Create installation directory
INSTALL_DIR="$HOME/.cerebral-platform"
mkdir -p "$INSTALL_DIR"

# Save Redis configuration
cat > "$INSTALL_DIR/redis_config.json" << EOF
{
  "host": "redis.cerebral.baerautotech.com",
  "port": 6380,
  "token": "user_test_user_123_d7eda8e450ae4edd",
  "ssl": true,
  "ssl_cert_reqs": null,
  "ssl_check_hostname": false
}
EOF

# Save MCP configuration
cat > "$INSTALL_DIR/mcp_config.json" << EOF
{
  "api_url": "https://mcp.dev.baerautotech.com",
  "auth_token": "user_test_user_123_d7eda8e450ae4edd"
}
EOF

# Create environment file
cat > "$INSTALL_DIR/.env" << EOF
# Cerebral Platform Configuration
# Generated: 2025-09-19T18:42:09.989966
# Expires: 2025-09-20T18:42:09.989517

# Redis Configuration
REDIS_HOST=redis.cerebral.baerautotech.com
REDIS_PORT=6380
REDIS_TOKEN=user_test_user_123_d7eda8e450ae4edd
REDIS_SSL=true

# MCP Configuration
MCP_API_URL=https://mcp.dev.baerautotech.com
MCP_AUTH_TOKEN=user_test_user_123_d7eda8e450ae4edd

# BMAD Configuration
BMAD_VENDOR_PATH=vendor/bmad
EOF

# Create Python client
cat > "$INSTALL_DIR/cerebral_client.py" << 'EOF'
import os
import json
import redis
import requests
from pathlib import Path

class CerebralClient:
    def __init__(self):
        self.config_dir = Path.home() / ".cerebral-platform"
        self.load_config()
    
    def load_config(self):
        with open(self.config_dir / "redis_config.json") as f:
            self.redis_config = json.load(f)
        with open(self.config_dir / "mcp_config.json") as f:
            self.mcp_config = json.load(f)
    
    def get_redis_client(self):
        return redis.Redis(
            host=self.redis_config['host'],
            port=self.redis_config['port'],
            password=self.redis_config['token'],
            ssl=self.redis_config['ssl'],
            ssl_cert_reqs=None,
            ssl_check_hostname=False,
            decode_responses=True
        )
    
    def execute_mcp_tool(self, tool_name, parameters=None):
        response = requests.post(
            f"https://mcp.dev.baerautotech.com/execute",
            json={
                "tool_name": tool_name,
                "parameters": parameters or {}
            },
            headers={
                "Authorization": f"Bearer {mcp_config['auth_token']}",
                "Content-Type": "application/json"
            }
        )
        return response.json()

if __name__ == "__main__":
    client = CerebralClient()
    print("✅ Cerebral Platform client ready!")
EOF

echo "✅ Installation complete!"
echo "📁 Installation directory: $INSTALL_DIR"
echo "🔑 Redis token expires: 2025-09-20T18:42:09.989517"
echo ""
echo "To use the platform:"
echo "  python $INSTALL_DIR/cerebral_client.py"
echo ""
echo "For more information, see: $INSTALL_DIR/README.md"
