#!/usr/bin/env python3
"""
Test script for BMAD Workflow Testing Engine
Phase 4.1.1: Implement complete workflow testing

This script tests the workflow testing functionality to ensure it works correctly.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from cflow_platform.core.workflow_testing_engine import (
    workflow_testing_engine,
    WorkflowPhase,
    TestStatus
)
from cflow_platform.core.direct_client import execute_mcp_tool

async def test_workflow_testing_engine():
    """Test the workflow testing engine directly"""
    print("🧪 Testing Workflow Testing Engine...")
    
    try:
        # Test 1: Run complete workflow test
        print("\n1. Running complete workflow test...")
        execution = await workflow_testing_engine.run_complete_workflow_test()
        
        print(f"   ✅ Execution ID: {execution.execution_id}")
        print(f"   ✅ Status: {execution.status.value}")
        print(f"   ✅ Duration: {execution.duration_seconds:.2f} seconds")
        print(f"   ✅ Overall Score: {execution.overall_score:.2f}" if execution.overall_score is not None else "   ✅ Overall Score: N/A")
        print(f"   ✅ Steps Executed: {len(execution.step_results)}")
        
        # Test 2: Create custom test suite
        print("\n2. Creating custom test suite...")
        suite = workflow_testing_engine.suite_builder.create_custom_suite(
            name="Test Suite",
            description="Custom test suite for validation",
            phases=[WorkflowPhase.PRD_CREATION, WorkflowPhase.ARCHITECTURE_DESIGN],
            custom_steps=[]
        )
        
        print(f"   ✅ Suite ID: {suite.suite_id}")
        print(f"   ✅ Suite Name: {suite.suite_name}")
        print(f"   ✅ Phases: {[phase.value for phase in suite.workflow_phases]}")
        
        # Test 3: Get test statistics
        print("\n3. Getting test statistics...")
        stats = workflow_testing_engine.get_test_statistics()
        
        print(f"   ✅ Total Tests: {stats['total_tests']}")
        print(f"   ✅ Pass Rate: {stats['pass_rate']:.2f}%")
        print(f"   ✅ Average Score: {stats['average_score']:.2f}")
        
        # Test 4: Get test history
        print("\n4. Getting test history...")
        history = workflow_testing_engine.get_test_history(limit=10)
        
        print(f"   ✅ History Entries: {len(history)}")
        if history:
            latest = history[-1]
            print(f"   ✅ Latest Execution: {latest.execution_id}")
            print(f"   ✅ Latest Status: {latest.status.value}")
        
        print("\n✅ Workflow Testing Engine tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Workflow Testing Engine test failed: {e}")
        return False

async def test_mcp_tools():
    """Test the MCP tools for workflow testing"""
    print("\n🔧 Testing MCP Tools...")
    
    try:
        # Test 1: Run complete workflow test via MCP
        print("\n1. Testing bmad_workflow_test_run_complete...")
        result = await execute_mcp_tool("bmad_workflow_test_run_complete")
        
        if result.get("success"):
            print(f"   ✅ Execution ID: {result.get('execution_id')}")
            print(f"   ✅ Status: {result.get('status')}")
            print(f"   ✅ Duration: {result.get('duration_seconds')}")
            print(f"   ✅ Steps: {len(result.get('step_results', []))}")
        else:
            print(f"   ❌ Error: {result.get('error')}")
            return False
        
        # Test 2: List test suites
        print("\n2. Testing bmad_workflow_test_list_suites...")
        result = await execute_mcp_tool("bmad_workflow_test_list_suites")
        
        if result.get("success"):
            suites = result.get("suites", [])
            print(f"   ✅ Found {len(suites)} test suites")
            for suite in suites[:3]:  # Show first 3
                print(f"   ✅ Suite: {suite['suite_name']} ({suite['suite_id'][:8]}...)")
        else:
            print(f"   ❌ Error: {result.get('error')}")
            return False
        
        # Test 3: Get test statistics
        print("\n3. Testing bmad_workflow_test_get_statistics...")
        result = await execute_mcp_tool("bmad_workflow_test_get_statistics")
        
        if result.get("success"):
            stats = result.get("statistics", {})
            print(f"   ✅ Total Tests: {stats.get('total_tests', 0)}")
            print(f"   ✅ Pass Rate: {stats.get('pass_rate', 0):.2f}%")
            print(f"   ✅ Average Score: {stats.get('average_score', 0):.2f}")
        else:
            print(f"   ❌ Error: {result.get('error')}")
            return False
        
        # Test 4: Get test history
        print("\n4. Testing bmad_workflow_test_get_history...")
        result = await execute_mcp_tool("bmad_workflow_test_get_history", limit=5)
        
        if result.get("success"):
            executions = result.get("executions", [])
            print(f"   ✅ Found {len(executions)} executions")
            if executions:
                latest = executions[0]
                print(f"   ✅ Latest: {latest['execution_id'][:8]}... ({latest['status']})")
        else:
            print(f"   ❌ Error: {result.get('error')}")
            return False
        
        # Test 5: Create custom test suite
        print("\n5. Testing bmad_workflow_test_create_suite...")
        result = await execute_mcp_tool("bmad_workflow_test_create_suite", 
                                       name="MCP Test Suite",
                                       description="Test suite created via MCP",
                                       phases=["PRD_CREATION", "ARCHITECTURE_DESIGN"])
        
        if result.get("success"):
            suite_id = result.get("suite_id")
            print(f"   ✅ Created suite: {suite_id}")
            
            # Test 6: Run the custom suite
            print("\n6. Testing bmad_workflow_test_run_suite...")
            result = await execute_mcp_tool("bmad_workflow_test_run_suite", suite_id=suite_id)
            
            if result.get("success"):
                print(f"   ✅ Suite execution: {result.get('status')}")
                print(f"   ✅ Duration: {result.get('duration_seconds')}")
            else:
                print(f"   ❌ Suite execution error: {result.get('error')}")
                return False
        else:
            print(f"   ❌ Error: {result.get('error')}")
            return False
        
        print("\n✅ MCP Tools tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ MCP Tools test failed: {e}")
        return False

async def test_validation():
    """Test the validation functionality"""
    print("\n🔍 Testing Validation...")
    
    try:
        # Test step validation
        print("\n1. Testing step validation...")
        result = await execute_mcp_tool("bmad_workflow_test_validate_step",
                                       step_id="test_step",
                                       output={
                                           "prd_content": {
                                               "problem_definition": "Test problem",
                                               "solution_overview": "Test solution",
                                               "user_stories": ["Story 1", "Story 2"],
                                               "acceptance_criteria": ["Criteria 1", "Criteria 2"],
                                               "word_count": 600
                                           }
                                       },
                                       validation_criteria={
                                           "required_sections": ["problem_definition", "solution_overview", "user_stories", "acceptance_criteria"],
                                           "min_word_count": 500
                                       })
        
        if result.get("success"):
            validation_results = result.get("validation_results", {})
            print(f"   ✅ Validation Valid: {validation_results.get('valid', False)}")
            print(f"   ✅ Validation Score: {validation_results.get('score', 0):.2f}")
            print(f"   ✅ Issues: {len(validation_results.get('issues', []))}")
        else:
            print(f"   ❌ Error: {result.get('error')}")
            return False
        
        print("\n✅ Validation tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Validation test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 BMAD Workflow Testing - Phase 4.1.1 Test Suite")
    print("=" * 60)
    
    # Run all tests
    tests = [
        ("Workflow Testing Engine", test_workflow_testing_engine),
        ("MCP Tools", test_mcp_tools),
        ("Validation", test_validation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Phase 4.1.1 implementation is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total-passed} test(s) failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
