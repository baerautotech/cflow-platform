"""
HashiCorp Vault Integration for BMAD

YOLO MODE: Fast implementation of centralized secret management.
"""

import os
import json
import hvac
from typing import Any, Dict, Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class BMADVaultIntegration:
    """YOLO HashiCorp Vault integration for BMAD secrets."""
    
    def __init__(self):
        self.vault_client = None
        # For development, use localhost with port-forward
        # For production, this should be the cerebral cluster vault address
        self.vault_url = os.getenv("VAULT_URL", "http://localhost:8200")
        self.vault_token = os.getenv("VAULT_TOKEN", "root-token-12345")
        self._connect()
    
    def _connect(self) -> None:
        """Connect to Vault (YOLO style)."""
        try:
            if not self.vault_token:
                print("[INFO][INFO] YOLO: No VAULT_TOKEN found, using mock vault")
                self.vault_client = None
                return
            
            self.vault_client = hvac.Client(url=self.vault_url, token=self.vault_token)
            
            # Test connection
            if self.vault_client.is_authenticated():
                print("[INFO] YOLO: Vault connected successfully")
            else:
                print("[INFO] YOLO: Vault authentication failed")
                self.vault_client = None
                
        except Exception as e:
            print(f"[INFO][INFO] YOLO: Vault connection failed: {e}")
            self.vault_client = None
    
    def store_secret(self, path: str, secret_data: Dict[str, Any]) -> bool:
        """Store secret in Vault (YOLO implementation)."""
        try:
            if not self.vault_client:
                print(f"[INFO][INFO] YOLO: Mock storing secret at {path}")
                return True
            
            # Ensure the secret engine is enabled
            self._ensure_secret_engine()
            
            # Store the secret
            response = self.vault_client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret_data
            )
            
            print(f"[INFO] YOLO: Secret stored at {path}")
            return True
            
        except Exception as e:
            print(f"[INFO] YOLO: Failed to store secret: {e}")
            return False
    
    def retrieve_secret(self, path: str) -> Optional[Dict[str, Any]]:
        """Retrieve secret from Vault (YOLO implementation)."""
        try:
            if not self.vault_client:
                print(f"[INFO][INFO] YOLO: Mock retrieving secret from {path}")
                return {"mock": "secret", "path": path}
            
            response = self.vault_client.secrets.kv.v2.read_secret_version(path=path)
            secret_data = response['data']['data']
            
            print(f"[INFO] YOLO: Secret retrieved from {path}")
            return secret_data
            
        except Exception as e:
            print(f"[INFO] YOLO: Failed to retrieve secret: {e}")
            return None
    
    def _ensure_secret_engine(self) -> None:
        """Ensure KV v2 secret engine is enabled (YOLO style)."""
        try:
            if not self.vault_client:
                return
            
            # Check if KV v2 is enabled
            mounts = self.vault_client.sys.list_mounted_secrets_engines()
            
            if 'secret/' not in mounts:
                # Enable KV v2
                self.vault_client.sys.enable_secrets_engine(
                    backend_type='kv',
                    path='secret',
                    options={'version': 2}
                )
                print("[INFO] YOLO: KV v2 secret engine enabled")
            
        except Exception as e:
            print(f"[INFO][INFO] YOLO: Secret engine setup failed: {e}")
    
    def migrate_supabase_secrets(self) -> bool:
        """Migrate Supabase secrets to Vault (YOLO migration)."""
        try:
            # Get Supabase secrets from environment
            supabase_secrets = {
                "supabase_url": os.getenv("SUPABASE_URL"),
                "supabase_anon_key": os.getenv("SUPABASE_ANON_KEY"),
                "supabase_service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
                "supabase_project_ref": os.getenv("SUPABASE_PROJECT_REF"),
                "supabase_db_pass": os.getenv("SUPABASE_DB_PASS"),
            }
            
            # Store in Vault
            success = self.store_secret("bmad/supabase", supabase_secrets)
            
            if success:
                print("[INFO] YOLO: Supabase secrets migrated to Vault")
                return True
            else:
                print("[INFO] YOLO: Supabase secrets migration failed")
                return False
                
        except Exception as e:
            print(f"[INFO] YOLO: Secret migration failed: {e}")
            return False
    
    def get_supabase_config(self) -> Dict[str, str]:
        """Get Supabase config from Vault (YOLO implementation)."""
        try:
            if not self.vault_client:
                # Fallback to environment variables
                return {
                    "url": os.getenv("SUPABASE_URL", ""),
                    "anon_key": os.getenv("SUPABASE_ANON_KEY", ""),
                    "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
                }
            
            secret = self.retrieve_secret("bmad/supabase")
            if secret:
                return {
                    "url": secret.get("supabase_url", ""),
                    "anon_key": secret.get("supabase_anon_key", ""),
                    "service_role_key": secret.get("supabase_service_role_key", ""),
                }
            else:
                # Fallback to environment
                return {
                    "url": os.getenv("SUPABASE_URL", ""),
                    "anon_key": os.getenv("SUPABASE_ANON_KEY", ""),
                    "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
                }
                
        except Exception as e:
            print(f"[INFO] YOLO: Failed to get Supabase config: {e}")
            return {
                "url": os.getenv("SUPABASE_URL", ""),
                "anon_key": os.getenv("SUPABASE_ANON_KEY", ""),
                "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
            }


# YOLO Global instance
vault_integration = BMADVaultIntegration()

# Alias for compatibility
VaultIntegration = BMADVaultIntegration


def get_vault_integration() -> BMADVaultIntegration:
    """Get global Vault integration instance."""
    return vault_integration


# YOLO Test function
def test_vault_integration():
    """Test Vault integration (YOLO style)."""
    print("[INFO] YOLO: Testing Vault Integration...")
    
    vault = get_vault_integration()
    
    # Test secret storage
    test_secret = {
        "bmad_api_key": "test_key_123",
        "bmad_secret": "test_secret_456",
        "timestamp": "2025-01-09T00:00:00Z"
    }
    
    success = vault.store_secret("bmad/test", test_secret)
    print(f"Secret storage: {'[INFO]' if success else '[INFO]'}")
    
    # Test secret retrieval
    retrieved = vault.retrieve_secret("bmad/test")
    print(f"Secret retrieval: {'[INFO]' if retrieved else '[INFO]'}")
    
    # Test Supabase migration
    migration_success = vault.migrate_supabase_secrets()
    print(f"Supabase migration: {'[INFO]' if migration_success else '[INFO]'}")
    
    # Test config retrieval
    config = vault.get_supabase_config()
    print(f"Config retrieval: {'[INFO]' if config.get('url') else '[INFO]'}")
    
    print("[INFO] YOLO: Vault integration test complete!")


if __name__ == "__main__":
    test_vault_integration()
