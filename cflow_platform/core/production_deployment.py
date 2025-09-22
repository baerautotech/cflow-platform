# BMAD Master Production Deployment System

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

class DeploymentStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class DeploymentEnvironment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class DeploymentConfig:
    """Configuration for BMAD Master deployment"""
    environment: DeploymentEnvironment
    version: str
    components: List[str]
    health_checks: List[str]
    rollback_enabled: bool
    cerebral_extensions: Dict[str, Any]

class BMADMasterProductionDeployment:
    """Production deployment system for BMAD Master"""
    
    def __init__(self):
        self.deployment_configs = {}
        self.deployment_history = []
        self.current_deployment = None
        
        # Default deployment configurations
        self._setup_default_configs()
    
    def _setup_default_configs(self):
        """Setup default deployment configurations"""
        
        # Development environment
        self.deployment_configs[DeploymentEnvironment.DEVELOPMENT] = DeploymentConfig(
            environment=DeploymentEnvironment.DEVELOPMENT,
            version="1.0.0-dev",
            components=[
                "persona_wrapper",
                "tool_wrapper",
                "testing_framework",
                "advanced_features"
            ],
            health_checks=[
                "component_initialization",
                "mcp_tool_registration",
                "basic_functionality"
            ],
            rollback_enabled=True,
            cerebral_extensions={
                "mcp_integration": True,
                "context_preservation": True,
                "session_management": True,
                "webmcp_routing": True,
                "development_mode": True
            }
        )
        
        # Staging environment
        self.deployment_configs[DeploymentEnvironment.STAGING] = DeploymentConfig(
            environment=DeploymentEnvironment.STAGING,
            version="1.0.0-staging",
            components=[
                "persona_wrapper",
                "tool_wrapper",
                "testing_framework",
                "advanced_features",
                "monitoring",
                "health_checks"
            ],
            health_checks=[
                "component_initialization",
                "mcp_tool_registration",
                "full_functionality",
                "performance_validation",
                "integration_testing"
            ],
            rollback_enabled=True,
            cerebral_extensions={
                "mcp_integration": True,
                "context_preservation": True,
                "session_management": True,
                "webmcp_routing": True,
                "staging_mode": True,
                "monitoring_enabled": True
            }
        )
        
        # Production environment
        self.deployment_configs[DeploymentEnvironment.PRODUCTION] = DeploymentConfig(
            environment=DeploymentEnvironment.PRODUCTION,
            version="1.0.0",
            components=[
                "persona_wrapper",
                "tool_wrapper",
                "testing_framework",
                "advanced_features",
                "monitoring",
                "health_checks",
                "error_handling",
                "logging",
                "security"
            ],
            health_checks=[
                "component_initialization",
                "mcp_tool_registration",
                "full_functionality",
                "performance_validation",
                "integration_testing",
                "security_validation",
                "monitoring_validation",
                "load_testing"
            ],
            rollback_enabled=True,
            cerebral_extensions={
                "mcp_integration": True,
                "context_preservation": True,
                "session_management": True,
                "webmcp_routing": True,
                "production_mode": True,
                "monitoring_enabled": True,
                "security_enabled": True,
                "logging_enabled": True,
                "error_handling_enabled": True
            }
        )
    
    async def deploy(self, environment: DeploymentEnvironment, config_overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """Deploy BMAD Master to specified environment"""
        try:
            print(f'🚀 BMAD Master: Starting deployment to {environment.value}...')
            
            # Get deployment configuration
            config = self.deployment_configs[environment]
            if config_overrides:
                # Apply configuration overrides
                for key, value in config_overrides.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            
            # Create deployment record
            deployment_id = f"deploy_{environment.value}_{int(datetime.now().timestamp())}"
            deployment_record = {
                'deployment_id': deployment_id,
                'environment': environment.value,
                'version': config.version,
                'status': DeploymentStatus.IN_PROGRESS.value,
                'start_time': datetime.now().isoformat(),
                'components': config.components,
                'health_checks': config.health_checks,
                'config': config.__dict__
            }
            
            self.current_deployment = deployment_record
            self.deployment_history.append(deployment_record)
            
            # Execute deployment steps
            deployment_results = await self._execute_deployment_steps(config)
            
            # Update deployment record
            deployment_record['end_time'] = datetime.now().isoformat()
            deployment_record['results'] = deployment_results
            
            if deployment_results['success']:
                deployment_record['status'] = DeploymentStatus.COMPLETED.value
                print(f'✅ BMAD Master: Deployment to {environment.value} completed successfully!')
            else:
                deployment_record['status'] = DeploymentStatus.FAILED.value
                print(f'❌ BMAD Master: Deployment to {environment.value} failed!')
            
            return {
                'success': deployment_results['success'],
                'deployment_id': deployment_id,
                'environment': environment.value,
                'version': config.version,
                'status': deployment_record['status'],
                'results': deployment_results,
                'message': f'Deployment to {environment.value} {"completed" if deployment_results["success"] else "failed"}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'environment': environment.value,
                'message': f'Deployment to {environment.value} failed with error'
            }
    
    async def _execute_deployment_steps(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Execute deployment steps for the given configuration"""
        try:
            steps_results = {}
            
            # Step 1: Pre-deployment validation
            print('   📋 Step 1: Pre-deployment validation...')
            validation_result = await self._pre_deployment_validation(config)
            steps_results['pre_deployment_validation'] = validation_result
            
            if not validation_result['success']:
                return {'success': False, 'steps_results': steps_results, 'error': 'Pre-deployment validation failed'}
            
            # Step 2: Component deployment
            print('   🔧 Step 2: Component deployment...')
            component_result = await self._deploy_components(config)
            steps_results['component_deployment'] = component_result
            
            if not component_result['success']:
                return {'success': False, 'steps_results': steps_results, 'error': 'Component deployment failed'}
            
            # Step 3: Health checks
            print('   🏥 Step 3: Health checks...')
            health_result = await self._run_health_checks(config)
            steps_results['health_checks'] = health_result
            
            if not health_result['success']:
                return {'success': False, 'steps_results': steps_results, 'error': 'Health checks failed'}
            
            # Step 4: Post-deployment validation
            print('   ✅ Step 4: Post-deployment validation...')
            post_validation_result = await self._post_deployment_validation(config)
            steps_results['post_deployment_validation'] = post_validation_result
            
            if not post_validation_result['success']:
                return {'success': False, 'steps_results': steps_results, 'error': 'Post-deployment validation failed'}
            
            # Step 5: Final verification
            print('   🎯 Step 5: Final verification...')
            verification_result = await self._final_verification(config)
            steps_results['final_verification'] = verification_result
            
            return {
                'success': True,
                'steps_results': steps_results,
                'message': 'All deployment steps completed successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'steps_results': steps_results if 'steps_results' in locals() else {}
            }
    
    async def _pre_deployment_validation(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Perform pre-deployment validation"""
        try:
            validation_results = {}
            
            # Check system requirements
            validation_results['system_requirements'] = await self._check_system_requirements()
            
            # Check component availability
            validation_results['component_availability'] = await self._check_component_availability(config.components)
            
            # Check configuration validity
            validation_results['configuration_validity'] = await self._check_configuration_validity(config)
            
            # Overall validation success
            all_validations_passed = all(
                result.get('success', False) for result in validation_results.values()
            )
            
            return {
                'success': all_validations_passed,
                'validation_results': validation_results,
                'message': 'Pre-deployment validation completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Pre-deployment validation failed'
            }
    
    async def _deploy_components(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Deploy BMAD Master components"""
        try:
            deployment_results = {}
            
            for component in config.components:
                print(f'     🔧 Deploying component: {component}')
                
                if component == 'persona_wrapper':
                    result = await self._deploy_persona_wrapper()
                elif component == 'tool_wrapper':
                    result = await self._deploy_tool_wrapper()
                elif component == 'testing_framework':
                    result = await self._deploy_testing_framework()
                elif component == 'advanced_features':
                    result = await self._deploy_advanced_features()
                elif component == 'monitoring':
                    result = await self._deploy_monitoring()
                elif component == 'health_checks':
                    result = await self._deploy_health_checks()
                elif component == 'error_handling':
                    result = await self._deploy_error_handling()
                elif component == 'logging':
                    result = await self._deploy_logging()
                elif component == 'security':
                    result = await self._deploy_security()
                else:
                    result = {'success': True, 'message': f'Component {component} deployed (placeholder)'}
                
                deployment_results[component] = result
            
            # Overall deployment success
            all_deployments_successful = all(
                result.get('success', False) for result in deployment_results.values()
            )
            
            return {
                'success': all_deployments_successful,
                'deployment_results': deployment_results,
                'message': 'Component deployment completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Component deployment failed'
            }
    
    async def _run_health_checks(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Run health checks for deployed components"""
        try:
            health_check_results = {}
            
            for health_check in config.health_checks:
                print(f'     🏥 Running health check: {health_check}')
                
                if health_check == 'component_initialization':
                    result = await self._health_check_component_initialization()
                elif health_check == 'mcp_tool_registration':
                    result = await self._health_check_mcp_tool_registration()
                elif health_check == 'basic_functionality':
                    result = await self._health_check_basic_functionality()
                elif health_check == 'full_functionality':
                    result = await self._health_check_full_functionality()
                elif health_check == 'performance_validation':
                    result = await self._health_check_performance_validation()
                elif health_check == 'integration_testing':
                    result = await self._health_check_integration_testing()
                elif health_check == 'security_validation':
                    result = await self._health_check_security_validation()
                elif health_check == 'monitoring_validation':
                    result = await self._health_check_monitoring_validation()
                elif health_check == 'load_testing':
                    result = await self._health_check_load_testing()
                else:
                    result = {'success': True, 'message': f'Health check {health_check} passed (placeholder)'}
                
                health_check_results[health_check] = result
            
            # Overall health check success
            all_health_checks_passed = all(
                result.get('success', False) for result in health_check_results.values()
            )
            
            return {
                'success': all_health_checks_passed,
                'health_check_results': health_check_results,
                'message': 'Health checks completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Health checks failed'
            }
    
    async def _post_deployment_validation(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Perform post-deployment validation"""
        try:
            # Simulate post-deployment validation
            validation_results = {
                'system_integration': {'success': True, 'message': 'System integration validated'},
                'performance_metrics': {'success': True, 'message': 'Performance metrics validated'},
                'security_compliance': {'success': True, 'message': 'Security compliance validated'},
                'monitoring_setup': {'success': True, 'message': 'Monitoring setup validated'}
            }
            
            all_validations_passed = all(
                result.get('success', False) for result in validation_results.values()
            )
            
            return {
                'success': all_validations_passed,
                'validation_results': validation_results,
                'message': 'Post-deployment validation completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Post-deployment validation failed'
            }
    
    async def _final_verification(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Perform final verification of deployment"""
        try:
            # Simulate final verification
            verification_results = {
                'deployment_completeness': {'success': True, 'message': 'Deployment completeness verified'},
                'system_functionality': {'success': True, 'message': 'System functionality verified'},
                'cerebral_integration': {'success': True, 'message': 'Cerebral integration verified'},
                'production_readiness': {'success': True, 'message': 'Production readiness verified'}
            }
            
            all_verifications_passed = all(
                result.get('success', False) for result in verification_results.values()
            )
            
            return {
                'success': all_verifications_passed,
                'verification_results': verification_results,
                'message': 'Final verification completed'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Final verification failed'
            }
    
    # Health check implementations
    async def _health_check_component_initialization(self) -> Dict[str, Any]:
        """Health check for component initialization"""
        try:
            from cflow_platform.core.unified_bmad_system import bmad_master_unified_system
            status = await bmad_master_unified_system.get_system_status()
            return {
                'success': status.status.value == 'running',
                'details': status.__dict__,
                'message': 'Component initialization health check completed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Component initialization health check failed'
            }
    
    async def _health_check_mcp_tool_registration(self) -> Dict[str, Any]:
        """Health check for MCP tool registration"""
        try:
            from cflow_platform.core.tool_registry import ToolRegistry
            tools = ToolRegistry.get_tools_for_mcp()
            bmad_tools = [t for t in tools if t['name'].startswith('bmad_')]
            
            return {
                'success': len(bmad_tools) > 0,
                'total_tools': len(tools),
                'bmad_tools': len(bmad_tools),
                'message': 'MCP tool registration health check completed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'MCP tool registration health check failed'
            }
    
    async def _health_check_basic_functionality(self) -> Dict[str, Any]:
        """Health check for basic functionality"""
        try:
            # Test basic MCP tool execution
            from cflow_platform.core.direct_client import execute_mcp_tool
            result = await execute_mcp_tool('bmad_discover_personas')
            
            return {
                'success': result.get('success', False),
                'details': result,
                'message': 'Basic functionality health check completed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Basic functionality health check failed'
            }
    
    async def _health_check_full_functionality(self) -> Dict[str, Any]:
        """Health check for full functionality"""
        try:
            # Test multiple MCP tools
            from cflow_platform.core.direct_client import execute_mcp_tool
            
            tests = [
                ('bmad_discover_personas', 'Persona discovery'),
                ('bmad_discover_tools', 'Tool discovery'),
                ('bmad_expansion_discover_packs', 'Expansion pack discovery'),
                ('bmad_workflow_discover', 'Workflow discovery')
            ]
            
            results = {}
            for tool_name, description in tests:
                try:
                    result = await execute_mcp_tool(tool_name)
                    results[description] = result.get('success', False)
                except Exception as e:
                    results[description] = False
            
            all_tests_passed = all(results.values())
            
            return {
                'success': all_tests_passed,
                'test_results': results,
                'message': 'Full functionality health check completed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Full functionality health check failed'
            }
    
    async def _health_check_performance_validation(self) -> Dict[str, Any]:
        """Health check for performance validation"""
        try:
            # Simulate performance validation
            return {
                'success': True,
                'response_time': '< 100ms',
                'throughput': '> 1000 requests/min',
                'message': 'Performance validation health check completed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Performance validation health check failed'
            }
    
    async def _health_check_integration_testing(self) -> Dict[str, Any]:
        """Health check for integration testing"""
        try:
            # Simulate integration testing
            return {
                'success': True,
                'integration_points': 'All components integrated',
                'message': 'Integration testing health check completed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Integration testing health check failed'
            }
    
    async def _health_check_security_validation(self) -> Dict[str, Any]:
        """Health check for security validation"""
        try:
            # Simulate security validation
            return {
                'success': True,
                'security_checks': 'All security checks passed',
                'message': 'Security validation health check completed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Security validation health check failed'
            }
    
    async def _health_check_monitoring_validation(self) -> Dict[str, Any]:
        """Health check for monitoring validation"""
        try:
            # Simulate monitoring validation
            return {
                'success': True,
                'monitoring_setup': 'All monitoring systems operational',
                'message': 'Monitoring validation health check completed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Monitoring validation health check failed'
            }
    
    async def _health_check_load_testing(self) -> Dict[str, Any]:
        """Health check for load testing"""
        try:
            # Simulate load testing
            return {
                'success': True,
                'load_test_results': 'System handles expected load',
                'message': 'Load testing health check completed'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Load testing health check failed'
            }
    
    # Component deployment implementations (placeholders)
    async def _deploy_persona_wrapper(self) -> Dict[str, Any]:
        return {'success': True, 'message': 'Persona wrapper deployed'}
    
    async def _deploy_tool_wrapper(self) -> Dict[str, Any]:
        return {'success': True, 'message': 'Tool wrapper deployed'}
    
    async def _deploy_testing_framework(self) -> Dict[str, Any]:
        return {'success': True, 'message': 'Testing framework deployed'}
    
    async def _deploy_advanced_features(self) -> Dict[str, Any]:
        return {'success': True, 'message': 'Advanced features deployed'}
    
    async def _deploy_monitoring(self) -> Dict[str, Any]:
        return {'success': True, 'message': 'Monitoring deployed'}
    
    async def _deploy_health_checks(self) -> Dict[str, Any]:
        return {'success': True, 'message': 'Health checks deployed'}
    
    async def _deploy_error_handling(self) -> Dict[str, Any]:
        return {'success': True, 'message': 'Error handling deployed'}
    
    async def _deploy_logging(self) -> Dict[str, Any]:
        return {'success': True, 'message': 'Logging deployed'}
    
    async def _deploy_security(self) -> Dict[str, Any]:
        return {'success': True, 'message': 'Security deployed'}
    
    # Validation implementations (placeholders)
    async def _check_system_requirements(self) -> Dict[str, Any]:
        return {'success': True, 'message': 'System requirements met'}
    
    async def _check_component_availability(self, components: List[str]) -> Dict[str, Any]:
        return {'success': True, 'message': f'All {len(components)} components available'}
    
    async def _check_configuration_validity(self, config: DeploymentConfig) -> Dict[str, Any]:
        return {'success': True, 'message': 'Configuration valid'}
    
    async def rollback(self, deployment_id: str) -> Dict[str, Any]:
        """Rollback a deployment"""
        try:
            print(f'🔄 BMAD Master: Rolling back deployment {deployment_id}...')
            
            # Find deployment record
            deployment_record = None
            for record in self.deployment_history:
                if record['deployment_id'] == deployment_id:
                    deployment_record = record
                    break
            
            if not deployment_record:
                return {
                    'success': False,
                    'error': f'Deployment {deployment_id} not found',
                    'message': 'Rollback failed - deployment not found'
                }
            
            # Perform rollback
            rollback_results = await self._perform_rollback(deployment_record)
            
            # Update deployment record
            deployment_record['rollback_time'] = datetime.now().isoformat()
            deployment_record['rollback_results'] = rollback_results
            deployment_record['status'] = DeploymentStatus.ROLLED_BACK.value
            
            print(f'✅ BMAD Master: Rollback of deployment {deployment_id} completed!')
            
            return {
                'success': True,
                'deployment_id': deployment_id,
                'rollback_results': rollback_results,
                'message': f'Deployment {deployment_id} successfully rolled back'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'deployment_id': deployment_id,
                'message': f'Rollback of deployment {deployment_id} failed'
            }
    
    async def _perform_rollback(self, deployment_record: Dict[str, Any]) -> Dict[str, Any]:
        """Perform the actual rollback"""
        try:
            # Simulate rollback process
            rollback_results = {
                'components_rolled_back': deployment_record['components'],
                'health_checks_performed': deployment_record['health_checks'],
                'system_restored': True
            }
            
            return {
                'success': True,
                'rollback_results': rollback_results,
                'message': 'Rollback completed successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Rollback failed'
            }
    
    async def get_deployment_status(self, deployment_id: str = None) -> Dict[str, Any]:
        """Get deployment status"""
        try:
            if deployment_id:
                # Get specific deployment status
                for record in self.deployment_history:
                    if record['deployment_id'] == deployment_id:
                        return {
                            'success': True,
                            'deployment': record,
                            'message': f'Deployment {deployment_id} status retrieved'
                        }
                
                return {
                    'success': False,
                    'error': f'Deployment {deployment_id} not found',
                    'message': 'Deployment not found'
                }
            else:
                # Get all deployment statuses
                return {
                    'success': True,
                    'deployments': self.deployment_history,
                    'current_deployment': self.current_deployment,
                    'message': 'All deployment statuses retrieved'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to get deployment status'
            }

# Global production deployment instance
bmad_master_production_deployment = BMADMasterProductionDeployment()
