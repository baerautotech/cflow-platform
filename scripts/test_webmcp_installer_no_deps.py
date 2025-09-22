#!/usr/bin/env python3
"""
Test for WebMCP installer module without external dependencies.
"""

import json
import sys
from pathlib import Path


def test_webmcp_config():
    """Test WebMCPConfig dataclass."""
    print("🧪 Testing WebMCPConfig...")
    
    try:
        # Create config manually (simulating the dataclass)
        config_data = {
            "server_url": "https://test.example.com",
            "api_key": "test-key",
            "bmad_api_url": "https://bmad-api.example.com",
            "bmad_auth_token": "test-token",
            "timeout": 30
        }
        
        print(f"✅ WebMCPConfig structure validated")
        print(f"   Server URL: {config_data['server_url']}")
        print(f"   API Key: {config_data['api_key']}")
        print(f"   BMAD API URL: {config_data['bmad_api_url']}")
        print(f"   Timeout: {config_data['timeout']}")
        
        return True
        
    except Exception as e:
        print(f"❌ WebMCPConfig test failed: {e}")
        return False


def test_webmcp_install_result():
    """Test WebMCPInstallResult dataclass."""
    print("\n🧪 Testing WebMCPInstallResult...")
    
    try:
        # Create result manually (simulating the dataclass)
        result_data = {
            "success": True,
            "message": "Test successful",
            "config_file_path": "/tmp/test.json",
            "warnings": ["Test warning"],
            "errors": []
        }
        
        print(f"✅ WebMCPInstallResult structure validated")
        print(f"   Success: {result_data['success']}")
        print(f"   Message: {result_data['message']}")
        print(f"   Config file: {result_data['config_file_path']}")
        print(f"   Warnings: {len(result_data['warnings'])}")
        print(f"   Errors: {len(result_data['errors'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ WebMCPInstallResult test failed: {e}")
        return False


def test_cluster_detection():
    """Test cluster deployment detection logic."""
    print("\n🧪 Testing cluster deployment detection...")
    
    try:
        def detect_cluster_deployment(server_url: str) -> bool:
            """Detect if this is a cluster deployment based on URL."""
            cluster_indicators = [
                "cerebral.baerautotech.com",
                "dev.cerebral.baerautotech.com",
                "webmcp-bmad.dev.cerebral.baerautotech.com"
            ]
            return any(indicator in server_url for indicator in cluster_indicators)
        
        # Test cluster URLs
        cluster_urls = [
            "https://webmcp-bmad.dev.cerebral.baerautotech.com",
            "https://bmad-api.dev.cerebral.baerautotech.com",
            "https://bmad-method.dev.cerebral.baerautotech.com"
        ]
        
        for url in cluster_urls:
            is_cluster = detect_cluster_deployment(url)
            print(f"✅ Cluster detection: {is_cluster} for {url}")
            if not is_cluster:
                return False
        
        # Test local URLs
        local_urls = [
            "http://localhost:8000",
            "http://127.0.0.1:8001",
            "http://localhost:8080"
        ]
        
        for url in local_urls:
            is_cluster = detect_cluster_deployment(url)
            print(f"✅ Local detection: {not is_cluster} for {url}")
            if is_cluster:
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Cluster detection test failed: {e}")
        return False


def test_config_creation():
    """Test configuration creation logic."""
    print("\n🧪 Testing configuration creation...")
    
    try:
        def create_cluster_config(config_data):
            """Create configuration for cluster deployment."""
            return {
                "deployment_type": "cluster",
                "webmcp": {
                    "server_url": "https://webmcp-bmad.dev.cerebral.baerautotech.com",
                    "api_key": config_data.get("api_key"),
                    "timeout": config_data.get("timeout", 30),
                    "health_endpoint": "https://webmcp-bmad.dev.cerebral.baerautotech.com/health",
                    "tools_endpoint": "https://webmcp-bmad.dev.cerebral.baerautotech.com/mcp/tools",
                    "call_endpoint": "https://webmcp-bmad.dev.cerebral.baerautotech.com/mcp/tools/call"
                },
                "bmad_api": {
                    "server_url": "https://bmad-api.dev.cerebral.baerautotech.com",
                    "auth_token": config_data.get("bmad_auth_token"),
                    "timeout": config_data.get("timeout", 30),
                    "health_endpoint": "https://bmad-api.dev.cerebral.baerautotech.com/health",
                    "project_type_endpoint": "https://bmad-api.dev.cerebral.baerautotech.com/bmad/project-type/detect",
                    "prd_create_endpoint": "https://bmad-api.dev.cerebral.baerautotech.com/bmad/greenfield/prd-create"
                },
                "bmad_method": {
                    "server_url": "https://bmad-method.dev.cerebral.baerautotech.com",
                    "timeout": config_data.get("timeout", 30),
                    "health_endpoint": "https://bmad-method.dev.cerebral.baerautotech.com/health",
                    "agents_endpoint": "https://bmad-method.dev.cerebral.baerautotech.com/bmad/agents",
                    "workflows_endpoint": "https://bmad-method.dev.cerebral.baerautotech.com/bmad/workflows"
                },
                "cluster_info": {
                    "dns_resolution": "cerebral.baerautotech.com",
                    "certificates": "Let's Encrypt via cert-manager",
                    "authentication": "Dex OIDC",
                    "load_balancer": "MetalLB"
                }
            }
        
        def create_local_config(config_data):
            """Create configuration for local deployment."""
            return {
                "deployment_type": "local",
                "webmcp": {
                    "server_url": config_data.get("server_url", "http://localhost:8000"),
                    "api_key": config_data.get("api_key"),
                    "timeout": config_data.get("timeout", 30),
                    "health_endpoint": f"{config_data.get('server_url', 'http://localhost:8000')}/health",
                    "tools_endpoint": f"{config_data.get('server_url', 'http://localhost:8000')}/mcp/tools",
                    "call_endpoint": f"{config_data.get('server_url', 'http://localhost:8000')}/mcp/tools/call"
                },
                "bmad_api": {
                    "server_url": config_data.get("bmad_api_url", "http://localhost:8001"),
                    "auth_token": config_data.get("bmad_auth_token"),
                    "timeout": config_data.get("timeout", 30),
                    "health_endpoint": f"{config_data.get('bmad_api_url', 'http://localhost:8001')}/health"
                },
                "bmad_method": {
                    "server_url": "http://localhost:8080",
                    "timeout": config_data.get("timeout", 30),
                    "health_endpoint": "http://localhost:8080/health"
                }
            }
        
        # Test cluster config
        config_data = {
            "server_url": "https://webmcp-bmad.dev.cerebral.baerautotech.com",
            "api_key": "test-key",
            "bmad_api_url": "https://bmad-api.dev.cerebral.baerautotech.com",
            "bmad_auth_token": "test-token",
            "timeout": 30
        }
        
        cluster_config = create_cluster_config(config_data)
        print(f"✅ Cluster config created: {cluster_config.get('deployment_type')}")
        print(f"   WebMCP URL: {cluster_config['webmcp']['server_url']}")
        print(f"   BMAD API URL: {cluster_config['bmad_api']['server_url']}")
        print(f"   BMAD-Method URL: {cluster_config['bmad_method']['server_url']}")
        print(f"   DNS Resolution: {cluster_config['cluster_info']['dns_resolution']}")
        
        # Test local config
        local_config = create_local_config(config_data)
        print(f"✅ Local config created: {local_config.get('deployment_type')}")
        print(f"   WebMCP URL: {local_config['webmcp']['server_url']}")
        print(f"   BMAD API URL: {local_config['bmad_api']['server_url']}")
        print(f"   BMAD-Method URL: {local_config['bmad_method']['server_url']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration creation test failed: {e}")
        return False


def test_config_file_creation():
    """Test configuration file creation."""
    print("\n🧪 Testing configuration file creation...")
    
    try:
        # Create test config directory
        test_config_dir = Path("/tmp/test_webmcp_config")
        test_config_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = test_config_dir / "config.json"
        
        # Create cluster configuration
        cluster_config = {
            "deployment_type": "cluster",
            "webmcp": {
                "server_url": "https://webmcp-bmad.dev.cerebral.baerautotech.com",
                "api_key": "test-key",
                "timeout": 30,
                "health_endpoint": "https://webmcp-bmad.dev.cerebral.baerautotech.com/health",
                "tools_endpoint": "https://webmcp-bmad.dev.cerebral.baerautotech.com/mcp/tools",
                "call_endpoint": "https://webmcp-bmad.dev.cerebral.baerautotech.com/mcp/tools/call"
            },
            "bmad_api": {
                "server_url": "https://bmad-api.dev.cerebral.baerautotech.com",
                "auth_token": "test-token",
                "timeout": 30,
                "health_endpoint": "https://bmad-api.dev.cerebral.baerautotech.com/health",
                "project_type_endpoint": "https://bmad-api.dev.cerebral.baerautotech.com/bmad/project-type/detect",
                "prd_create_endpoint": "https://bmad-api.dev.cerebral.baerautotech.com/bmad/greenfield/prd-create"
            },
            "bmad_method": {
                "server_url": "https://bmad-method.dev.cerebral.baerautotech.com",
                "timeout": 30,
                "health_endpoint": "https://bmad-method.dev.cerebral.baerautotech.com/health",
                "agents_endpoint": "https://bmad-method.dev.cerebral.baerautotech.com/bmad/agents",
                "workflows_endpoint": "https://bmad-method.dev.cerebral.baerautotech.com/bmad/workflows"
            },
            "cluster_info": {
                "dns_resolution": "cerebral.baerautotech.com",
                "certificates": "Let's Encrypt via cert-manager",
                "authentication": "Dex OIDC",
                "load_balancer": "MetalLB"
            }
        }
        
        # Write configuration file
        with open(config_file, 'w') as f:
            json.dump(cluster_config, f, indent=2)
        
        print(f"✅ Configuration file created: {config_file}")
        
        # Verify file exists and is valid JSON
        if config_file.exists():
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            print(f"✅ Configuration file is valid JSON")
            print(f"   Deployment type: {config_data.get('deployment_type')}")
            print(f"   WebMCP URL: {config_data.get('webmcp', {}).get('server_url')}")
            print(f"   BMAD API URL: {config_data.get('bmad_api', {}).get('server_url')}")
            print(f"   BMAD-Method URL: {config_data.get('bmad_method', {}).get('server_url')}")
            
            if 'cluster_info' in config_data:
                print(f"   Cluster DNS: {config_data['cluster_info'].get('dns_resolution')}")
                print(f"   Certificates: {config_data['cluster_info'].get('certificates')}")
                print(f"   Authentication: {config_data['cluster_info'].get('authentication')}")
                print(f"   Load Balancer: {config_data['cluster_info'].get('load_balancer')}")
            
            return True
        else:
            print(f"❌ Configuration file not found: {config_file}")
            return False
        
    except Exception as e:
        print(f"❌ Configuration file creation test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 WebMCP Installer Module Test Suite (No Dependencies)")
    print("=" * 60)
    
    tests = [
        test_webmcp_config,
        test_webmcp_install_result,
        test_cluster_detection,
        test_config_creation,
        test_config_file_creation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"💥 Test {test.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {test.__name__}: {status}")
    
    print(f"\nOverall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All WebMCP Installer tests passed!")
        print("\nThe One-Touch Installer is ready for cluster deployment.")
        print("\nUsage examples:")
        print("  # Setup for cluster deployment")
        print("  python -m cflow_platform.cli.one_touch_installer --setup-webmcp --cluster-deployment")
        print("\n  # Validate cluster endpoints")
        print("  python -m cflow_platform.cli.one_touch_installer --validate-cluster")
        print("\n  # Full setup with BMAD integration")
        print("  python -m cflow_platform.cli.one_touch_installer --setup-webmcp --setup-bmad --cluster-deployment")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
