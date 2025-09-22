#!/usr/bin/env python3
"""
Phase 6: Final Integration & Production Deployment Testing

Tests the complete BMAD Master system integration including:
- Unified system initialization
- Production deployment
- Health monitoring
- Cross-phase workflows
- System health checks
- MCP integration validation
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cflow_platform.core.unified_bmad_system import bmad_master_unified_system
from cflow_platform.core.production_deployment import bmad_master_production_deployment, DeploymentEnvironment
from cflow_platform.core.health_monitoring import bmad_master_health_monitoring
from cflow_platform.core.direct_client import execute_mcp_tool

async def test_unified_system_initialization():
    """Test unified system initialization"""
    print("🚀 Testing Unified System Initialization")
    print("-" * 50)
    
    try:
        result = await bmad_master_unified_system.initialize_system()
        if result['success']:
            print(f"✅ System initialized: {result['status']}")
            print(f"✅ Version: {result['version']}")
            print(f"✅ Components: {len(result['components'])} components")
            print(f"✅ MCP Tools: {result['mcp_tools']['bmad_tools']} BMAD tools")
            
            # Show component details
            for component_name, component_result in result['components'].items():
                if component_result['status'] == 'success':
                    print(f"   • {component_name}: {component_result.get('message', 'Initialized')}")
                else:
                    print(f"   • {component_name}: ERROR - {component_result.get('error', 'Unknown error')}")
            
            return True
        else:
            print(f"❌ Initialization failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_production_deployment():
    """Test production deployment"""
    print("\n🔧 Testing Production Deployment")
    print("-" * 50)
    
    try:
        # Test development deployment
        result = await bmad_master_production_deployment.deploy(DeploymentEnvironment.DEVELOPMENT)
        if result['success']:
            print(f"✅ Development deployment: {result['deployment_id']}")
            print(f"✅ Environment: {result['environment']}")
            print(f"✅ Version: {result['version']}")
            print(f"✅ Status: {result['status']}")
            
            # Show deployment steps
            if 'results' in result and 'steps_results' in result['results']:
                steps = result['results']['steps_results']
                for step_name, step_result in steps.items():
                    status = "✅" if step_result.get('success', False) else "❌"
                    print(f"   {status} {step_name}: {step_result.get('message', 'Completed')}")
            
            return True
        else:
            print(f"❌ Deployment failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_health_monitoring():
    """Test health monitoring system"""
    print("\n🏥 Testing Health Monitoring")
    print("-" * 50)
    
    try:
        # Start monitoring
        start_result = await bmad_master_health_monitoring.start_monitoring()
        if start_result['success']:
            print(f"✅ Health monitoring started: {start_result['monitoring_active']}")
            
            # Wait for monitoring to collect data
            await asyncio.sleep(3)
            
            # Get health status
            health_result = await bmad_master_health_monitoring.get_health_status()
            if health_result['success']:
                print(f"✅ Overall status: {health_result['overall_status']}")
                print(f"✅ Monitoring active: {health_result['monitoring_active']}")
                print(f"✅ Components monitored: {len(health_result['components'])}")
                print(f"✅ Recent metrics: {len(health_result['recent_metrics'])}")
                
                # Show component statuses
                print("   Component Statuses:")
                for component, status_info in health_result['components'].items():
                    status_icon = "✅" if status_info['status'] == 'healthy' else "⚠️" if status_info['status'] == 'warning' else "❌"
                    print(f"     {status_icon} {component}: {status_info['status']} (errors: {status_info['error_count']})")
                
                return True
            else:
                print(f"❌ Health status failed: {health_result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Health monitoring start failed: {start_result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_cross_phase_workflows():
    """Test cross-phase workflows"""
    print("\n🔄 Testing Cross-Phase Workflows")
    print("-" * 50)
    
    try:
        # Test complete BMAD workflow
        result = await bmad_master_unified_system.execute_cross_phase_workflow(
            'complete_bmad_workflow',
            {
                'persona_id': 'bmad-master',
                'tool_id': 'bmad_discover_tools',
                'test_type': 'workflow',
                'expansion_pack_id': 'bmad-godot-game-dev'
            }
        )
        
        if result['success']:
            print(f"✅ Cross-phase workflow: {result['workflow_type']}")
            print(f"✅ Phases executed: {result['phases_executed']}")
            print(f"✅ Results: {len(result['results'])} results")
            
            # Show phase results
            for phase, phase_result in result['results'].items():
                status = "✅" if phase_result.get('success', False) else "❌"
                print(f"   {status} {phase}: {phase_result.get('message', 'Completed')}")
            
            return True
        else:
            print(f"❌ Cross-phase workflow failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_system_health_check():
    """Test system health check"""
    print("\n🔍 Testing System Health Check")
    print("-" * 50)
    
    try:
        result = await bmad_master_unified_system.health_check()
        if result['overall_status'] in ['healthy', 'degraded']:
            print(f"✅ System health: {result['overall_status']}")
            print(f"✅ Components checked: {len(result['components'])}")
            
            # Show component health
            healthy_components = 0
            for component_name, component_result in result['components'].items():
                if component_result['status'] == 'healthy':
                    healthy_components += 1
                    print(f"   ✅ {component_name}: {component_result['status']}")
                else:
                    print(f"   ❌ {component_name}: {component_result['status']}")
            
            print(f"✅ Healthy components: {healthy_components}/{len(result['components'])}")
            return True
        else:
            print(f"❌ System health check failed: {result['overall_status']}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_mcp_integration_validation():
    """Test MCP integration validation"""
    print("\n🔗 Testing MCP Integration Validation")
    print("-" * 50)
    
    try:
        # Test key MCP tools from each phase
        mcp_tests = [
            ('bmad_discover_personas', 'Persona Management (Phase 2)'),
            ('bmad_discover_tools', 'Tool Consolidation (Phase 3)'),
            ('bmad_workflow_test_run_complete', 'Testing Framework (Phase 4)'),
            ('bmad_expansion_discover_packs', 'Advanced Features (Phase 5)'),
            ('bmad_monitoring_collect_metric', 'Monitoring (Phase 6)', {'name': 'test_metric', 'value': 100, 'metric_type': 'performance'})
        ]
        
        passed_tests = 0
        for test_item in mcp_tests:
            if len(test_item) == 3:
                tool_name, description, params = test_item
            else:
                tool_name, description = test_item
                params = {}
            
            try:
                result = await execute_mcp_tool(tool_name, **params)
                if result.get('success', False):
                    print(f"   ✅ {description}: {tool_name}")
                    passed_tests += 1
                else:
                    print(f"   ❌ {description}: {tool_name} - {result.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"   ❌ {description}: {tool_name} - {e}")
        
        print(f"✅ MCP Integration: {passed_tests}/{len(mcp_tests)} tools working")
        return passed_tests == len(mcp_tests)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_deployment_status():
    """Test deployment status retrieval"""
    print("\n📊 Testing Deployment Status")
    print("-" * 50)
    
    try:
        result = await bmad_master_production_deployment.get_deployment_status()
        if result['success']:
            deployments = result['deployments']
            print(f"✅ Total deployments: {len(deployments)}")
            
            if deployments:
                print("   Recent deployments:")
                for deployment in deployments[-3:]:  # Show last 3
                    print(f"     • {deployment['deployment_id']}: {deployment['environment']} - {deployment['status']}")
            
            return True
        else:
            print(f"❌ Deployment status failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def run_comprehensive_phase_6_test():
    """Run comprehensive Phase 6 validation"""
    print("🧪 Phase 6: Final Integration & Production Deployment - Comprehensive Validation")
    print("=" * 80)
    
    tests = [
        ("Unified System Initialization", test_unified_system_initialization),
        ("Production Deployment", test_production_deployment),
        ("Health Monitoring", test_health_monitoring),
        ("Cross-Phase Workflows", test_cross_phase_workflows),
        ("System Health Check", test_system_health_check),
        ("MCP Integration Validation", test_mcp_integration_validation),
        ("Deployment Status", test_deployment_status),
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
    
    print("\n" + "=" * 80)
    print(f"📊 Phase 6 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Phase 6 tests passed!")
        print("🚀 BMAD Master is ready for production deployment!")
        return True
    else:
        print("⚠️ Some Phase 6 tests failed.")
        return False

async def main():
    """Main test function"""
    try:
        success = await run_comprehensive_phase_6_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Phase 6 validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
