"""
BMAD Expansion Pack Storage Management

This module provides S3-based storage management for BMAD expansion packs,
including pack discovery, installation, and metadata management.
"""

import os
import json
import yaml
import asyncio
import hashlib
import io
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from minio import Minio
from minio.error import S3Error

from cflow_platform.core.config.vault_config import get_vault_config


@dataclass
class ExpansionPackMetadata:
    """Metadata for an expansion pack."""
    name: str
    version: str
    short_title: str
    description: str
    author: str
    license: str
    price: str
    category: str
    tags: List[str]
    commercial: bool
    slash_prefix: Optional[str] = None
    file_count: int = 0
    total_size_bytes: int = 0
    last_updated: Optional[str] = None
    download_count: int = 0
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


@dataclass
class PackFile:
    """Represents a file within an expansion pack."""
    path: str
    size_bytes: int
    content_type: str
    checksum: str
    last_modified: str
    category: str  # agents, templates, workflows, tasks, checklists, data, config


class ExpansionPackStorage:
    """S3-based storage manager for BMAD expansion packs."""
    
    def __init__(self):
        self.vault_config = get_vault_config()
        self.bucket_name = "bmad-expansion-packs"
        self.metadata_bucket = "bmad-expansion-metadata"
        self.minio_client = None
        self._ensure_minio_client()
    
    def _ensure_minio_client(self) -> None:
        """Initialize MinIO client with credentials from Vault."""
        try:
            # Get MinIO credentials from Vault
            minio_endpoint = self.vault_config.get_config_value_sync("MINIO_ENDPOINT", "minio")
            minio_access_key = self.vault_config.get_config_value_sync("MINIO_ACCESS_KEY", "minio")
            minio_secret_key = self.vault_config.get_config_value_sync("MINIO_SECRET_KEY", "minio")
            minio_secure = self.vault_config.get_config_value_sync("MINIO_SECURE", "minio", fallback_to_env=False)
            
            # Fallback to environment variables
            if not minio_endpoint:
                minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
            if not minio_access_key:
                minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
            if not minio_secret_key:
                minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
            if not minio_secure:
                minio_secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
            
            self.minio_client = Minio(
                minio_endpoint,
                access_key=minio_access_key,
                secret_key=minio_secret_key,
                secure=minio_secure
            )
            
            # Ensure buckets exist
            self._ensure_buckets()
            print(f"[INFO] Expansion Pack Storage: Connected to MinIO at {minio_endpoint}")
            
        except Exception as e:
            print(f"[WARN] Expansion Pack Storage: MinIO connection failed: {e}")
            self.minio_client = None
    
    def _ensure_buckets(self) -> None:
        """Ensure required S3 buckets exist."""
        if not self.minio_client:
            return
        
        try:
            buckets = [self.bucket_name, self.metadata_bucket]
            for bucket in buckets:
                if not self.minio_client.bucket_exists(bucket):
                    self.minio_client.make_bucket(bucket)
                    print(f"[INFO] Expansion Pack Storage: Created bucket {bucket}")
        except Exception as e:
            print(f"[WARN] Expansion Pack Storage: Failed to ensure buckets: {e}")
    
    async def list_available_packs(self) -> List[ExpansionPackMetadata]:
        """List all available expansion packs."""
        if not self.minio_client:
            return []
        
        try:
            # Get pack metadata from metadata bucket
            pack_list = []
            objects = self.minio_client.list_objects(self.metadata_bucket, prefix="pack_", recursive=True)
            
            for obj in objects:
                try:
                    # Download metadata file
                    response = self.minio_client.get_object(self.metadata_bucket, obj.object_name)
                    metadata_json = response.read().decode('utf-8')
                    metadata_dict = json.loads(metadata_json)
                    
                    # Create metadata object
                    metadata = ExpansionPackMetadata(**metadata_dict)
                    pack_list.append(metadata)
                    
                except Exception as e:
                    print(f"[WARN] Expansion Pack Storage: Failed to load metadata for {obj.object_name}: {e}")
                    continue
            
            return sorted(pack_list, key=lambda x: x.name)
            
        except Exception as e:
            print(f"[ERROR] Expansion Pack Storage: Failed to list packs: {e}")
            return []
    
    async def get_pack_metadata(self, pack_name: str) -> Optional[ExpansionPackMetadata]:
        """Get metadata for a specific expansion pack."""
        if not self.minio_client:
            return None
        
        try:
            metadata_key = f"pack_{pack_name}.json"
            response = self.minio_client.get_object(self.metadata_bucket, metadata_key)
            metadata_json = response.read().decode('utf-8')
            metadata_dict = json.loads(metadata_json)
            
            return ExpansionPackMetadata(**metadata_dict)
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return None
            print(f"[ERROR] Expansion Pack Storage: Failed to get metadata for {pack_name}: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Expansion Pack Storage: Failed to get metadata for {pack_name}: {e}")
            return None
    
    async def upload_pack(self, pack_path: Path, metadata: ExpansionPackMetadata) -> bool:
        """Upload an expansion pack to S3."""
        if not self.minio_client or not pack_path.exists():
            return False
        
        try:
            uploaded_files = []
            total_size = 0
            
            # Upload all files in the pack
            for file_path in pack_path.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(pack_path)
                    s3_key = f"{metadata.name}/{relative_path}"
                    
                    # Calculate file checksum
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        checksum = hashlib.sha256(content).hexdigest()
                    
                    # Upload file to S3
                    self.minio_client.put_object(
                        self.bucket_name,
                        s3_key,
                        file_path,
                        content_type=self._get_content_type(file_path),
                        metadata={
                            'pack_name': metadata.name,
                            'pack_version': metadata.version,
                            'checksum': checksum,
                            'uploaded_at': datetime.now(timezone.utc).isoformat()
                        }
                    )
                    
                    file_size = file_path.stat().st_size
                    uploaded_files.append(PackFile(
                        path=str(relative_path),
                        size_bytes=file_size,
                        content_type=self._get_content_type(file_path),
                        checksum=checksum,
                        last_modified=datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc).isoformat(),
                        category=self._get_file_category(relative_path)
                    ))
                    
                    total_size += file_size
            
            # Update metadata with file information
            metadata.file_count = len(uploaded_files)
            metadata.total_size_bytes = total_size
            metadata.last_updated = datetime.now(timezone.utc).isoformat()
            
            # Upload metadata
            await self._upload_pack_metadata(metadata)
            
            print(f"[INFO] Expansion Pack Storage: Uploaded pack {metadata.name} with {len(uploaded_files)} files ({total_size} bytes)")
            return True
            
        except Exception as e:
            print(f"[ERROR] Expansion Pack Storage: Failed to upload pack {metadata.name}: {e}")
            return False
    
    async def download_pack(self, pack_name: str, destination: Path) -> bool:
        """Download an expansion pack from S3."""
        if not self.minio_client:
            return False
        
        try:
            # Create destination directory
            destination.mkdir(parents=True, exist_ok=True)
            
            # List all objects for this pack
            objects = self.minio_client.list_objects(self.bucket_name, prefix=f"{pack_name}/", recursive=True)
            
            downloaded_files = 0
            for obj in objects:
                # Calculate local file path
                relative_path = obj.object_name[len(pack_name) + 1:]  # Remove pack_name/ prefix
                local_file_path = destination / relative_path
                
                # Create parent directories
                local_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Download file
                response = self.minio_client.get_object(self.bucket_name, obj.object_name)
                with open(local_file_path, 'wb') as f:
                    for chunk in response.stream(32*1024):
                        f.write(chunk)
                
                downloaded_files += 1
            
            # Update download count
            await self._increment_download_count(pack_name)
            
            print(f"[INFO] Expansion Pack Storage: Downloaded pack {pack_name} with {downloaded_files} files")
            return True
            
        except Exception as e:
            print(f"[ERROR] Expansion Pack Storage: Failed to download pack {pack_name}: {e}")
            return False
    
    async def get_pack_file(self, pack_name: str, file_path: str) -> Optional[bytes]:
        """Get a specific file from an expansion pack."""
        if not self.minio_client:
            return None
        
        try:
            s3_key = f"{pack_name}/{file_path}"
            response = self.minio_client.get_object(self.bucket_name, s3_key)
            return response.read()
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return None
            print(f"[ERROR] Expansion Pack Storage: Failed to get file {file_path} from pack {pack_name}: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Expansion Pack Storage: Failed to get file {file_path} from pack {pack_name}: {e}")
            return None
    
    async def delete_pack(self, pack_name: str) -> bool:
        """Delete an expansion pack from S3."""
        if not self.minio_client:
            return False
        
        try:
            # Delete all pack files
            objects = self.minio_client.list_objects(self.bucket_name, prefix=f"{pack_name}/", recursive=True)
            for obj in objects:
                self.minio_client.remove_object(self.bucket_name, obj.object_name)
            
            # Delete metadata
            metadata_key = f"pack_{pack_name}.json"
            self.minio_client.remove_object(self.metadata_bucket, metadata_key)
            
            print(f"[INFO] Expansion Pack Storage: Deleted pack {pack_name}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Expansion Pack Storage: Failed to delete pack {pack_name}: {e}")
            return False
    
    async def search_packs(self, query: str, category: Optional[str] = None) -> List[ExpansionPackMetadata]:
        """Search for expansion packs by query and optional category filter."""
        all_packs = await self.list_available_packs()
        
        filtered_packs = []
        query_lower = query.lower()
        
        for pack in all_packs:
            # Check if query matches name, description, or tags
            if (query_lower in pack.name.lower() or 
                query_lower in pack.description.lower() or 
                any(query_lower in tag.lower() for tag in pack.tags)):
                
                # Apply category filter if specified
                if category is None or pack.category.lower() == category.lower():
                    filtered_packs.append(pack)
        
        return filtered_packs
    
    def _get_content_type(self, file_path: Path) -> str:
        """Determine content type based on file extension."""
        suffix = file_path.suffix.lower()
        content_types = {
            '.yaml': 'application/x-yaml',
            '.yml': 'application/x-yaml',
            '.json': 'application/json',
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.py': 'text/x-python',
            '.js': 'text/javascript',
            '.ts': 'text/typescript',
            '.css': 'text/css',
            '.html': 'text/html'
        }
        return content_types.get(suffix, 'application/octet-stream')
    
    def _get_file_category(self, relative_path: Path) -> str:
        """Determine file category based on path."""
        path_str = str(relative_path).lower()
        if 'agents' in path_str:
            return 'agents'
        elif 'templates' in path_str:
            return 'templates'
        elif 'workflows' in path_str:
            return 'workflows'
        elif 'tasks' in path_str:
            return 'tasks'
        elif 'checklists' in path_str:
            return 'checklists'
        elif 'data' in path_str:
            return 'data'
        elif relative_path.name == 'config.yaml':
            return 'config'
        else:
            return 'other'
    
    async def _upload_pack_metadata(self, metadata: ExpansionPackMetadata) -> None:
        """Upload pack metadata to S3."""
        if not self.minio_client:
            return
        
        try:
            metadata_key = f"pack_{metadata.name}.json"
            metadata_json = json.dumps(asdict(metadata), indent=2)
            
            self.minio_client.put_object(
                self.metadata_bucket,
                metadata_key,
                io.BytesIO(metadata_json.encode('utf-8')),
                length=len(metadata_json),
                content_type='application/json'
            )
            
        except Exception as e:
            print(f"[ERROR] Expansion Pack Storage: Failed to upload metadata for {metadata.name}: {e}")
    
    async def _increment_download_count(self, pack_name: str) -> None:
        """Increment download count for a pack."""
        metadata = await self.get_pack_metadata(pack_name)
        if metadata:
            metadata.download_count += 1
            await self._upload_pack_metadata(metadata)


# Global instance
_expansion_pack_storage = None


def get_expansion_pack_storage() -> ExpansionPackStorage:
    """Get global expansion pack storage instance."""
    global _expansion_pack_storage
    if _expansion_pack_storage is None:
        _expansion_pack_storage = ExpansionPackStorage()
    return _expansion_pack_storage


# Utility functions for pack management

async def discover_local_packs(expansion_packs_dir: Path) -> List[ExpansionPackMetadata]:
    """Discover expansion packs from local directory structure."""
    discovered_packs = []
    
    if not expansion_packs_dir.exists():
        return discovered_packs
    
    for pack_dir in expansion_packs_dir.iterdir():
        if pack_dir.is_dir() and not pack_dir.name.startswith('.'):
            config_file = pack_dir / 'config.yaml'
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config_data = yaml.safe_load(f)
                    
                    # Extract metadata from config
                    metadata = ExpansionPackMetadata(
                        name=config_data.get('name', pack_dir.name),
                        version=config_data.get('version', '1.0.0'),
                        short_title=config_data.get('short-title', config_data.get('short_title', '')),
                        description=config_data.get('description', ''),
                        author=config_data.get('author', ''),
                        license=config_data.get('license', 'Unknown'),
                        price=config_data.get('price', 'Free'),
                        category=config_data.get('category', 'General'),
                        tags=config_data.get('tags', []),
                        commercial=config_data.get('commercial', False),
                        slash_prefix=config_data.get('slashPrefix', config_data.get('slash_prefix'))
                    )
                    
                    # Count files and calculate size
                    file_count = 0
                    total_size = 0
                    for file_path in pack_dir.rglob("*"):
                        if file_path.is_file():
                            file_count += 1
                            total_size += file_path.stat().st_size
                    
                    metadata.file_count = file_count
                    metadata.total_size_bytes = total_size
                    
                    discovered_packs.append(metadata)
                    
                except Exception as e:
                    print(f"[WARN] Expansion Pack Storage: Failed to process pack {pack_dir.name}: {e}")
    
    return discovered_packs


async def migrate_local_packs_to_s3(expansion_packs_dir: Path) -> Dict[str, Any]:
    """Migrate all local expansion packs to S3."""
    storage = get_expansion_pack_storage()
    local_packs = await discover_local_packs(expansion_packs_dir)
    
    migration_results = {
        "total_packs": len(local_packs),
        "successful_uploads": 0,
        "failed_uploads": 0,
        "errors": []
    }
    
    for pack_metadata in local_packs:
        pack_path = expansion_packs_dir / pack_metadata.name
        try:
            success = await storage.upload_pack(pack_path, pack_metadata)
            if success:
                migration_results["successful_uploads"] += 1
            else:
                migration_results["failed_uploads"] += 1
                migration_results["errors"].append(f"Failed to upload {pack_metadata.name}")
        except Exception as e:
            migration_results["failed_uploads"] += 1
            migration_results["errors"].append(f"Error uploading {pack_metadata.name}: {str(e)}")
    
    return migration_results


if __name__ == "__main__":
    # Example usage
    async def main():
        storage = get_expansion_pack_storage()
        
        # List available packs
        packs = await storage.list_available_packs()
        print(f"Available packs: {len(packs)}")
        for pack in packs:
            print(f"  - {pack.name} v{pack.version} ({pack.category})")
        
        # Example migration
        expansion_packs_dir = Path(__file__).parent.parent.parent / "vendor" / "bmad" / "expansion-packs"
        if expansion_packs_dir.exists():
            print("\nMigrating local packs to S3...")
            results = await migrate_local_packs_to_s3(expansion_packs_dir)
            print(f"Migration results: {results}")
    
    asyncio.run(main())