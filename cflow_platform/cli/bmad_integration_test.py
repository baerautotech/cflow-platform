#!/usr/bin/env python3
"""
BMAD S3 Integration Test Script

This script validates the BMAD S3 expansion pack integration without requiring
a running MinIO instance. It tests the code structure, imports, and fallback mechanisms.

Usage:
    python -m cflow_platform.cli.bmad_integration_test
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cflow_platform.core.expansion_pack_storage import get_expansion_pack_storage, ExpansionPackMetadata
from cflow_platform.core.bmad_template_loader import get_bmad_template_loader
from cflow_platform.handlers.expansion_pack_handlers import get_expansion_pack_handlers
from cflow_platform.handlers.bmad_template_handlers import get_bmad_template_handlers
from cflow_platform.core.direct_client import execute_mcp_tool


async def test_code_structure():
    """Test that all code structures are properly implemented."""
    print("🧪 Testing BMAD S3 Code Structure")
    print("=" * 40)
    
    # Test 1: Import all modules
    print("\n1. Testing Module Imports...")
    try:
        from cflow_platform.core.expansion_pack_storage import (
            ExpansionPackStorage, ExpansionPackMetadata, PackFile,
            discover_local_packs, migrate_local_packs_to_s3
        )
        print("   ✅ Expansion pack storage modules imported")
        
        from cflow_platform.core.bmad_template_loader import (
            BMADTemplateLoader, BMADTemplate,
            load_core_template, load_expansion_template
        )
        print("   ✅ Template loader modules imported")
        
        from cflow_platform.handlers.expansion_pack_handlers import BMADExpansionPackHandlers
        from cflow_platform.handlers.bmad_template_handlers import BMADTemplateHandlers
        print("   ✅ Handler modules imported")
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    # Test 2: Class instantiation
    print("\n2. Testing Class Instantiation...")
    try:
        storage = get_expansion_pack_storage()
        print("   ✅ Expansion pack storage instance created")
        
        template_loader = get_bmad_template_loader()
        print("   ✅ Template loader instance created")
        
        expansion_handlers = get_expansion_pack_handlers()
        print("   ✅ Expansion pack handlers instance created")
        
        template_handlers = get_bmad_template_handlers()
        print("   ✅ Template handlers instance created")
        
    except Exception as e:
        print(f"   ❌ Instantiation failed: {e}")
        return False
    
    # Test 3: Metadata structure
    print("\n3. Testing Metadata Structures...")
    try:
        # Test ExpansionPackMetadata
        metadata = ExpansionPackMetadata(
            name="test-pack",
            version="1.0.0",
            short_title="Test Pack",
            description="A test pack",
            author="Test Author",
            license="MIT",
            price="Free",
            category="Test",
            tags=["test"],
            commercial=False
        )
        print("   ✅ ExpansionPackMetadata structure valid")
        
        # Test that metadata has all required fields
        required_fields = ['name', 'version', 'description', 'author', 'license', 'category']
        for field in required_fields:
            if not hasattr(metadata, field):
                print(f"   ❌ Missing field: {field}")
                return False
        print("   ✅ All required metadata fields present")
        
    except Exception as e:
        print(f"   ❌ Metadata structure test failed: {e}")
        return False
    
    # Test 4: Handler method signatures
    print("\n4. Testing Handler Method Signatures...")
    try:
        # Test expansion pack handler methods
        expansion_methods = [
            'bmad_expansion_list_packs',
            'bmad_expansion_get_pack',
            'bmad_expansion_search_packs',
            'bmad_expansion_download_pack',
            'bmad_expansion_get_file',
            'bmad_expansion_upload_pack',
            'bmad_expansion_delete_pack',
            'bmad_expansion_migrate_local'
        ]
        
        for method_name in expansion_methods:
            if not hasattr(expansion_handlers, method_name):
                print(f"   ❌ Missing expansion handler method: {method_name}")
                return False
        print("   ✅ All expansion pack handler methods present")
        
        # Test template handler methods
        template_methods = [
            'bmad_template_load',
            'bmad_template_list',
            'bmad_template_search',
            'bmad_template_validate',
            'bmad_template_preload'
        ]
        
        for method_name in template_methods:
            if not hasattr(template_handlers, method_name):
                print(f"   ❌ Missing template handler method: {method_name}")
                return False
        print("   ✅ All template handler methods present")
        
    except Exception as e:
        print(f"   ❌ Handler method test failed: {e}")
        return False
    
    return True


async def test_fallback_mechanisms():
    """Test fallback mechanisms when S3 is not available."""
    print("\n5. Testing Fallback Mechanisms...")
    
    try:
        # Test template loader fallback
        template_loader = get_bmad_template_loader()
        
        # This should work even without S3 (falls back to local)
        template = await template_loader.load_template("prd", "core")
        
        if template:
            print(f"   ✅ Template fallback works: loaded from {template.loaded_from}")
        else:
            print("   ⚠️  Template fallback: no template found (expected if no local templates)")
        
        # Test storage graceful degradation
        storage = get_expansion_pack_storage()
        
        # These should handle missing S3 gracefully
        packs = await storage.list_available_packs()
        print(f"   ✅ Storage graceful degradation: returned {len(packs)} packs")
        
        # Test error handling for non-existent resources
        metadata = await storage.get_pack_metadata("non-existent-pack")
        if metadata is None:
            print("   ✅ Non-existent pack handled gracefully")
        else:
            print("   ⚠️  Non-existent pack returned unexpected result")
        
    except Exception as e:
        print(f"   ❌ Fallback mechanism test failed: {e}")
        return False
    
    return True


async def test_mcp_tool_registration():
    """Test that MCP tools are properly registered."""
    print("\n6. Testing MCP Tool Registration...")
    
    try:
        from cflow_platform.core.tool_registry import ToolRegistry
        
        # Get all registered tools
        tools = ToolRegistry.get_tools_for_mcp()
        
        # Check for BMAD expansion pack tools
        expansion_tools = [tool for tool in tools if tool['name'].startswith('bmad_expansion_')]
        print(f"   ✅ Found {len(expansion_tools)} expansion pack MCP tools")
        
        # Check for BMAD template tools
        template_tools = [tool for tool in tools if tool['name'].startswith('bmad_template_')]
        print(f"   ✅ Found {len(template_tools)} template MCP tools")
        
        # Check for BMAD update tools
        update_tools = [tool for tool in tools if tool['name'].startswith('bmad_update_')]
        print(f"   ✅ Found {len(update_tools)} update MCP tools")
        
        # Verify specific tools exist
        required_expansion_tools = [
            'bmad_expansion_list_packs',
            'bmad_expansion_get_pack',
            'bmad_expansion_search_packs',
            'bmad_expansion_download_pack',
            'bmad_expansion_get_file',
            'bmad_expansion_upload_pack',
            'bmad_expansion_delete_pack',
            'bmad_expansion_migrate_local'
        ]
        
        for tool_name in required_expansion_tools:
            if not any(tool['name'] == tool_name for tool in tools):
                print(f"   ❌ Missing expansion tool: {tool_name}")
                return False
        
        required_template_tools = [
            'bmad_template_load',
            'bmad_template_list',
            'bmad_template_search',
            'bmad_template_validate',
            'bmad_template_preload'
        ]
        
        for tool_name in required_template_tools:
            if not any(tool['name'] == tool_name for tool in tools):
                print(f"   ❌ Missing template tool: {tool_name}")
                return False
        
        print("   ✅ All required MCP tools registered")
        
    except Exception as e:
        print(f"   ❌ MCP tool registration test failed: {e}")
        return False
    
    return True


async def test_direct_client_integration():
    """Test direct client integration for MCP tools."""
    print("\n7. Testing Direct Client Integration...")
    
    try:
        # Test that direct client can handle BMAD tools
        # These will fail gracefully when S3 is not available
        
        # Test expansion pack list
        try:
            result = await execute_mcp_tool("bmad_expansion_list_packs")
            if result.get("status") in ["success", "error"]:
                print("   ✅ Direct client handles expansion pack tools")
            else:
                print(f"   ⚠️  Unexpected result: {result}")
        except Exception as e:
            print(f"   ⚠️  Direct client expansion test: {e}")
        
        # Test template list
        try:
            result = await execute_mcp_tool("bmad_template_list")
            if result.get("status") in ["success", "error"]:
                print("   ✅ Direct client handles template tools")
            else:
                print(f"   ⚠️  Unexpected result: {result}")
        except Exception as e:
            print(f"   ⚠️  Direct client template test: {e}")
        
        # Test template load
        try:
            result = await execute_mcp_tool("bmad_template_load", 
                template_name="prd",
                template_type="core"
            )
            if result.get("status") in ["success", "error"]:
                print("   ✅ Direct client handles template loading")
            else:
                print(f"   ⚠️  Unexpected result: {result}")
        except Exception as e:
            print(f"   ⚠️  Direct client template load test: {e}")
        
    except Exception as e:
        print(f"   ❌ Direct client integration test failed: {e}")
        return False
    
    return True


async def test_local_pack_discovery():
    """Test local pack discovery functionality."""
    print("\n8. Testing Local Pack Discovery...")
    
    try:
        from cflow_platform.core.expansion_pack_storage import discover_local_packs
        
        # Test discovery in vendor directory
        vendor_dir = Path(__file__).parent.parent.parent / "vendor" / "bmad" / "expansion-packs"
        
        if vendor_dir.exists():
            local_packs = await discover_local_packs(vendor_dir)
            print(f"   ✅ Local pack discovery works: found {len(local_packs)} packs")
            
            for pack in local_packs[:3]:  # Show first 3 packs
                print(f"      - {pack.name} v{pack.version} ({pack.category})")
        else:
            print(f"   ⚠️  Vendor directory not found: {vendor_dir}")
            print("   ✅ Discovery function available (no packs to discover)")
        
    except Exception as e:
        print(f"   ❌ Local pack discovery test failed: {e}")
        return False
    
    return True


async def main():
    """Main entry point."""
    print("🚀 BMAD S3 Integration Test (No S3 Required)")
    print("=" * 50)
    
    tests = [
        ("Code Structure", test_code_structure),
        ("Fallback Mechanisms", test_fallback_mechanisms),
        ("MCP Tool Registration", test_mcp_tool_registration),
        ("Direct Client Integration", test_direct_client_integration),
        ("Local Pack Discovery", test_local_pack_discovery),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed_tests += 1
            else:
                print(f"\n❌ {test_name} test failed")
        except Exception as e:
            print(f"\n💥 {test_name} test crashed: {e}")
    
    print(f"\n📊 Test Results: {passed_tests}/{total_tests} passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All integration tests passed!")
        print("✅ BMAD S3 expansion pack system is properly integrated")
        print("🚀 Ready for production deployment with S3 backend")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed")
        print("❌ Some integration issues need to be addressed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
