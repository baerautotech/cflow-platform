#!/usr/bin/env python3
"""
Advanced Features Testing Validation Script

Tests the advanced features framework functionality including:
- Expansion pack management
- HIL integration
- Workflow engine
- Monitoring & analytics
- MCP integration
- Cerebral extensions
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cflow_platform.core.direct_client import execute_mcp_tool

async def test_expansion_pack_management():
    """Test expansion pack management functionality"""
    print("📦 Testing Expansion Pack Management")
    print("-" * 40)
    
    try:
        # Test pack discovery
        result = await execute_mcp_tool('bmad_expansion_discover_packs')
        if result['success']:
            print(f"✅ Pack discovery: {result['total_packs']} packs found")
            
            # Test pack installation
            if result['packs']:
                first_pack = result['packs'][0]
                install_result = await execute_mcp_tool('bmad_expansion_install_pack', pack_id=first_pack['id'])
                if install_result['success']:
                    print(f"✅ Pack installation: {install_result['pack_name']}")
                    
                    # Test pack activation
                    activate_result = await execute_mcp_tool('bmad_expansion_activate_pack', pack_id=first_pack['id'])
                    if activate_result['success']:
                        print(f"✅ Pack activation: {activate_result['pack_name']}")
                        
                        # Test pack deactivation
                        deactivate_result = await execute_mcp_tool('bmad_expansion_deactivate_pack', pack_id=first_pack['id'])
                        if deactivate_result['success']:
                            print(f"✅ Pack deactivation: {deactivate_result['pack_name']}")
                        else:
                            print(f"❌ Pack deactivation failed: {deactivate_result.get('error', 'Unknown error')}")
                    else:
                        print(f"❌ Pack activation failed: {activate_result.get('error', 'Unknown error')}")
                else:
                    print(f"❌ Pack installation failed: {install_result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Pack discovery failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Test pack status
        status_result = await execute_mcp_tool('bmad_expansion_get_pack_status')
        if status_result['success']:
            print(f"✅ Pack status: {status_result['status']['total_packs']} total, {status_result['status']['installed_packs']} installed")
        else:
            print(f"❌ Pack status failed: {status_result.get('error', 'Unknown error')}")
        
        return True
    except Exception as e:
        print(f"❌ Expansion pack management error: {e}")
        return False

async def test_hil_integration():
    """Test HIL integration functionality"""
    print("\n🤝 Testing HIL Integration")
    print("-" * 40)
    
    try:
        # Test session creation
        result = await execute_mcp_tool('bmad_hil_create_session', user_id='test_user', task_type='elicitation', context={'test': 'data'})
        if result['success']:
            session_id = result['session_id']
            print(f"✅ HIL session creation: {session_id}")
            
            # Test session update
            update_result = await execute_mcp_tool('bmad_hil_update_session', session_id=session_id, updates={'status': 'updated'})
            if update_result['success']:
                print(f"✅ HIL session update: {update_result['session_id']}")
                
                # Test session completion
                complete_result = await execute_mcp_tool('bmad_hil_complete_session', session_id=session_id, result={'outcome': 'success'})
                if complete_result['success']:
                    print(f"✅ HIL session completion: {complete_result['session_id']}")
                else:
                    print(f"❌ HIL session completion failed: {complete_result.get('error', 'Unknown error')}")
            else:
                print(f"❌ HIL session update failed: {update_result.get('error', 'Unknown error')}")
        else:
            print(f"❌ HIL session creation failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Test HIL status
        status_result = await execute_mcp_tool('bmad_hil_get_status')
        if status_result['success']:
            print(f"✅ HIL status: {status_result['status']['active_sessions']} active, {status_result['status']['total_history']} history")
        else:
            print(f"❌ HIL status failed: {status_result.get('error', 'Unknown error')}")
        
        return True
    except Exception as e:
        print(f"❌ HIL integration error: {e}")
        return False

async def test_workflow_engine():
    """Test workflow engine functionality"""
    print("\n⚙️ Testing Workflow Engine")
    print("-" * 40)
    
    try:
        # Test workflow discovery
        result = await execute_mcp_tool('bmad_workflow_discover')
        if result['success']:
            print(f"✅ Workflow discovery: {result['total_workflows']} workflows found")
            
            # Test workflow start
            if result['workflows']:
                first_workflow = result['workflows'][0]
                start_result = await execute_mcp_tool('bmad_workflow_start', workflow_id=first_workflow['workflow_id'], context={'test': 'data'})
                if start_result['success']:
                    print(f"✅ Workflow start: {start_result['workflow_name']}")
                    
                    # Test workflow step execution
                    if first_workflow['steps'] > 0:
                        step_result = await execute_mcp_tool('bmad_workflow_execute_step', workflow_id=first_workflow['workflow_id'], step_index=0, step_data={'test': 'step'})
                        if step_result['success']:
                            print(f"✅ Workflow step execution: {step_result['step_result']['step_name']}")
                        else:
                            print(f"❌ Workflow step execution failed: {step_result.get('error', 'Unknown error')}")
                    
                    # Test workflow completion
                    complete_result = await execute_mcp_tool('bmad_workflow_complete', workflow_id=first_workflow['workflow_id'], result={'outcome': 'success'})
                    if complete_result['success']:
                        print(f"✅ Workflow completion: {complete_result['workflow_name']}")
                    else:
                        print(f"❌ Workflow completion failed: {complete_result.get('error', 'Unknown error')}")
                else:
                    print(f"❌ Workflow start failed: {start_result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Workflow discovery failed: {result.get('error', 'Unknown error')}")
            return False
        
        # Test workflow status
        status_result = await execute_mcp_tool('bmad_workflow_get_status')
        if status_result['success']:
            print(f"✅ Workflow status: {status_result['status']['total_workflows']} total, {status_result['status']['active_workflows']} active")
        else:
            print(f"❌ Workflow status failed: {status_result.get('error', 'Unknown error')}")
        
        return True
    except Exception as e:
        print(f"❌ Workflow engine error: {e}")
        return False

async def test_monitoring_analytics():
    """Test monitoring & analytics functionality"""
    print("\n📊 Testing Monitoring & Analytics")
    print("-" * 40)
    
    try:
        # Test metric collection
        metrics = [
            ('cpu_usage', 75.5, 'performance', {'server': 'web-01'}),
            ('user_logins', 150, 'usage', {'user_type': 'premium'}),
            ('api_errors', 3, 'error', {'endpoint': '/api/users'}),
            ('security_alerts', 1, 'security', {'threat_level': 'medium'}),
            ('revenue', 50000, 'business', {'currency': 'USD'})
        ]
        
        for name, value, metric_type, tags in metrics:
            result = await execute_mcp_tool('bmad_monitoring_collect_metric', name=name, value=value, metric_type=metric_type, tags=tags)
            if result['success']:
                print(f"✅ Metric collection: {result['name']} = {result['value']}")
            else:
                print(f"❌ Metric collection failed: {result.get('error', 'Unknown error')}")
        
        # Test analytics report generation
        report_types = ['performance', 'usage', 'error', 'security', 'business']
        for report_type in report_types:
            result = await execute_mcp_tool('bmad_monitoring_generate_report', report_type=report_type)
            if result['success']:
                print(f"✅ Analytics report: {result['report_id']} ({len(result['insights'])} insights)")
            else:
                print(f"❌ Analytics report failed: {result.get('error', 'Unknown error')}")
        
        # Test alerts
        alerts_result = await execute_mcp_tool('bmad_monitoring_get_alerts')
        if alerts_result['success']:
            print(f"✅ Alerts: {alerts_result['total_alerts']} alerts found")
        else:
            print(f"❌ Alerts failed: {alerts_result.get('error', 'Unknown error')}")
        
        # Test monitoring status
        status_result = await execute_mcp_tool('bmad_monitoring_get_status')
        if status_result['success']:
            print(f"✅ Monitoring status: {status_result['status']['total_metrics']} metrics, {status_result['status']['total_reports']} reports")
        else:
            print(f"❌ Monitoring status failed: {status_result.get('error', 'Unknown error')}")
        
        return True
    except Exception as e:
        print(f"❌ Monitoring & analytics error: {e}")
        return False

async def run_comprehensive_test():
    """Run comprehensive advanced features validation"""
    print("🧪 Advanced Features Comprehensive Validation")
    print("=" * 60)
    
    tests = [
        ("Expansion Pack Management", test_expansion_pack_management),
        ("HIL Integration", test_hil_integration),
        ("Workflow Engine", test_workflow_engine),
        ("Monitoring & Analytics", test_monitoring_analytics),
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
        print("🎉 All advanced features tests passed!")
        return True
    else:
        print("⚠️ Some advanced features tests failed.")
        return False

async def main():
    """Main test function"""
    try:
        success = await run_comprehensive_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Advanced features validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
