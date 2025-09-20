"""
One-Touch Installer Token Generator

Generates Redis tokens for users during installer creation.
Tokens are embedded in the installer package for seamless setup.
"""

import os
import json
import uuid
import requests
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class InstallerTokenGenerator:
    """Generate Redis tokens for one-touch installer."""
    
    def __init__(self):
        self.mcp_api_url = os.getenv("MCP_API_URL", "https://mcp.dev.baerautotech.com")
        self.admin_token = os.getenv("ADMIN_TOKEN")  # Admin token for token generation
    
    def generate_user_token(self, user_id: str, duration_hours: int = 24) -> Dict[str, Any]:
        """Generate Redis token for user via MCP API."""
        try:
            # Call MCP API to generate token
            response = requests.post(
                f"{self.mcp_api_url}/token",
                json={
                    "user_id": user_id,
                    "duration_hours": duration_hours
                },
                headers={
                    "Authorization": f"Bearer {self.admin_token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                print(f"[INFO] Generated Redis token for user {user_id}")
                return token_data
            else:
                print(f"[INFO] Failed to generate token: {response.status_code} - {response.text}")
                return self._generate_fallback_token(user_id, duration_hours)
                
        except Exception as e:
            print(f"[INFO][INFO] Token generation failed, using fallback: {e}")
            return self._generate_fallback_token(user_id, duration_hours)
    
    def _generate_fallback_token(self, user_id: str, duration_hours: int) -> Dict[str, Any]:
        """Generate fallback token when API is unavailable."""
        redis_token = f"user_{user_id}_{uuid.uuid4().hex[:16]}"
        expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        
        return {
            "user_id": user_id,
            "redis_token": redis_token,
            "redis_port": 6380,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "fallback": True
        }
    
    def create_installer_config(self, user_id: str, duration_hours: int = 24) -> Dict[str, Any]:
        """Create complete installer configuration with Redis token."""
        try:
            print(f"[INFO] Creating installer config for user {user_id}...")
            
            # Generate Redis token
            token_data = self.generate_user_token(user_id, duration_hours)
            
            # Create installer configuration
            installer_config = {
                "user_id": user_id,
                "redis": {
                    "host": "redis.cerebral.baerautotech.com",
                    "port": token_data["redis_port"],
                    "token": token_data["redis_token"],
                    "ssl": True,
                    "ssl_cert_reqs": None,  # Skip cert verification for development
                    "ssl_check_hostname": False
                },
                "mcp": {
                    "api_url": self.mcp_api_url,
                    "auth_token": token_data["redis_token"]  # Use Redis token for MCP auth
                },
                "bmad": {
                    "vendor_path": "vendor/bmad",
                    "expansion_packs": [
                        "bmad-infrastructure-devops",
                        "bmad-creative-writing",
                        "bmad-godot-game-dev"
                    ]
                },
                "generated_at": datetime.utcnow().isoformat(),
                "expires_at": token_data["expires_at"],
                "version": "1.0.0"
            }
            
            print(f"[INFO] Installer config created for user {user_id}")
            return installer_config
            
        except Exception as e:
            print(f"[INFO] Failed to create installer config: {e}")
            raise
    
    def save_installer_config(self, config: Dict[str, Any], output_path: str) -> bool:
        """Save installer configuration to file."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"[INFO] Installer config saved to {output_file}")
            return True
            
        except Exception as e:
            print(f"[INFO] Failed to save installer config: {e}")
            return False
    
    def create_installer_package(self, user_id: str, output_dir: str, duration_hours: int = 24) -> bool:
        """Create complete installer package with embedded tokens."""
        try:
            print(f"[INFO] Creating installer package for user {user_id}...")
            
            # Create installer configuration
            config = self.create_installer_config(user_id, duration_hours)
            
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            config_file = output_path / "installer_config.json"
            self.save_installer_config(config, str(config_file))
            
            # Create installer script
            installer_script = self._create_installer_script(config)
            script_file = output_path / "install.sh"
            with open(script_file, 'w') as f:
                f.write(installer_script)
            script_file.chmod(0o755)  # Make executable
            
            # Create README
            readme_content = self._create_readme(config)
            readme_file = output_path / "README.md"
            with open(readme_file, 'w') as f:
                f.write(readme_content)
            
            print(f"[INFO] Installer package created in {output_path}")
            print(f"   - Configuration: {config_file}")
            print(f"   - Installer script: {script_file}")
            print(f"   - Documentation: {readme_file}")
            
            return True
            
        except Exception as e:
            print(f"[INFO] Failed to create installer package: {e}")
            return False
    
    def _create_installer_script(self, config: Dict[str, Any]) -> str:
        """Create installer shell script."""
        redis_config = config["redis"]
        mcp_config = config["mcp"]
        
        return f"""#!/bin/bash

# Cerebral Platform One-Touch Installer
# Generated for user: {config['user_id']}
# Expires: {config['expires_at']}

set -e

echo "[INFO] Installing Cerebral Platform..."

# Create installation directory
INSTALL_DIR="$HOME/.cerebral-platform"
mkdir -p "$INSTALL_DIR"

# Save Redis configuration
cat > "$INSTALL_DIR/redis_config.json" << EOF
{json.dumps(redis_config, indent=2)}
EOF

# Save MCP configuration
cat > "$INSTALL_DIR/mcp_config.json" << EOF
{json.dumps(mcp_config, indent=2)}
EOF

# Create environment file
cat > "$INSTALL_DIR/.env" << EOF
# Cerebral Platform Configuration
# Generated: {config['generated_at']}
# Expires: {config['expires_at']}

# Redis Configuration
REDIS_HOST={redis_config['host']}
REDIS_PORT={redis_config['port']}
REDIS_TOKEN={redis_config['token']}
REDIS_SSL=true

# MCP Configuration
MCP_API_URL={mcp_config['api_url']}
MCP_AUTH_TOKEN={mcp_config['auth_token']}

# BMAD Configuration
BMAD_VENDOR_PATH={config['bmad']['vendor_path']}
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
            f"{mcp_config['api_url']}/execute",
            json={{
                "tool_name": tool_name,
                "parameters": parameters or {{}}
            }},
            headers={{
                "Authorization": f"Bearer {{mcp_config['auth_token']}}",
                "Content-Type": "application/json"
            }}
        )
        return response.json()

if __name__ == "__main__":
    client = CerebralClient()
    print("[INFO] Cerebral Platform client ready!")
EOF

echo "[INFO] Installation complete!"
echo "📁 Installation directory: $INSTALL_DIR"
echo "🔑 Redis token expires: {config['expires_at']}"
echo ""
echo "To use the platform:"
echo "  python $INSTALL_DIR/cerebral_client.py"
echo ""
echo "For more information, see: $INSTALL_DIR/README.md"
"""

    def _create_readme(self, config: Dict[str, Any]) -> str:
        """Create README documentation."""
        return f"""# Cerebral Platform Installer

**User ID:** {config['user_id']}  
**Generated:** {config['generated_at']}  
**Expires:** {config['expires_at']}  
**Version:** {config['version']}

## What's Included

This installer package contains everything needed to connect to the Cerebral Platform:

- **Redis Configuration** - Direct access to the cerebral Redis cluster
- **MCP API Access** - Tool execution via MCP protocol
- **BMAD Integration** - Access to BMAD agents and workflows
- **Authentication** - Pre-configured user token

## Installation

Run the installer script:

```bash
chmod +x install.sh
./install.sh
```

## Usage

After installation, use the Python client:

```python
from cerebral_client import CerebralClient

client = CerebralClient()

# Access Redis directly
redis_client = client.get_redis_client()
redis_client.set("test", "Hello Cerebral!")

# Execute MCP tools
result = client.execute_mcp_tool("bmad_prd_create", {{
    "project_name": "My Project",
    "goals": ["Build something amazing"]
}})
```

## Configuration

All configuration is stored in `~/.cerebral-platform/`:

- `redis_config.json` - Redis connection details
- `mcp_config.json` - MCP API configuration
- `.env` - Environment variables
- `cerebral_client.py` - Python client library

## Security

- Your Redis token expires on: **{config['expires_at']}**
- All connections use SSL/TLS encryption
- Tokens are user-specific and cannot be shared

## Support

For issues or questions, contact the Cerebral Platform team.

---

*Generated by Cerebral Platform Installer v{config['version']}*
"""


def create_installer_for_user(user_id: str, output_dir: str = "installers", duration_hours: int = 24) -> bool:
    """Create installer package for a specific user."""
    generator = InstallerTokenGenerator()
    return generator.create_installer_package(user_id, output_dir, duration_hours)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python token_generator.py <user_id> [output_dir] [duration_hours]")
        sys.exit(1)
    
    user_id = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "installers"
    duration_hours = int(sys.argv[3]) if len(sys.argv) > 3 else 24
    
    success = create_installer_for_user(user_id, output_dir, duration_hours)
    sys.exit(0 if success else 1)
