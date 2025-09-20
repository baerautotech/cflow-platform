#!/usr/bin/env python3
"""
Cerebral Platform Pod Generator
Generates consistent Kubernetes deployments for all cerebral platform services
"""

import argparse
import json
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class PodGenerator:
    """Generates Kubernetes deployments using the pod framework"""
    
    def __init__(self, framework_dir: str = "infrastructure/framework"):
        self.framework_dir = Path(framework_dir)
        self.templates_dir = self.framework_dir / "templates"
        self.output_dir = Path("infrastructure/kubernetes")
        
    def load_framework_config(self) -> Dict[str, Any]:
        """Load framework configuration"""
        config_file = self.framework_dir / "pod-framework.yaml"
        if not config_file.exists():
            raise FileNotFoundError(f"Framework config not found: {config_file}")
            
        with open(config_file, 'r') as f:
            content = f.read()
            
        # Parse YAML documents
        documents = list(yaml.safe_load_all(content))
        config_doc = documents[0]  # First document is the config
        
        return config_doc['data']
    
    def get_environment_config(self, environment: str) -> Dict[str, Any]:
        """Get configuration for specific environment"""
        config = self.load_framework_config()
        environments = yaml.safe_load(config['environments'])
        
        if environment not in environments:
            raise ValueError(f"Unknown environment: {environment}")
            
        return environments[environment]
    
    def generate_pod_config(self, 
                          service_name: str,
                          component: str,
                          tier: str,
                          environment: str,
                          port: int = 8000,
                          image: str = None,
                          custom_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate pod configuration for a service"""
        
        # Get environment-specific config
        env_config = self.get_environment_config(environment)
        
        # Default values
        config = {
            'name': service_name,
            'namespace': f'cerebral-{environment}',
            'version': '1.0.0',
            'component': component,
            'tier': tier,
            'environment': environment,
            'registry': 'registry.baerautotech.com',
            'image': image or service_name,
            'tag': 'latest',  # Will be replaced with SHA in deployment
            'port': port,
            'replicas': env_config['replicas'],
            'resources': env_config['resources'],
            'security': env_config['security'],
            'monitoring': env_config['monitoring'],
            'ingress': env_config['ingress'],
            'hpa': env_config['hpa'],
            'secrets': env_config['secrets'],
            'timestamp': datetime.utcnow().isoformat(),
            
            # Health check configuration
            'health': {
                'path': '/health',
                'initialDelaySeconds': 30,
                'readinessDelaySeconds': 10,
                'periodSeconds': 10,
                'timeoutSeconds': 5,
                'failureThreshold': 3
            },
            
            # Default environment variables
            'env': {
                'SERVICE_NAME': service_name,
                'ENVIRONMENT': environment,
                'PORT': str(port),
                'LOG_LEVEL': 'info'
            },
            
            # Default configuration
            'config': {
                'SERVICE_NAME': service_name,
                'ENVIRONMENT': environment,
                'PORT': str(port),
                'LOG_LEVEL': 'info'
            },
            
            # Default secrets (empty, to be filled by deployment)
            'secretData': {},
            
            # Default volumes
            'volumes': [
                {
                    'name': 'tmp-storage',
                    'emptyDir': {'sizeLimit': '1Gi'}
                }
            ],
            
            # Default volume mounts
            'volumeMounts': [
                {
                    'name': 'tmp-storage',
                    'mountPath': '/tmp'
                }
            ]
        }
        
        # Apply custom configuration
        if custom_config:
            config.update(custom_config)
            
        # Set ingress hosts based on environment
        if config['ingress']['enabled']:
            config['ingress']['hosts'] = [f"{service_name}.{environment}.baerautotech.com"]
            config['ingress']['proxyBodySize'] = "10m"
            config['ingress']['proxyReadTimeout'] = "300"
            config['ingress']['proxySendTimeout'] = "300"
            config['ingress']['rateLimit'] = "10"
            config['ingress']['rateLimitWindow'] = "1m"
            
        # Set HPA configuration
        if config['hpa']['enabled']:
            config['hpa']['minReplicas'] = env_config['hpa']['min_replicas']
            config['hpa']['maxReplicas'] = env_config['hpa']['max_replicas']
            config['hpa']['cpuTarget'] = 70
            config['hpa']['memoryTarget'] = 80
            config['hpa']['scaleDownStabilization'] = 300
            config['hpa']['scaleDownPercent'] = 10
            config['hpa']['scaleDownPeriod'] = 60
            config['hpa']['scaleUpStabilization'] = 60
            config['hpa']['scaleUpPercent'] = 50
            config['hpa']['scaleUpPeriod'] = 60
            
        return config
    
    def generate_kubernetes_manifests(self, config: Dict[str, Any]) -> List[str]:
        """Generate Kubernetes manifest files"""
        manifests = []
        
        # Load templates
        template_files = [
            'deployment.yaml',
            'service.yaml', 
            'serviceaccount.yaml',
            'configmap.yaml',
            'secret.yaml',
            'hpa.yaml',
            'ingress.yaml'
        ]
        
        for template_file in template_files:
            template_path = self.templates_dir / template_file
            if template_path.exists():
                with open(template_path, 'r') as f:
                    template_content = f.read()
                    
                # Simple template substitution (in production, use Jinja2)
                manifest_content = self._substitute_template(template_content, config)
                manifests.append(manifest_content)
                
        return manifests
    
    def _substitute_template(self, template: str, config: Dict[str, Any]) -> str:
        """Simple template substitution"""
        # This is a simplified version - in production, use Jinja2
        result = template
        
        # Replace {{ .Values.key }} patterns
        import re
        pattern = r'\{\{\s*\.Values\.(\w+)\s*\}\}'
        
        def replace_func(match):
            key = match.group(1)
            if key in config:
                value = config[key]
                if isinstance(value, (dict, list)):
                    return yaml.dump(value, default_flow_style=False).strip()
                else:
                    return str(value)
            return match.group(0)
            
        result = re.sub(pattern, replace_func, result)
        
        # Replace {{ .Values.key.subkey }} patterns
        pattern = r'\{\{\s*\.Values\.(\w+)\.(\w+)\s*\}\}'
        
        def replace_nested_func(match):
            key1, key2 = match.group(1), match.group(2)
            if key1 in config and key2 in config[key1]:
                value = config[key1][key2]
                if isinstance(value, (dict, list)):
                    return yaml.dump(value, default_flow_style=False).strip()
                else:
                    return str(value)
            return match.group(0)
            
        result = re.sub(pattern, replace_nested_func, result)
        
        return result
    
    def save_manifests(self, service_name: str, environment: str, manifests: List[str]):
        """Save generated manifests to files"""
        output_file = self.output_dir / f"{service_name}-{environment}.yaml"
        
        # Combine all manifests into one file
        combined_content = "---\n".join(manifests)
        
        with open(output_file, 'w') as f:
            f.write(combined_content)
            
        print(f"Generated manifests for {service_name} ({environment}): {output_file}")
    
    def generate_service(self, 
                       service_name: str,
                       component: str,
                       tier: str,
                       environment: str,
                       **kwargs):
        """Generate complete service deployment"""
        
        # Generate configuration
        config = self.generate_pod_config(
            service_name=service_name,
            component=component,
            tier=tier,
            environment=environment,
            **kwargs
        )
        
        # Generate manifests
        manifests = self.generate_kubernetes_manifests(config)
        
        # Save manifests
        self.save_manifests(service_name, environment, manifests)
        
        return config

def main():
    parser = argparse.ArgumentParser(description='Generate Kubernetes pod deployments')
    parser.add_argument('service_name', help='Name of the service')
    parser.add_argument('component', help='Component type (api, service, worker, etc.)')
    parser.add_argument('tier', help='Tier (frontend, backend, data, etc.)')
    parser.add_argument('environment', choices=['development', 'staging', 'production', 'enterprise'],
                       help='Deployment environment')
    parser.add_argument('--port', type=int, default=8000, help='Service port')
    parser.add_argument('--image', help='Docker image name (defaults to service_name)')
    parser.add_argument('--config', help='Path to custom configuration JSON file')
    parser.add_argument('--output-dir', default='infrastructure/kubernetes',
                       help='Output directory for generated manifests')
    
    args = parser.parse_args()
    
    # Load custom config if provided
    custom_config = {}
    if args.config:
        with open(args.config, 'r') as f:
            custom_config = json.load(f)
    
    # Generate the service
    generator = PodGenerator()
    
    try:
        config = generator.generate_service(
            service_name=args.service_name,
            component=args.component,
            tier=args.tier,
            environment=args.environment,
            port=args.port,
            image=args.image,
            custom_config=custom_config
        )
        
        print(f"✅ Successfully generated {args.service_name} deployment for {args.environment}")
        print(f"📊 Configuration: {json.dumps(config, indent=2)}")
        
    except Exception as e:
        print(f"❌ Error generating service: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
