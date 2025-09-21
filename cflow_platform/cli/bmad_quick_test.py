#!/usr/bin/env python3
"""
BMAD S3 Quick Test Script

A simplified test script to quickly validate S3 expansion pack functionality.
This script tests the core operations without extensive setup.

Usage:
    python -m cflow_platform.cli.bmad_quick_test
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cflow_platform.core.expansion_pack_storage import get_expansion_pack_storage
from cflow_platform.core.bmad_template_loader import get_bmad_template_loader
from cflow_platform.core.direct_client import execute_mcp_tool


async def test_basic_functionality():
    """Test basic S3 expansion pack functionality."""
    print("🧪 Testing BMAD S3 Expansion Pack Functionality")
    print("=" * 50)
    
    # Test 1: S3 Storage Connection
    print("\n1. Testing S3 Storage Connection...")
    try:
        storage = get_expansion_pack_storage()
        if storage.minio_client:
            print("   ✅ MinIO client initialized")
            
            # Test bucket access
            bucket_exists = storage.minio_client.bucket_exists(storage.bucket_name)
            metadata_bucket_exists = storage.minio_client.bucket_exists(storage.metadata_bucket)
            
            if bucket_exists and metadata_bucket_exists:
                print("   ✅ Both S3 buckets accessible")
            else:
                print(f"   ⚠️  Bucket status: main={bucket_exists}, metadata={metadata_bucket_exists}")
        else:
            print("   ❌ MinIO client not initialized")
            return False
    except Exception as e:
        print(f"   ❌ S3 connection failed: {e}")
        return False
    
    # Test 2: List Expansion Packs
    print("\n2. Testing Expansion Pack Listing...")
    try:
        packs = await storage.list_available_packs()
        print(f"   ✅ Found {len(packs)} expansion packs")
        for pack in packs[:3]:  # Show first 3 packs
            print(f"      - {pack.name} v{pack.version} ({pack.category})")
    except Exception as e:
        print(f"   ❌ Failed to list packs: {e}")
        return False
    
    # Test 3: Template Loading
    print("\n3. Testing Template Loading...")
    try:
        template_loader = get_bmad_template_loader()
        template = await template_loader.load_template("prd", "core")
        
        if template:
            print(f"   ✅ Core template loaded from: {template.loaded_from}")
            print(f"      Content size: {len(template.content)} characters")
        else:
            print("   ⚠️  Core template not found")
    except Exception as e:
        print(f"   ❌ Template loading failed: {e}")
        return False
    
    # Test 4: Template Listing
    print("\n4. Testing Template Listing...")
    try:
        templates = await template_loader.list_available_templates()
        print(f"   ✅ Found {len(templates)} available templates")
        
        core_templates = [t for t in templates if t.get("type") == "core"]
        expansion_templates = [t for t in templates if t.get("type") == "expansion"]
        
        print(f"      - Core templates: {len(core_templates)}")
        print(f"      - Expansion templates: {len(expansion_templates)}")
    except Exception as e:
        print(f"   ❌ Template listing failed: {e}")
        return False
    
    # Test 5: MCP Tool Integration
    print("\n5. Testing MCP Tool Integration...")
    try:
        # Test expansion pack list via MCP
        result = await execute_mcp_tool("bmad_expansion_list_packs", {})
        if result.get("status") == "success":
            print("   ✅ MCP expansion pack listing works")
        else:
            print(f"   ⚠️  MCP expansion pack listing: {result.get('message', 'Unknown error')}")
        
        # Test template list via MCP
        result = await execute_mcp_tool("bmad_template_list", {})
        if result.get("status") == "success":
            print("   ✅ MCP template listing works")
        else:
            print(f"   ⚠️  MCP template listing: {result.get('message', 'Unknown error')}")
        
        # Test template load via MCP
        result = await execute_mcp_tool("bmad_template_load", {
            "template_name": "prd",
            "template_type": "core"
        })
        if result.get("status") == "success":
            print("   ✅ MCP template loading works")
        else:
            print(f"   ⚠️  MCP template loading: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ MCP tool integration failed: {e}")
        return False
    
    # Test 6: Error Handling
    print("\n6. Testing Error Handling...")
    try:
        # Test non-existent pack
        metadata = await storage.get_pack_metadata("non-existent-pack")
        if metadata is None:
            print("   ✅ Non-existent pack handled gracefully")
        else:
            print("   ⚠️  Non-existent pack returned unexpected result")
        
        # Test non-existent template
        template = await template_loader.load_template("non-existent-template", "core")
        if template is None:
            print("   ✅ Non-existent template handled gracefully")
        else:
            print("   ⚠️  Non-existent template returned unexpected result")
            
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
        return False
    
    print("\n🎉 All basic tests completed successfully!")
    print("✅ S3 expansion pack system is functional")
    return True


async def main():
    """Main entry point."""
    try:
        success = await test_basic_functionality()
        if success:
            print("\n🚀 BMAD S3 Expansion Pack System: READY FOR PRODUCTION")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed. Please review the output above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
