#!/usr/bin/env python3
"""
Simple Cerebral Platform Pod Generator
Generates Kubernetes deployments directly without complex templating
"""

import argparse
import json
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class SimplePodGenerator:
    """Simple pod generator that creates Kubernetes manifests directly"""
    
    def __init__(self):
        self.output_dir = Path("infrastructure/kubernetes")
        
    def get_environment_config(self, environment: str) -> Dict[str, Any]:
        """Get configuration for specific environment"""
        configs = {
            'development': {
                'replicas': 1,
                'resources': {
                    'requests': {'memory': '256Mi', 'cpu': '100m'},
                    'limits': {'memory': '512Mi', 'cpu': '250m'}
                },
                'security': {
                    'runAsNonRoot': False,
                    'allowPrivilegeEscalation': True,
                    'readOnlyRootFilesystem': False
                },
                'monitoring': {'enabled': False},
                'ingress': {'enabled': False, 'tls': False},
                'hpa': {'enabled': False},
                'secrets': {'vault_integration': False, 'supabase_integration': False}
            },
            'staging': {
                'replicas': 2,
                'resources': {
                    'requests': {'memory': '512Mi', 'cpu': '250m'},
                    'limits': {'memory': '1Gi', 'cpu': '500m'}
                },
                'security': {
                    'runAsNonRoot': True,
                    'allowPrivilegeEscalation': False,
                    'readOnlyRootFilesystem': False
                },
                'monitoring': {'enabled': True},
                'ingress': {'enabled': True, 'tls': True},
                'hpa': {'enabled': True, 'min_replicas': 2, 'max_replicas': 5},
                'secrets': {'vault_integration': True, 'supabase_integration': True}
            },
            'production': {
                'replicas': 3,
                'resources': {
                    'requests': {'memory': '1Gi', 'cpu': '500m'},
                    'limits': {'memory': '2Gi', 'cpu': '1000m'}
                },
                'security': {
                    'runAsNonRoot': True,
                    'allowPrivilegeEscalation': False,
                    'readOnlyRootFilesystem': True
                },
                'monitoring': {'enabled': True},
                'ingress': {'enabled': True, 'tls': True},
                'hpa': {'enabled': True, 'min_replicas': 3, 'max_replicas': 10},
                'secrets': {'vault_integration': True, 'supabase_integration': True}
            },
            'enterprise': {
                'replicas': 5,
                'resources': {
                    'requests': {'memory': '2Gi', 'cpu': '1000m'},
                    'limits': {'memory': '4Gi', 'cpu': '2000m'}
                },
                'security': {
                    'runAsNonRoot': True,
                    'allowPrivilegeEscalation': False,
                    'readOnlyRootFilesystem': True,
                    'seccompProfile': 'RuntimeDefault'
                },
                'monitoring': {'enabled': True},
                'ingress': {'enabled': True, 'tls': True},
                'hpa': {'enabled': True, 'min_replicas': 5, 'max_replicas': 20},
                'secrets': {'vault_integration': True, 'supabase_integration': True, 'enterprise_secrets': True}
            }
        }
        
        if environment not in configs:
            raise ValueError(f"Unknown environment: {environment}")
            
        return configs[environment]
    
    def load_service_config(self, service_name: str) -> Dict[str, Any]:
        """Load service configuration from services.yaml"""
        services_file = Path("infrastructure/framework/services.yaml")
        if not services_file.exists():
            raise FileNotFoundError(f"Services file not found: {services_file}")
            
        with open(services_file, 'r') as f:
            services_data = yaml.safe_load(f)
            
        if service_name not in services_data['services']:
            raise ValueError(f"Service {service_name} not found in services.yaml")
            
        return services_data['services'][service_name]
    
    def generate_deployment_manifest(self, service_name: str, service_config: Dict[str, Any], env_config: Dict[str, Any], environment: str) -> str:
        """Generate deployment manifest"""
        
        # Extract service configuration
        component = service_config['component']
        tier = service_config['tier']
        port = service_config['port']
        image = service_config['image']
        
        # Extract environment configuration
        replicas = env_config['replicas']
        resources = env_config['resources']
        security = env_config['security']
        
        # Generate environment variables
        env_vars = service_config.get('env', {})
        env_vars.update({
            'SERVICE_NAME': service_name,
            'ENVIRONMENT': environment,
            'PORT': str(port),
            'LOG_LEVEL': 'info'
        })
        
        # Generate secrets
        secrets = service_config.get('secrets', {})
        
        # Generate volumes
        volumes = service_config.get('volumes', [])
        volumes.append({'name': 'tmp-storage', 'emptyDir': {'sizeLimit': '1Gi'}})
        
        # Generate volume mounts
        volume_mounts = service_config.get('volumeMounts', [])
        volume_mounts.append({'name': 'tmp-storage', 'mountPath': '/tmp'})
        
        # Create deployment manifest
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': service_name,
                'namespace': f'cerebral-{environment}',
                'labels': {
                    'app': service_name,
                    'version': '1.0.0',
                    'component': component,
                    'tier': tier,
                    'environment': environment,
                    'app.kubernetes.io/managed-by': 'cerebral-platform',
                    'app.kubernetes.io/part-of': 'cerebral-cluster'
                },
                'annotations': {
                    'cerebral.baerautotech.com/created-by': 'pod-framework',
                    'cerebral.baerautotech.com/framework-version': '1.0.0',
                    'cerebral.baerautotech.com/last-updated': datetime.now().isoformat()
                }
            },
            'spec': {
                'replicas': replicas,
                'selector': {
                    'matchLabels': {
                        'app': service_name
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': service_name,
                            'version': '1.0.0',
                            'component': component,
                            'tier': tier,
                            'environment': environment
                        }
                    },
                    'spec': {
                        'serviceAccountName': f'{service_name}-sa',
                        'containers': [{
                            'name': service_name,
                            'image': f'registry.baerautotech.com/{image}:latest',
                            'imagePullPolicy': 'Always',
                            'ports': [{
                                'containerPort': port,
                                'name': 'http',
                                'protocol': 'TCP'
                            }],
                            'env': [{'name': k, 'value': v} for k, v in env_vars.items()],
                            'resources': resources,
                            'livenessProbe': {
                                'httpGet': {
                                    'path': service_config.get('health_path', '/health'),
                                    'port': port,
                                    'scheme': 'HTTP'
                                },
                                'initialDelaySeconds': 30,
                                'periodSeconds': 10,
                                'timeoutSeconds': 5,
                                'failureThreshold': 3
                            },
                            'readinessProbe': {
                                'httpGet': {
                                    'path': service_config.get('health_path', '/health'),
                                    'port': port,
                                    'scheme': 'HTTP'
                                },
                                'initialDelaySeconds': 10,
                                'periodSeconds': 5,
                                'timeoutSeconds': 3,
                                'failureThreshold': 3
                            },
                            'securityContext': security,
                            'volumeMounts': volume_mounts
                        }],
                        'volumes': volumes,
                        'securityContext': {
                            'fsGroup': 1000,
                            'runAsNonRoot': security['runAsNonRoot']
                        },
                        'restartPolicy': 'Always'
                    }
                }
            }
        }
        
        # Add secrets to environment variables
        if secrets:
            secret_env_vars = []
            for key, secret_key in secrets.items():
                secret_env_vars.append({
                    'name': key,
                    'valueFrom': {
                        'secretKeyRef': {
                            'name': f'{service_name}-secrets',
                            'key': secret_key
                        }
                    }
                })
            deployment['spec']['template']['spec']['containers'][0]['env'].extend(secret_env_vars)
        
        return yaml.dump(deployment, default_flow_style=False)
    
    def generate_service_manifest(self, service_name: str, service_config: Dict[str, Any], environment: str) -> str:
        """Generate service manifest"""
        port = service_config['port']
        component = service_config['component']
        tier = service_config['tier']
        
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f'{service_name}-service',
                'namespace': f'cerebral-{environment}',
                'labels': {
                    'app': service_name,
                    'component': component,
                    'tier': tier,
                    'environment': environment
                }
            },
            'spec': {
                'selector': {
                    'app': service_name
                },
                'ports': [{
                    'port': port,
                    'targetPort': port,
                    'protocol': 'TCP',
                    'name': 'http'
                }],
                'type': 'ClusterIP'
            }
        }
        
        return yaml.dump(service, default_flow_style=False)
    
    def generate_serviceaccount_manifest(self, service_name: str, service_config: Dict[str, Any], environment: str) -> str:
        """Generate service account manifest"""
        component = service_config['component']
        tier = service_config['tier']
        
        serviceaccount = {
            'apiVersion': 'v1',
            'kind': 'ServiceAccount',
            'metadata': {
                'name': f'{service_name}-sa',
                'namespace': f'cerebral-{environment}',
                'labels': {
                    'app': service_name,
                    'component': component,
                    'tier': tier,
                    'environment': environment
                }
            }
        }
        
        return yaml.dump(serviceaccount, default_flow_style=False)
    
    def generate_configmap_manifest(self, service_name: str, service_config: Dict[str, Any], environment: str) -> str:
        """Generate configmap manifest"""
        component = service_config['component']
        tier = service_config['tier']
        config = service_config.get('config', {})
        
        configmap = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': f'{service_name}-config',
                'namespace': f'cerebral-{environment}',
                'labels': {
                    'app': service_name,
                    'component': component,
                    'tier': tier,
                    'environment': environment
                }
            },
            'data': config
        }
        
        return yaml.dump(configmap, default_flow_style=False)
    
    def generate_secret_manifest(self, service_name: str, service_config: Dict[str, Any], environment: str) -> str:
        """Generate secret manifest"""
        component = service_config['component']
        tier = service_config['tier']
        secrets = service_config.get('secrets', {})
        
        secret = {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': f'{service_name}-secrets',
                'namespace': f'cerebral-{environment}',
                'labels': {
                    'app': service_name,
                    'component': component,
                    'tier': tier,
                    'environment': environment
                }
            },
            'type': 'Opaque',
            'data': {key: '' for key in secrets.keys()}  # Empty values, to be filled by deployment
        }
        
        return yaml.dump(secret, default_flow_style=False)
    
    def generate_hpa_manifest(self, service_name: str, service_config: Dict[str, Any], env_config: Dict[str, Any], environment: str) -> str:
        """Generate HPA manifest"""
        if not env_config['hpa']['enabled']:
            return ''
            
        component = service_config['component']
        tier = service_config['tier']
        hpa_config = env_config['hpa']
        
        hpa = {
            'apiVersion': 'autoscaling/v2',
            'kind': 'HorizontalPodAutoscaler',
            'metadata': {
                'name': f'{service_name}-hpa',
                'namespace': f'cerebral-{environment}',
                'labels': {
                    'app': service_name,
                    'component': component,
                    'tier': tier,
                    'environment': environment
                }
            },
            'spec': {
                'scaleTargetRef': {
                    'apiVersion': 'apps/v1',
                    'kind': 'Deployment',
                    'name': service_name
                },
                'minReplicas': hpa_config['min_replicas'],
                'maxReplicas': hpa_config['max_replicas'],
                'metrics': [
                    {
                        'type': 'Resource',
                        'resource': {
                            'name': 'cpu',
                            'target': {
                                'type': 'Utilization',
                                'averageUtilization': 70
                            }
                        }
                    },
                    {
                        'type': 'Resource',
                        'resource': {
                            'name': 'memory',
                            'target': {
                                'type': 'Utilization',
                                'averageUtilization': 80
                            }
                        }
                    }
                ],
                'behavior': {
                    'scaleDown': {
                        'stabilizationWindowSeconds': 300,
                        'policies': [{
                            'type': 'Percent',
                            'value': 10,
                            'periodSeconds': 60
                        }]
                    },
                    'scaleUp': {
                        'stabilizationWindowSeconds': 60,
                        'policies': [{
                            'type': 'Percent',
                            'value': 50,
                            'periodSeconds': 60
                        }]
                    }
                }
            }
        }
        
        return yaml.dump(hpa, default_flow_style=False)
    
    def generate_ingress_manifest(self, service_name: str, service_config: Dict[str, Any], env_config: Dict[str, Any], environment: str) -> str:
        """Generate ingress manifest"""
        if not env_config['ingress']['enabled']:
            return ''
            
        component = service_config['component']
        tier = service_config['tier']
        port = service_config['port']
        ingress_config = env_config['ingress']
        
        ingress = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'Ingress',
            'metadata': {
                'name': f'{service_name}-ingress',
                'namespace': f'cerebral-{environment}',
                'labels': {
                    'app': service_name,
                    'component': component,
                    'tier': tier,
                    'environment': environment
                },
                'annotations': {
                    'nginx.ingress.kubernetes.io/ssl-redirect': str(ingress_config['tls']).lower(),
                    'nginx.ingress.kubernetes.io/force-ssl-redirect': str(ingress_config['tls']).lower(),
                    'nginx.ingress.kubernetes.io/proxy-body-size': '10m',
                    'nginx.ingress.kubernetes.io/proxy-read-timeout': '300',
                    'nginx.ingress.kubernetes.io/proxy-send-timeout': '300'
                }
            },
            'spec': {
                'ingressClassName': 'nginx',
                'rules': [{
                    'host': f'{service_name}.{environment}.baerautotech.com',
                    'http': {
                        'paths': [{
                            'path': '/',
                            'pathType': 'Prefix',
                            'backend': {
                                'service': {
                                    'name': f'{service_name}-service',
                                    'port': {'number': port}
                                }
                            }
                        }]
                    }
                }]
            }
        }
        
        if ingress_config['tls']:
            ingress['spec']['tls'] = [{
                'hosts': [f'{service_name}.{environment}.baerautotech.com'],
                'secretName': f'{service_name}-tls'
            }]
            ingress['metadata']['annotations']['cert-manager.io/cluster-issuer'] = 'letsencrypt-prod'
        
        return yaml.dump(ingress, default_flow_style=False)
    
    def generate_all_manifests(self, service_name: str, environment: str) -> str:
        """Generate all manifests for a service"""
        
        # Load configurations
        service_config = self.load_service_config(service_name)
        env_config = self.get_environment_config(environment)
        
        # Generate all manifests
        manifests = []
        
        manifests.append(self.generate_deployment_manifest(service_name, service_config, env_config, environment))
        manifests.append(self.generate_service_manifest(service_name, service_config, environment))
        manifests.append(self.generate_serviceaccount_manifest(service_name, service_config, environment))
        manifests.append(self.generate_configmap_manifest(service_name, service_config, environment))
        manifests.append(self.generate_secret_manifest(service_name, service_config, environment))
        
        hpa_manifest = self.generate_hpa_manifest(service_name, service_config, env_config, environment)
        if hpa_manifest:
            manifests.append(hpa_manifest)
            
        ingress_manifest = self.generate_ingress_manifest(service_name, service_config, env_config, environment)
        if ingress_manifest:
            manifests.append(ingress_manifest)
        
        # Combine all manifests
        return '---\n'.join(manifests)
    
    def save_manifests(self, service_name: str, environment: str, manifests: str):
        """Save generated manifests to file"""
        output_file = self.output_dir / f"{service_name}-{environment}.yaml"
        
        with open(output_file, 'w') as f:
            f.write(manifests)
            
        print(f"Generated manifests for {service_name} ({environment}): {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate Kubernetes pod deployments (simple version)')
    parser.add_argument('service_name', help='Name of the service')
    parser.add_argument('environment', choices=['development', 'staging', 'production', 'enterprise'],
                       help='Deployment environment')
    
    args = parser.parse_args()
    
    # Generate the service
    generator = SimplePodGenerator()
    
    try:
        manifests = generator.generate_all_manifests(args.service_name, args.environment)
        generator.save_manifests(args.service_name, args.environment, manifests)
        
        print(f"✅ Successfully generated {args.service_name} deployment for {args.environment}")
        
    except Exception as e:
        print(f"❌ Error generating service: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
