#!/usr/bin/env python3
"""
BMAD Master Deployment CLI

Command-line interface for deploying BMAD Master to different environments.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cflow_platform.core.production_deployment import bmad_master_production_deployment, DeploymentEnvironment
from cflow_platform.core.unified_bmad_system import bmad_master_unified_system
from cflow_platform.core.health_monitoring import bmad_master_health_monitoring

async def deploy_to_environment(environment: str, config_overrides: Dict[str, Any] = None) -> bool:
    """Deploy BMAD Master to specified environment"""
    try:
        print(f'🚀 BMAD Master: Deploying to {environment} environment...')
        
        # Convert string to enum
        env_enum = DeploymentEnvironment(environment.lower())
        
        # Deploy
        result = await bmad_master_production_deployment.deploy(env_enum, config_overrides)
        
        if result['success']:
            print(f'✅ BMAD Master: Successfully deployed to {environment}!')
            print(f'   Deployment ID: {result["deployment_id"]}')
            print(f'   Version: {result["version"]}')
            return True
        else:
            print(f'❌ BMAD Master: Deployment to {environment} failed!')
            print(f'   Error: {result.get("error", "Unknown error")}')
            return False
            
    except Exception as e:
        print(f'❌ BMAD Master: Deployment error: {e}')
        return False

async def initialize_system() -> bool:
    """Initialize the unified BMAD Master system"""
    try:
        print('🚀 BMAD Master: Initializing unified system...')
        
        result = await bmad_master_unified_system.initialize_system()
        
        if result['success']:
            print('✅ BMAD Master: Unified system initialized successfully!')
            print(f'   Status: {result["status"]}')
            print(f'   Version: {result["version"]}')
            return True
        else:
            print(f'❌ BMAD Master: System initialization failed!')
            print(f'   Error: {result.get("error", "Unknown error")}')
            return False
            
    except Exception as e:
        print(f'❌ BMAD Master: Initialization error: {e}')
        return False

async def start_health_monitoring() -> bool:
    """Start health monitoring"""
    try:
        print('🏥 BMAD Master: Starting health monitoring...')
        
        result = await bmad_master_health_monitoring.start_monitoring()
        
        if result['success']:
            print('✅ BMAD Master: Health monitoring started successfully!')
            return True
        else:
            print(f'❌ BMAD Master: Health monitoring failed to start!')
            print(f'   Error: {result.get("error", "Unknown error")}')
            return False
            
    except Exception as e:
        print(f'❌ BMAD Master: Health monitoring error: {e}')
        return False

async def get_health_status() -> bool:
    """Get current health status"""
    try:
        print('🏥 BMAD Master: Getting health status...')
        
        result = await bmad_master_health_monitoring.get_health_status()
        
        if result['success']:
            print('✅ BMAD Master: Health status retrieved successfully!')
            print(f'   Overall Status: {result["overall_status"]}')
            print(f'   Monitoring Active: {result["monitoring_active"]}')
            print(f'   Uptime: {result["uptime"]}')
            
            # Print component statuses
            print('   Component Statuses:')
            for component, status_info in result['components'].items():
                print(f'     • {component}: {status_info["status"]} (errors: {status_info["error_count"]})')
            
            return True
        else:
            print(f'❌ BMAD Master: Health status retrieval failed!')
            print(f'   Error: {result.get("error", "Unknown error")}')
            return False
            
    except Exception as e:
        print(f'❌ BMAD Master: Health status error: {e}')
        return False

async def get_deployment_status(deployment_id: str = None) -> bool:
    """Get deployment status"""
    try:
        print('📊 BMAD Master: Getting deployment status...')
        
        result = await bmad_master_production_deployment.get_deployment_status(deployment_id)
        
        if result['success']:
            print('✅ BMAD Master: Deployment status retrieved successfully!')
            
            if deployment_id:
                # Single deployment
                deployment = result['deployment']
                print(f'   Deployment ID: {deployment["deployment_id"]}')
                print(f'   Environment: {deployment["environment"]}')
                print(f'   Version: {deployment["version"]}')
                print(f'   Status: {deployment["status"]}')
                print(f'   Start Time: {deployment["start_time"]}')
                if 'end_time' in deployment:
                    print(f'   End Time: {deployment["end_time"]}')
            else:
                # All deployments
                deployments = result['deployments']
                print(f'   Total Deployments: {len(deployments)}')
                
                if deployments:
                    print('   Recent Deployments:')
                    for deployment in deployments[-5:]:  # Show last 5
                        print(f'     • {deployment["deployment_id"]}: {deployment["environment"]} - {deployment["status"]}')
            
            return True
        else:
            print(f'❌ BMAD Master: Deployment status retrieval failed!')
            print(f'   Error: {result.get("error", "Unknown error")}')
            return False
            
    except Exception as e:
        print(f'❌ BMAD Master: Deployment status error: {e}')
        return False

async def rollback_deployment(deployment_id: str) -> bool:
    """Rollback a deployment"""
    try:
        print(f'🔄 BMAD Master: Rolling back deployment {deployment_id}...')
        
        result = await bmad_master_production_deployment.rollback(deployment_id)
        
        if result['success']:
            print(f'✅ BMAD Master: Deployment {deployment_id} rolled back successfully!')
            return True
        else:
            print(f'❌ BMAD Master: Rollback of deployment {deployment_id} failed!')
            print(f'   Error: {result.get("error", "Unknown error")}')
            return False
            
    except Exception as e:
        print(f'❌ BMAD Master: Rollback error: {e}')
        return False

async def run_comprehensive_deployment(environment: str) -> bool:
    """Run comprehensive deployment including initialization and health monitoring"""
    try:
        print(f'🚀 BMAD Master: Running comprehensive deployment to {environment}...')
        
        # Step 1: Initialize system
        print('\\n📋 Step 1: Initializing unified system...')
        if not await initialize_system():
            return False
        
        # Step 2: Deploy to environment
        print(f'\\n🔧 Step 2: Deploying to {environment}...')
        if not await deploy_to_environment(environment):
            return False
        
        # Step 3: Start health monitoring
        print('\\n🏥 Step 3: Starting health monitoring...')
        if not await start_health_monitoring():
            return False
        
        # Step 4: Verify deployment
        print('\\n✅ Step 4: Verifying deployment...')
        await asyncio.sleep(2)  # Give system time to stabilize
        
        if not await get_health_status():
            print('⚠️ BMAD Master: Health status check failed, but deployment may still be successful')
        
        print(f'\\n🎉 BMAD Master: Comprehensive deployment to {environment} completed!')
        return True
        
    except Exception as e:
        print(f'❌ BMAD Master: Comprehensive deployment error: {e}')
        return False

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description='BMAD Master Deployment CLI')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy BMAD Master to an environment')
    deploy_parser.add_argument('environment', choices=['development', 'staging', 'production'], 
                              help='Target environment')
    deploy_parser.add_argument('--config', type=str, help='Configuration overrides (JSON)')
    
    # Initialize command
    init_parser = subparsers.add_parser('init', help='Initialize the unified BMAD Master system')
    
    # Health monitoring commands
    health_parser = subparsers.add_parser('health', help='Health monitoring commands')
    health_subparsers = health_parser.add_subparsers(dest='health_command', help='Health commands')
    
    health_subparsers.add_parser('start', help='Start health monitoring')
    health_subparsers.add_parser('status', help='Get health status')
    
    # Deployment status command
    status_parser = subparsers.add_parser('status', help='Get deployment status')
    status_parser.add_argument('--deployment-id', type=str, help='Specific deployment ID')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback a deployment')
    rollback_parser.add_argument('deployment_id', type=str, help='Deployment ID to rollback')
    
    # Comprehensive deployment command
    comprehensive_parser = subparsers.add_parser('deploy-full', help='Run comprehensive deployment')
    comprehensive_parser.add_argument('environment', choices=['development', 'staging', 'production'], 
                                     help='Target environment')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    async def run_command():
        """Run the specified command"""
        try:
            if args.command == 'deploy':
                config_overrides = None
                if args.config:
                    import json
                    config_overrides = json.loads(args.config)
                
                success = await deploy_to_environment(args.environment, config_overrides)
                sys.exit(0 if success else 1)
                
            elif args.command == 'init':
                success = await initialize_system()
                sys.exit(0 if success else 1)
                
            elif args.command == 'health':
                if args.health_command == 'start':
                    success = await start_health_monitoring()
                    sys.exit(0 if success else 1)
                elif args.health_command == 'status':
                    success = await get_health_status()
                    sys.exit(0 if success else 1)
                else:
                    health_parser.print_help()
                    sys.exit(1)
                    
            elif args.command == 'status':
                success = await get_deployment_status(args.deployment_id)
                sys.exit(0 if success else 1)
                
            elif args.command == 'rollback':
                success = await rollback_deployment(args.deployment_id)
                sys.exit(0 if success else 1)
                
            elif args.command == 'deploy-full':
                success = await run_comprehensive_deployment(args.environment)
                sys.exit(0 if success else 1)
                
            else:
                parser.print_help()
                sys.exit(1)
                
        except Exception as e:
            print(f'❌ BMAD Master: Command execution error: {e}')
            sys.exit(1)
    
    # Run the command
    asyncio.run(run_command())

if __name__ == '__main__':
    main()
