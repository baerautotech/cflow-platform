"""
Vault Migration Script for BMAD

This script handles the migration of secrets from local files to HashiCorp Vault.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

from .vault_integration import get_vault_integration

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class VaultMigration:
    """Handles migration of secrets to HashiCorp Vault."""
    
    def __init__(self):
        self.vault = get_vault_integration()
        self.migration_log = []
    
    async def discover_local_secrets(self) -> Dict[str, Any]:
        """Discover all local secrets that need to be migrated."""
        secrets_discovered = {
            "environment_secrets": {},
            "local_files": [],
            "total_count": 0
        }
        
        # Check for environment variables
        env_secrets = {
            "SUPABASE_URL": os.getenv("SUPABASE_URL"),
            "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
            "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            "SUPABASE_PROJECT_REF": os.getenv("SUPABASE_PROJECT_REF"),
            "SUPABASE_DB_PASS": os.getenv("SUPABASE_DB_PASS"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "OPENAI_ORGANIZATION": os.getenv("OPENAI_ORGANIZATION"),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
            "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
            "GITHUB_USERNAME": os.getenv("GITHUB_USERNAME"),
            "REDIS_URL": os.getenv("REDIS_URL"),
            "REDIS_PASSWORD": os.getenv("REDIS_PASSWORD"),
            "VAULT_URL": os.getenv("VAULT_URL"),
            "VAULT_TOKEN": os.getenv("VAULT_TOKEN"),
            "VAULT_NAMESPACE": os.getenv("VAULT_NAMESPACE"),
        }
        
        # Filter out None values
        env_secrets = {k: v for k, v in env_secrets.items() if v is not None}
        secrets_discovered["environment_secrets"] = env_secrets
        secrets_discovered["total_count"] += len(env_secrets)
        
        # Check for local secret files
        secret_file_paths = [
            ".cerebraflow/secrets.json",
            ".env",
            ".env.local",
            ".env.production",
            "config/secrets.json",
            "secrets.json"
        ]
        
        for file_path in secret_file_paths:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        if file_path.endswith('.json'):
                            content = json.load(f)
                        else:
                            # Parse .env file
                            content = {}
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#') and '=' in line:
                                    key, value = line.split('=', 1)
                                    content[key] = value
                    
                    secrets_discovered["local_files"].append({
                        "path": file_path,
                        "secrets": content,
                        "count": len(content)
                    })
                    secrets_discovered["total_count"] += len(content)
                    
                except Exception as e:
                    print(f"[WARN] Failed to read {file_path}: {e}")
        
        return secrets_discovered
    
    async def migrate_secrets(self, dry_run: bool = False) -> Dict[str, Any]:
        """Migrate all discovered secrets to Vault."""
        migration_result = {
            "migration_id": f"migration_{int(asyncio.get_event_loop().time())}",
            "dry_run": dry_run,
            "discovered_secrets": await self.discover_local_secrets(),
            "migration_results": {},
            "success": True,
            "total_migrated": 0,
            "total_failed": 0,
            "errors": []
        }
        
        discovered = migration_result["discovered_secrets"]
        
        # Migrate environment secrets
        if discovered["environment_secrets"]:
            result = await self._migrate_environment_secrets(
                discovered["environment_secrets"], 
                dry_run
            )
            migration_result["migration_results"]["environment"] = result
            migration_result["total_migrated"] += result.get("migrated_count", 0)
            migration_result["total_failed"] += result.get("failed_count", 0)
            if not result.get("success"):
                migration_result["success"] = False
                migration_result["errors"].extend(result.get("errors", []))
        
        # Migrate local file secrets
        for file_info in discovered["local_files"]:
            result = await self._migrate_file_secrets(file_info, dry_run)
            migration_result["migration_results"][f"file_{file_info['path']}"] = result
            migration_result["total_migrated"] += result.get("migrated_count", 0)
            migration_result["total_failed"] += result.get("failed_count", 0)
            if not result.get("success"):
                migration_result["success"] = False
                migration_result["errors"].extend(result.get("errors", []))
        
        return migration_result
    
    async def _migrate_environment_secrets(
        self, 
        secrets: Dict[str, str], 
        dry_run: bool
    ) -> Dict[str, Any]:
        """Migrate environment secrets to Vault."""
        result = {
            "category": "environment",
            "dry_run": dry_run,
            "migrated_count": 0,
            "failed_count": 0,
            "success": True,
            "errors": []
        }
        
        # Group secrets by category
        secret_categories = {
            "supabase": {},
            "openai": {},
            "anthropic": {},
            "github": {},
            "redis": {},
            "vault": {},
            "other": {}
        }
        
        for key, value in secrets.items():
            if key.startswith("SUPABASE_"):
                secret_categories["supabase"][key.lower()] = value
            elif key.startswith("OPENAI_"):
                secret_categories["openai"][key.lower()] = value
            elif key.startswith("ANTHROPIC_"):
                secret_categories["anthropic"][key.lower()] = value
            elif key.startswith("GITHUB_"):
                secret_categories["github"][key.lower()] = value
            elif key.startswith("REDIS_"):
                secret_categories["redis"][key.lower()] = value
            elif key.startswith("VAULT_"):
                secret_categories["vault"][key.lower()] = value
            else:
                secret_categories["other"][key.lower()] = value
        
        # Migrate each category
        for category, category_secrets in secret_categories.items():
            if not category_secrets:
                continue
                
            if dry_run:
                print(f"[DRY RUN] Would migrate {len(category_secrets)} {category} secrets")
                result["migrated_count"] += len(category_secrets)
            else:
                try:
                    vault_result = await self.vault.store_secret(
                        category,
                        category_secrets,
                        metadata={
                            "category": category,
                            "migrated_from": "environment",
                            "migration_id": result["migration_id"]
                        }
                    )
                    
                    if vault_result.get("success"):
                        result["migrated_count"] += len(category_secrets)
                        print(f"[INFO] Migrated {len(category_secrets)} {category} secrets to Vault")
                    else:
                        result["failed_count"] += len(category_secrets)
                        result["success"] = False
                        result["errors"].append(f"Failed to migrate {category} secrets: {vault_result.get('error')}")
                        
                except Exception as e:
                    result["failed_count"] += len(category_secrets)
                    result["success"] = False
                    result["errors"].append(f"Error migrating {category} secrets: {str(e)}")
        
        return result
    
    async def _migrate_file_secrets(
        self, 
        file_info: Dict[str, Any], 
        dry_run: bool
    ) -> Dict[str, Any]:
        """Migrate secrets from a local file to Vault."""
        result = {
            "file_path": file_info["path"],
            "dry_run": dry_run,
            "migrated_count": 0,
            "failed_count": 0,
            "success": True,
            "errors": []
        }
        
        if dry_run:
            print(f"[DRY RUN] Would migrate {file_info['count']} secrets from {file_info['path']}")
            result["migrated_count"] = file_info["count"]
        else:
            try:
                # Use the file path as the secret path
                secret_path = f"local-file-{file_info['path'].replace('/', '-').replace('.', '-')}"
                
                vault_result = await self.vault.store_secret(
                    secret_path,
                    file_info["secrets"],
                    metadata={
                        "migrated_from": "local_file",
                        "source_file": file_info["path"],
                        "migration_id": result["migration_id"]
                    }
                )
                
                if vault_result.get("success"):
                    result["migrated_count"] = file_info["count"]
                    print(f"[INFO] Migrated {file_info['count']} secrets from {file_info['path']} to Vault")
                else:
                    result["failed_count"] = file_info["count"]
                    result["success"] = False
                    result["errors"].append(f"Failed to migrate secrets from {file_info['path']}: {vault_result.get('error')}")
                    
            except Exception as e:
                result["failed_count"] = file_info["count"]
                result["success"] = False
                result["errors"].append(f"Error migrating secrets from {file_info['path']}: {str(e)}")
        
        return result
    
    async def verify_migration(self) -> Dict[str, Any]:
        """Verify that secrets were migrated successfully."""
        verification_result = {
            "success": True,
            "verified_secrets": {},
            "failed_verifications": [],
            "total_verified": 0,
            "total_failed": 0
        }
        
        # List all secrets in Vault
        list_result = await self.vault.list_secrets()
        
        if not list_result.get("success"):
            verification_result["success"] = False
            verification_result["failed_verifications"].append(f"Failed to list secrets: {list_result.get('error')}")
            return verification_result
        
        # Verify each secret can be retrieved
        secrets = list_result.get("secrets", [])
        
        for secret_path in secrets:
            try:
                retrieve_result = await self.vault.retrieve_secret(secret_path)
                
                if retrieve_result.get("success"):
                    verification_result["verified_secrets"][secret_path] = {
                        "retrieved": True,
                        "metadata": retrieve_result.get("metadata", {}),
                        "version": retrieve_result.get("version")
                    }
                    verification_result["total_verified"] += 1
                else:
                    verification_result["failed_verifications"].append(f"Failed to retrieve {secret_path}: {retrieve_result.get('error')}")
                    verification_result["total_failed"] += 1
                    
            except Exception as e:
                verification_result["failed_verifications"].append(f"Error verifying {secret_path}: {str(e)}")
                verification_result["total_failed"] += 1
        
        if verification_result["total_failed"] > 0:
            verification_result["success"] = False
        
        return verification_result


async def run_migration(dry_run: bool = True):
    """Run the vault migration process."""
    print("[INFO] Starting Vault Migration Process")
    print(f"[INFO] Mode: {'DRY RUN' if dry_run else 'LIVE MIGRATION'}")
    print("=" * 60)
    
    migration = VaultMigration()
    
    # Discover secrets
    print("\n🔍 Discovering local secrets...")
    discovered = await migration.discover_local_secrets()
    
    print(f"Found {discovered['total_count']} secrets to migrate:")
    print(f"  • Environment secrets: {len(discovered['environment_secrets'])}")
    print(f"  • Local files: {len(discovered['local_files'])}")
    
    for file_info in discovered["local_files"]:
        print(f"    - {file_info['path']}: {file_info['count']} secrets")
    
    # Run migration
    print(f"\n🚀 {'Simulating' if dry_run else 'Executing'} migration...")
    migration_result = await migration.migrate_secrets(dry_run=dry_run)
    
    print(f"\n📊 Migration Results:")
    print(f"  • Total migrated: {migration_result['total_migrated']}")
    print(f"  • Total failed: {migration_result['total_failed']}")
    print(f"  • Success: {'✅' if migration_result['success'] else '❌'}")
    
    if migration_result["errors"]:
        print(f"\n❌ Errors:")
        for error in migration_result["errors"]:
            print(f"    - {error}")
    
    # Verify migration (only if not dry run)
    if not dry_run and migration_result["success"]:
        print(f"\n🔍 Verifying migration...")
        verification = await migration.verify_migration()
        
        print(f"  • Verified secrets: {verification['total_verified']}")
        print(f"  • Failed verifications: {verification['total_failed']}")
        print(f"  • Verification success: {'✅' if verification['success'] else '❌'}")
        
        if verification["failed_verifications"]:
            print(f"\n❌ Verification errors:")
            for error in verification["failed_verifications"]:
                print(f"    - {error}")
    
    return migration_result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate secrets to HashiCorp Vault")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Run in dry-run mode")
    parser.add_argument("--live", action="store_true", help="Run live migration (overrides dry-run)")
    
    args = parser.parse_args()
    
    # If --live is specified, override dry-run
    dry_run = args.dry_run and not args.live
    
    asyncio.run(run_migration(dry_run=dry_run))
