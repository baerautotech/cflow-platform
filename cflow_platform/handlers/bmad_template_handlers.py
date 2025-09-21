"""
BMAD Template Management Handlers

Handlers for BMAD template management tools including S3-based template loading,
searching, and validation.
"""

import asyncio
from typing import Any, Dict, List, Optional

from cflow_platform.core.bmad_template_loader import get_bmad_template_loader


class BMADTemplateHandlers:
    """Handlers for BMAD template management tools."""
    
    def __init__(self):
        self.template_loader = get_bmad_template_loader()
    
    async def bmad_template_load(
        self, 
        template_name: str, 
        template_type: str = "core",
        pack_name: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Load a BMAD template from S3 storage."""
        try:
            template = await self.template_loader.load_template(
                template_name=template_name,
                template_type=template_type,
                pack_name=pack_name,
                use_cache=use_cache
            )
            
            if not template:
                return {
                    "status": "error",
                    "message": f"Template '{template_name}' not found",
                    "template_name": template_name,
                    "template_type": template_type,
                    "pack_name": pack_name
                }
            
            # Validate template
            validation_result = await self.template_loader.validate_template(template)
            
            return {
                "status": "success",
                "message": f"Template '{template_name}' loaded successfully",
                "template": {
                    "name": template.name,
                    "template_type": template.template_type,
                    "pack_name": template.pack_name,
                    "version": template.version,
                    "loaded_from": template.loaded_from,
                    "checksum": template.checksum,
                    "metadata": template.metadata,
                    "content_preview": template.content[:500] + "..." if len(template.content) > 500 else template.content
                },
                "validation": validation_result,
                "cache_used": use_cache
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to load template '{template_name}': {str(e)}"
            }
    
    async def bmad_template_list(
        self, 
        template_type: str = "all",
        pack_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all available BMAD templates."""
        try:
            templates = await self.template_loader.list_available_templates(
                template_type=template_type,
                pack_name=pack_name
            )
            
            # Categorize templates
            categorized = {
                "core": [t for t in templates if t["type"] == "core"],
                "expansion": [t for t in templates if t["type"] == "expansion"],
                "by_pack": {}
            }
            
            # Group by pack
            for template in templates:
                pack = template["pack_name"]
                if pack not in categorized["by_pack"]:
                    categorized["by_pack"][pack] = []
                categorized["by_pack"][pack].append(template)
            
            return {
                "status": "success",
                "message": f"Found {len(templates)} available templates",
                "total_templates": len(templates),
                "template_type_filter": template_type,
                "pack_name_filter": pack_name,
                "templates": templates,
                "categorized": categorized
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to list templates: {str(e)}"
            }
    
    async def bmad_template_search(
        self, 
        query: str,
        template_type: str = "all",
        pack_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for BMAD templates by query."""
        try:
            results = await self.template_loader.search_templates(
                query=query,
                template_type=template_type,
                pack_category=pack_category
            )
            
            # Group results by relevance
            exact_matches = [t for t in results if query.lower() in t["name"].lower()]
            partial_matches = [t for t in results if t not in exact_matches]
            
            return {
                "status": "success",
                "message": f"Found {len(results)} templates matching '{query}'",
                "query": query,
                "template_type_filter": template_type,
                "pack_category_filter": pack_category,
                "total_results": len(results),
                "exact_matches": len(exact_matches),
                "partial_matches": len(partial_matches),
                "results": results,
                "grouped_results": {
                    "exact_matches": exact_matches,
                    "partial_matches": partial_matches
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to search templates: {str(e)}"
            }
    
    async def bmad_template_validate(
        self, 
        template_name: str,
        template_type: str = "core",
        pack_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate a BMAD template for correctness."""
        try:
            # Load the template first
            template = await self.template_loader.load_template(
                template_name=template_name,
                template_type=template_type,
                pack_name=pack_name,
                use_cache=True
            )
            
            if not template:
                return {
                    "status": "error",
                    "message": f"Template '{template_name}' not found for validation",
                    "template_name": template_name,
                    "template_type": template_type,
                    "pack_name": pack_name
                }
            
            # Validate the template
            validation_result = await self.template_loader.validate_template(template)
            
            return {
                "status": "success",
                "message": f"Template '{template_name}' validation completed",
                "template_name": template_name,
                "template_type": template_type,
                "pack_name": pack_name,
                "validation_result": validation_result,
                "template_info": {
                    "name": template.name,
                    "loaded_from": template.loaded_from,
                    "checksum": template.checksum,
                    "version": template.version,
                    "content_size": len(template.content)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to validate template '{template_name}': {str(e)}"
            }
    
    async def bmad_template_preload(self) -> Dict[str, Any]:
        """Preload core BMAD templates for better performance."""
        try:
            results = await self.template_loader.preload_core_templates()
            
            successful_loads = sum(1 for success in results.values() if success)
            failed_loads = len(results) - successful_loads
            
            return {
                "status": "success",
                "message": f"Preloaded {successful_loads}/{len(results)} core templates",
                "total_templates": len(results),
                "successful_loads": successful_loads,
                "failed_loads": failed_loads,
                "preload_results": results,
                "cache_enabled": True,
                "performance_improvement": "Templates are now cached for faster access"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to preload core templates: {str(e)}"
            }


# Global instance
_bmad_template_handlers = None


def get_bmad_template_handlers() -> BMADTemplateHandlers:
    """Get global BMAD template handlers instance."""
    global _bmad_template_handlers
    if _bmad_template_handlers is None:
        _bmad_template_handlers = BMADTemplateHandlers()
    return _bmad_template_handlers
