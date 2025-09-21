"""
BMAD Template Loader

This module provides S3-based template loading for BMAD templates and expansion packs,
replacing direct file system access with cloud storage access patterns.
"""

import asyncio
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from cflow_platform.core.expansion_pack_storage import ExpansionPackStorage, ExpansionPackMetadata
from cflow_platform.core.config.vault_config import get_vault_config


@dataclass
class BMADTemplate:
    """Represents a BMAD template loaded from S3."""
    name: str
    content: str
    template_type: str  # prd, architecture, story, etc.
    pack_name: Optional[str] = None  # Which expansion pack it came from
    version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    loaded_from: str = "s3"  # s3, local_fallback, cache
    checksum: Optional[str] = None


class BMADTemplateLoader:
    """S3-based template loader for BMAD templates and expansion packs."""
    
    def __init__(self):
        self.vault_config = get_vault_config()
        self.expansion_storage = ExpansionPackStorage()
        self.template_cache: Dict[str, BMADTemplate] = {}
        self.cache_ttl = 3600  # 1 hour cache TTL
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Core BMAD template mappings
        self.core_templates = {
            "prd": "prd-tmpl.yaml",
            "architecture": "architecture-tmpl.yaml", 
            "story": "story-tmpl.yaml",
            "fullstack-architecture": "fullstack-architecture-tmpl.yaml"
        }
        
        # Local fallback path for core templates
        self.local_fallback_root = Path(__file__).parent.parent.parent / "vendor" / "bmad"
    
    async def load_template(
        self, 
        template_name: str, 
        template_type: str = "core",
        pack_name: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[BMADTemplate]:
        """
        Load a BMAD template from S3 storage.
        
        Args:
            template_name: Name of the template (e.g., "prd", "architecture")
            template_type: Type of template ("core", "expansion")
            pack_name: Name of expansion pack (required for expansion templates)
            use_cache: Whether to use cached version if available
            
        Returns:
            BMADTemplate object or None if not found
        """
        cache_key = f"{template_type}:{pack_name or 'core'}:{template_name}"
        
        # Check cache first
        if use_cache and self._is_cache_valid(cache_key):
            return self.template_cache.get(cache_key)
        
        try:
            if template_type == "core":
                template = await self._load_core_template(template_name)
            elif template_type == "expansion" and pack_name:
                template = await self._load_expansion_template(template_name, pack_name)
            else:
                return None
            
            if template:
                # Cache the template
                if use_cache:
                    self.template_cache[cache_key] = template
                    self.cache_timestamps[cache_key] = datetime.now(timezone.utc)
                
                return template
            
        except Exception as e:
            print(f"[ERROR] BMAD Template Loader: Failed to load template {template_name}: {e}")
            return None
        
        return None
    
    async def _load_core_template(self, template_name: str) -> Optional[BMADTemplate]:
        """Load a core BMAD template."""
        try:
            # First try to load from S3 (if core templates are stored there)
            s3_template = await self._load_from_s3_core(template_name)
            if s3_template:
                return s3_template
            
            # Fallback to local vendor directory
            return await self._load_from_local_fallback(template_name)
            
        except Exception as e:
            print(f"[ERROR] BMAD Template Loader: Failed to load core template {template_name}: {e}")
            return None
    
    async def _load_from_s3_core(self, template_name: str) -> Optional[BMADTemplate]:
        """Load core template from S3 storage."""
        try:
            # Check if core templates are stored in a special core pack
            core_pack_name = "bmad-core"
            
            # Get the template filename
            template_filename = self.core_templates.get(template_name)
            if not template_filename:
                return None
            
            # Try to load from core expansion pack
            template_file = await self.expansion_storage.get_pack_file(
                pack_name=core_pack_name,
                file_path=f"templates/{template_filename}"
            )
            
            if template_file:
                content = template_file.get("content", "")
                if content:
                    return BMADTemplate(
                        name=template_name,
                        content=content,
                        template_type="core",
                        pack_name=core_pack_name,
                        version="latest",
                        metadata={"source": "s3_core"},
                        loaded_from="s3",
                        checksum=template_file.get("checksum")
                    )
            
        except Exception as e:
            print(f"[DEBUG] BMAD Template Loader: Core template not found in S3: {e}")
        
        return None
    
    async def _load_from_local_fallback(self, template_name: str) -> Optional[BMADTemplate]:
        """Load template from local vendor directory as fallback."""
        try:
            template_filename = self.core_templates.get(template_name)
            if not template_filename:
                return None
            
            template_path = self.local_fallback_root / "bmad-core" / "templates" / template_filename
            
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Calculate checksum
                import hashlib
                checksum = hashlib.sha256(content.encode()).hexdigest()
                
                return BMADTemplate(
                    name=template_name,
                    content=content,
                    template_type="core",
                    pack_name="local",
                    version="local",
                    metadata={"source": "local_fallback", "path": str(template_path)},
                    loaded_from="local_fallback",
                    checksum=checksum
                )
            
        except Exception as e:
            print(f"[ERROR] BMAD Template Loader: Failed to load local fallback {template_name}: {e}")
        
        return None
    
    async def _load_expansion_template(self, template_name: str, pack_name: str) -> Optional[BMADTemplate]:
        """Load template from expansion pack."""
        try:
            # Try different common template paths
            template_paths = [
                f"templates/{template_name}.yaml",
                f"templates/{template_name}.yml",
                f"{template_name}.yaml",
                f"{template_name}.yml"
            ]
            
            for template_path in template_paths:
                try:
                    template_file = await self.expansion_storage.get_pack_file(
                        pack_name=pack_name,
                        file_path=template_path
                    )
                    
                    if template_file:
                        content = template_file.get("content", "")
                        if content:
                            return BMADTemplate(
                                name=template_name,
                                content=content,
                                template_type="expansion",
                                pack_name=pack_name,
                                version=template_file.get("version", "latest"),
                                metadata=template_file.get("metadata", {}),
                                loaded_from="s3",
                                checksum=template_file.get("checksum")
                            )
                            
                except Exception:
                    continue
            
        except Exception as e:
            print(f"[ERROR] BMAD Template Loader: Failed to load expansion template {template_name} from {pack_name}: {e}")
        
        return None
    
    async def list_available_templates(
        self, 
        template_type: str = "all",
        pack_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all available templates."""
        templates = []
        
        try:
            if template_type in ["all", "core"]:
                # List core templates
                for template_name in self.core_templates.keys():
                    templates.append({
                        "name": template_name,
                        "type": "core",
                        "pack_name": "bmad-core",
                        "filename": self.core_templates[template_name],
                        "available": True
                    })
            
            if template_type in ["all", "expansion"]:
                # List expansion pack templates
                if pack_name:
                    # List templates from specific pack
                    pack_templates = await self._list_expansion_templates(pack_name)
                    templates.extend(pack_templates)
                else:
                    # List templates from all packs
                    available_packs = await self.expansion_storage.list_available_packs()
                    for pack in available_packs:
                        pack_templates = await self._list_expansion_templates(pack.name)
                        templates.extend(pack_templates)
            
        except Exception as e:
            print(f"[ERROR] BMAD Template Loader: Failed to list templates: {e}")
        
        return templates
    
    async def _list_expansion_templates(self, pack_name: str) -> List[Dict[str, Any]]:
        """List templates from a specific expansion pack."""
        templates = []
        
        try:
            # Get pack metadata to find template files
            pack_metadata = await self.expansion_storage.get_pack_metadata(pack_name)
            if not pack_metadata:
                return templates
            
            # Look for template files in the pack
            for file_info in pack_metadata.files:
                file_path = file_info.path
                if file_path.startswith("templates/") and file_path.endswith((".yaml", ".yml")):
                    template_name = Path(file_path).stem
                    templates.append({
                        "name": template_name,
                        "type": "expansion",
                        "pack_name": pack_name,
                        "filename": file_path,
                        "available": True,
                        "metadata": {
                            "size": file_info.size,
                            "last_modified": file_info.last_modified.isoformat(),
                            "checksum": file_info.checksum
                        }
                    })
            
        except Exception as e:
            print(f"[ERROR] BMAD Template Loader: Failed to list templates from pack {pack_name}: {e}")
        
        return templates
    
    async def search_templates(
        self, 
        query: str,
        template_type: str = "all",
        pack_category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for templates by query."""
        results = []
        
        try:
            # Get all available templates
            all_templates = await self.list_available_templates(template_type)
            
            # Filter by query
            query_lower = query.lower()
            for template in all_templates:
                if (query_lower in template["name"].lower() or 
                    query_lower in template.get("filename", "").lower()):
                    
                    # Filter by pack category if specified
                    if pack_category:
                        pack_metadata = await self.expansion_storage.get_pack_metadata(template["pack_name"])
                        if pack_metadata and pack_metadata.category != pack_category:
                            continue
                    
                    results.append(template)
            
        except Exception as e:
            print(f"[ERROR] BMAD Template Loader: Failed to search templates: {e}")
        
        return results
    
    async def validate_template(self, template: BMADTemplate) -> Dict[str, Any]:
        """Validate a template for correctness."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "checksum_valid": True
        }
        
        try:
            # Check if content is valid YAML
            import yaml
            try:
                yaml.safe_load(template.content)
            except yaml.YAMLError as e:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Invalid YAML: {str(e)}")
            
            # Validate checksum if provided
            if template.checksum:
                import hashlib
                calculated_checksum = hashlib.sha256(template.content.encode()).hexdigest()
                if calculated_checksum != template.checksum:
                    validation_result["checksum_valid"] = False
                    validation_result["warnings"].append("Checksum mismatch")
            
            # Check for required template fields
            try:
                template_data = yaml.safe_load(template.content)
                if isinstance(template_data, dict):
                    # Check for common required fields
                    required_fields = ["name", "description"]
                    for field in required_fields:
                        if field not in template_data:
                            validation_result["warnings"].append(f"Missing recommended field: {field}")
                else:
                    validation_result["warnings"].append("Template should be a YAML object")
                    
            except Exception:
                pass  # Already caught above
            
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached template is still valid."""
        if cache_key not in self.cache_timestamps:
            return False
        
        cache_time = self.cache_timestamps[cache_key]
        now = datetime.now(timezone.utc)
        
        return (now - cache_time).total_seconds() < self.cache_ttl
    
    def clear_cache(self) -> None:
        """Clear the template cache."""
        self.template_cache.clear()
        self.cache_timestamps.clear()
    
    async def preload_core_templates(self) -> Dict[str, bool]:
        """Preload all core templates for better performance."""
        results = {}
        
        for template_name in self.core_templates.keys():
            try:
                template = await self.load_template(template_name, "core")
                results[template_name] = template is not None
            except Exception as e:
                print(f"[WARN] BMAD Template Loader: Failed to preload {template_name}: {e}")
                results[template_name] = False
        
        return results


# Global instance
_bmad_template_loader = None


def get_bmad_template_loader() -> BMADTemplateLoader:
    """Get global BMAD template loader instance."""
    global _bmad_template_loader
    if _bmad_template_loader is None:
        _bmad_template_loader = BMADTemplateLoader()
    return _bmad_template_loader


# Convenience functions for common operations
async def load_core_template(template_name: str) -> Optional[BMADTemplate]:
    """Load a core BMAD template."""
    loader = get_bmad_template_loader()
    return await loader.load_template(template_name, "core")


async def load_expansion_template(template_name: str, pack_name: str) -> Optional[BMADTemplate]:
    """Load a template from an expansion pack."""
    loader = get_bmad_template_loader()
    return await loader.load_template(template_name, "expansion", pack_name)


async def list_all_templates() -> List[Dict[str, Any]]:
    """List all available templates."""
    loader = get_bmad_template_loader()
    return await loader.list_available_templates()


async def search_templates(query: str) -> List[Dict[str, Any]]:
    """Search for templates by query."""
    loader = get_bmad_template_loader()
    return await loader.search_templates(query)
