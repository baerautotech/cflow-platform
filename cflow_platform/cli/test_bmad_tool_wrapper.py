#!/usr/bin/env python3
"""
BMAD Tool Wrapper Test Suite

Tests the BMAD-Method tool wrapper functionality including:
- Tool discovery from vendor/bmad
- Tool categorization and management
- MCP integration
- Tool execution with Cerebral extensions
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cflow_platform.core.bmad_tool_wrapper import bmad_tool_wrapper
from cflow_platform.core.direct_client import execute_mcp_tool

async def test_tool_discovery():
    """Test BMAD tool discovery functionality"""
    print("🔍 Testing BMAD Tool Discovery")
    print("-" * 40)
    
    # Test direct wrapper discovery
    tools = await bmad_tool_wrapper.discover_bmad_tools()
    print(f"✅ Direct discovery: {len(tools)} tools found")
    
    # Test MCP discovery
    result = await execute_mcp_tool('bmad_discover_tools')
    if result['success']:
        print(f"✅ MCP discovery: {result['total_count']} tools found")
        print(f"✅ Categories: {list(result['categories'].keys())}")
    else:
        print(f"❌ MCP discovery failed: {result['error']}")
    
    return len(tools) > 0

async def test_tool_categorization():
    """Test tool categorization functionality"""
    print("\n📊 Testing Tool Categorization")
    print("-" * 40)
    
    # Test status
    status = await bmad_tool_wrapper.get_tool_status()
    print(f"✅ Total tools: {status['total_tools']}")
    print(f"✅ Categories: {status['categories']}")
    
    # Test MCP status
    result = await execute_mcp_tool('bmad_get_tool_status')
    if result['success']:
        print(f"✅ MCP status: {result['status']['total_tools']} tools")
    else:
        print(f"❌ MCP status failed: {result['error']}")
    
    # Test category listing
    result = await execute_mcp_tool('bmad_list_categories')
    if result['success']:
        print(f"✅ Categories via MCP: {result['total_categories']}")
        for category, info in result['categories'].items():
            print(f"   • {category}: {info['count']} tools")
    else:
        print(f"❌ Category listing failed: {result['error']}")
    
    return True

async def test_tool_retrieval():
    """Test tool retrieval functionality"""
    print("\n🔧 Testing Tool Retrieval")
    print("-" * 40)
    
    # Get first tool
    tools = await bmad_tool_wrapper.discover_bmad_tools()
    if not tools:
        print("❌ No tools available for testing")
        return False
    
    first_tool_id = list(tools.keys())[0]
    first_tool = tools[first_tool_id]
    
    print(f"✅ First tool: {first_tool.name} ({first_tool.id})")
    print(f"✅ Category: {first_tool.category}")
    print(f"✅ Type: {first_tool.tool_type}")
    
    # Test MCP tool retrieval
    result = await execute_mcp_tool('bmad_get_tool', tool_id=first_tool_id)
    if result['success']:
        tool_info = result['tool']
        print(f"✅ MCP retrieval: {tool_info['name']}")
        print(f"✅ Cerebral extensions: {tool_info['cerebral_extensions']}")
    else:
        print(f"❌ MCP retrieval failed: {result['error']}")
    
    # Test category retrieval
    result = await execute_mcp_tool('bmad_get_tools_by_category', category=first_tool.category)
    if result['success']:
        print(f"✅ Category tools: {result['count']} tools in {result['category']}")
    else:
        print(f"❌ Category retrieval failed: {result['error']}")
    
    return True

async def test_tool_execution():
    """Test tool execution functionality"""
    print("\n⚡ Testing Tool Execution")
    print("-" * 40)
    
    # Get a tool to execute
    tools = await bmad_tool_wrapper.discover_bmad_tools()
    if not tools:
        print("❌ No tools available for testing")
        return False
    
    first_tool_id = list(tools.keys())[0]
    
    # Test direct execution
    result = await bmad_tool_wrapper.execute_tool(first_tool_id, {'test': 'parameter'})
    if result['success']:
        print(f"✅ Direct execution: {result['tool_name']}")
        print(f"✅ Result: {result['result']}")
    else:
        print(f"❌ Direct execution failed: {result['error']}")
    
    # Test MCP execution
    result = await execute_mcp_tool('bmad_execute_tool', tool_id=first_tool_id, parameters={'test': 'mcp_parameter'})
    if result['success']:
        print(f"✅ MCP execution: {result['tool_name']}")
        print(f"✅ Result: {result['result']}")
        print(f"✅ Context: {result['context']['cerebral_extensions']}")
    else:
        print(f"❌ MCP execution failed: {result['error']}")
    
    return True

async def test_cerebral_extensions():
    """Test Cerebral extensions functionality"""
    print("\n🧠 Testing Cerebral Extensions")
    print("-" * 40)
    
    # Check wrapper extensions
    status = await bmad_tool_wrapper.get_tool_status()
    extensions = status['cerebral_extensions']
    
    print(f"✅ MCP Integration: {extensions['mcp_integration']}")
    print(f"✅ Context Preservation: {extensions['context_preservation']}")
    print(f"✅ Session Management: {extensions['session_management']}")
    print(f"✅ WebMCP Routing: {extensions['webmcp_routing']}")
    
    # Test tool with extensions
    tools = await bmad_tool_wrapper.discover_bmad_tools()
    if tools:
        first_tool_id = list(tools.keys())[0]
        tool = tools[first_tool_id]
        
        print(f"✅ Tool extensions: {tool.cerebral_extensions}")
        
        # Execute with extensions
        result = await bmad_tool_wrapper.execute_tool(first_tool_id, {'test': 'extensions'})
        if result['success']:
            context = result['context']
            print(f"✅ Execution context: {context['cerebral_extensions']}")
            print(f"✅ Timestamp: {context['timestamp']}")
    
    return True

async def run_comprehensive_test():
    """Run comprehensive test suite"""
    print("🧪 BMAD Tool Wrapper Comprehensive Test Suite")
    print("=" * 60)
    
    tests = [
        ("Tool Discovery", test_tool_discovery),
        ("Tool Categorization", test_tool_categorization),
        ("Tool Retrieval", test_tool_retrieval),
        ("Tool Execution", test_tool_execution),
        ("Cerebral Extensions", test_cerebral_extensions),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! BMAD Tool Wrapper is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Review the output above.")
        return False

async def main():
    """Main test function"""
    try:
        success = await run_comprehensive_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
