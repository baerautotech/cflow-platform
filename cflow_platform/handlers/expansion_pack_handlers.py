"""
BMAD Expansion Pack Handlers

Handlers for BMAD expansion pack management tools including S3 storage operations.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from cflow_platform.core.expansion_pack_storage import (
    get_expansion_pack_storage, 
    discover_local_packs, 
    migrate_local_packs_to_s3
)


class BMADExpansionPackHandlers:
    """Handlers for BMAD expansion pack management tools."""
    
    def __init__(self):
        self.storage = get_expansion_pack_storage()
    
    async def bmad_expansion_list_packs(self) -> Dict[str, Any]:
        """List all available expansion packs."""
        try:
            packs = await self.storage.list_available_packs()
            
            pack_list = []
            for pack in packs:
                pack_list.append({
                    "name": pack.name,
                    "version": pack.version,
                    "short_title": pack.short_title,
                    "description": pack.description,
                    "author": pack.author,
                    "license": pack.license,
                    "price": pack.price,
                    "category": pack.category,
                    "tags": pack.tags,
                    "commercial": pack.commercial,
                    "file_count": pack.file_count,
                    "total_size_bytes": pack.total_size_bytes,
                    "download_count": pack.download_count,
                    "last_updated": pack.last_updated
                })
            
            return {
                "status": "success",
                "message": f"Found {len(pack_list)} expansion packs",
                "packs": pack_list,
                "total_packs": len(pack_list)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to list expansion packs: {str(e)}"
            }
    
    async def bmad_expansion_get_pack(self, pack_name: str) -> Dict[str, Any]:
        """Get metadata for a specific expansion pack."""
        try:
            metadata = await self.storage.get_pack_metadata(pack_name)
            
            if not metadata:
                return {
                    "status": "error",
                    "message": f"Expansion pack '{pack_name}' not found"
                }
            
            return {
                "status": "success",
                "message": f"Retrieved metadata for expansion pack '{pack_name}'",
                "pack": {
                    "name": metadata.name,
                    "version": metadata.version,
                    "short_title": metadata.short_title,
                    "description": metadata.description,
                    "author": metadata.author,
                    "license": metadata.license,
                    "price": metadata.price,
                    "category": metadata.category,
                    "tags": metadata.tags,
                    "commercial": metadata.commercial,
                    "slash_prefix": metadata.slash_prefix,
                    "file_count": metadata.file_count,
                    "total_size_bytes": metadata.total_size_bytes,
                    "download_count": metadata.download_count,
                    "last_updated": metadata.last_updated,
                    "created_at": metadata.created_at
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get expansion pack metadata: {str(e)}"
            }
    
    async def bmad_expansion_search_packs(self, query: str, category: Optional[str] = None) -> Dict[str, Any]:
        """Search expansion packs by query and optional category filter."""
        try:
            packs = await self.storage.search_packs(query, category)
            
            pack_list = []
            for pack in packs:
                pack_list.append({
                    "name": pack.name,
                    "version": pack.version,
                    "short_title": pack.short_title,
                    "description": pack.description,
                    "author": pack.author,
                    "license": pack.license,
                    "price": pack.price,
                    "category": pack.category,
                    "tags": pack.tags,
                    "commercial": pack.commercial,
                    "file_count": pack.file_count,
                    "total_size_bytes": pack.total_size_bytes,
                    "download_count": pack.download_count
                })
            
            return {
                "status": "success",
                "message": f"Found {len(pack_list)} expansion packs matching query '{query}'" + 
                          (f" in category '{category}'" if category else ""),
                "query": query,
                "category": category,
                "packs": pack_list,
                "total_matches": len(pack_list)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to search expansion packs: {str(e)}"
            }
    
    async def bmad_expansion_download_pack(self, pack_name: str, destination: Optional[str] = None) -> Dict[str, Any]:
        """Download an expansion pack from S3."""
        try:
            # Set default destination if not provided
            if not destination:
                destination = f"./downloads/{pack_name}"
            
            destination_path = Path(destination)
            
            success = await self.storage.download_pack(pack_name, destination_path)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Successfully downloaded expansion pack '{pack_name}'",
                    "pack_name": pack_name,
                    "destination": str(destination_path.absolute()),
                    "path": str(destination_path.absolute())
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to download expansion pack '{pack_name}'"
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to download expansion pack: {str(e)}"
            }
    
    async def bmad_expansion_get_file(self, pack_name: str, file_path: str) -> Dict[str, Any]:
        """Get a specific file from an expansion pack."""
        try:
            file_content = await self.storage.get_pack_file(pack_name, file_path)
            
            if file_content is None:
                return {
                    "status": "error",
                    "message": f"File '{file_path}' not found in expansion pack '{pack_name}'"
                }
            
            # Try to decode as text for text files
            try:
                content_str = file_content.decode('utf-8')
                return {
                    "status": "success",
                    "message": f"Retrieved file '{file_path}' from expansion pack '{pack_name}'",
                    "pack_name": pack_name,
                    "file_path": file_path,
                    "content": content_str,
                    "size_bytes": len(file_content),
                    "content_type": "text"
                }
            except UnicodeDecodeError:
                # Binary file - return base64 encoded content
                import base64
                content_b64 = base64.b64encode(file_content).decode('ascii')
                return {
                    "status": "success",
                    "message": f"Retrieved binary file '{file_path}' from expansion pack '{pack_name}'",
                    "pack_name": pack_name,
                    "file_path": file_path,
                    "content": content_b64,
                    "size_bytes": len(file_content),
                    "content_type": "binary",
                    "encoding": "base64"
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get file from expansion pack: {str(e)}"
            }
    
    async def bmad_expansion_upload_pack(self, pack_path: str) -> Dict[str, Any]:
        """Upload a local expansion pack to S3."""
        try:
            pack_path_obj = Path(pack_path)
            
            if not pack_path_obj.exists():
                return {
                    "status": "error",
                    "message": f"Pack path '{pack_path}' does not exist"
                }
            
            # Discover local pack metadata
            local_packs = await discover_local_packs(pack_path_obj.parent)
            pack_metadata = None
            
            for pack in local_packs:
                if pack.name == pack_path_obj.name:
                    pack_metadata = pack
                    break
            
            if not pack_metadata:
                return {
                    "status": "error",
                    "message": f"Could not find metadata for pack '{pack_path_obj.name}'"
                }
            
            success = await self.storage.upload_pack(pack_path_obj, pack_metadata)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Successfully uploaded expansion pack '{pack_metadata.name}'",
                    "pack_name": pack_metadata.name,
                    "version": pack_metadata.version,
                    "file_count": pack_metadata.file_count,
                    "total_size_bytes": pack_metadata.total_size_bytes
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to upload expansion pack '{pack_metadata.name}'"
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to upload expansion pack: {str(e)}"
            }
    
    async def bmad_expansion_delete_pack(self, pack_name: str) -> Dict[str, Any]:
        """Delete an expansion pack from S3."""
        try:
            success = await self.storage.delete_pack(pack_name)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Successfully deleted expansion pack '{pack_name}'",
                    "pack_name": pack_name
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to delete expansion pack '{pack_name}'"
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to delete expansion pack: {str(e)}"
            }
    
    async def bmad_expansion_migrate_local(self, expansion_packs_dir: Optional[str] = None) -> Dict[str, Any]:
        """Migrate all local expansion packs to S3."""
        try:
            # Set default directory if not provided
            if not expansion_packs_dir:
                expansion_packs_dir = "./vendor/bmad/expansion-packs"
            
            expansion_packs_path = Path(expansion_packs_dir)
            
            if not expansion_packs_path.exists():
                return {
                    "status": "error",
                    "message": f"Expansion packs directory '{expansion_packs_dir}' does not exist"
                }
            
            results = await migrate_local_packs_to_s3(expansion_packs_path)
            
            return {
                "status": "success" if results["failed_uploads"] == 0 else "partial_success",
                "message": f"Migration completed: {results['successful_uploads']} successful, {results['failed_uploads']} failed",
                "results": results,
                "total_packs": results["total_packs"],
                "successful_uploads": results["successful_uploads"],
                "failed_uploads": results["failed_uploads"],
                "errors": results["errors"]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to migrate local expansion packs: {str(e)}"
            }


# Global instance
_expansion_pack_handlers = BMADExpansionPackHandlers()


def get_expansion_pack_handlers() -> BMADExpansionPackHandlers:
    """Get global expansion pack handlers instance."""
    return _expansion_pack_handlers
