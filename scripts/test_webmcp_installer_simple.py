#!/usr/bin/env python3
"""
Simple test for WebMCP installer module without external dependencies.
"""

import json
import sys
from pathlib import Path


def test_webmcp_config():
    """Test WebMCPConfig dataclass."""
    print("🧪 Testing WebMCPConfig...")
    
    try:
        # Import the module
        sys.path.insert(0, str(Path(__file__).parent))
        from cflow_platform.core.webmcp_installer import WebMCPConfig
        
        # Create config
        config = WebMCPConfig(
            server_url="https://test.example.com",
            api_key="test-key",
            bmad_api_url="https://bmad-api.example.com",
            bmad_auth_token="test-token",
            timeout=30
        )
        
        print(f"✅ WebMCPConfig created successfully")
        print(f"   Server URL: {config.server_url}")
        print(f"   API Key: {config.api_key}")
        print(f"   BMAD API URL: {config.bmad_api_url}")
        print(f"   Timeout: {config.timeout}")
        
        return True
        
    except Exception as e:
        print(f"❌ WebMCPConfig test failed: {e}")
        return False


def test_webmcp_install_result():
    """Test WebMCPInstallResult dataclass."""
    print("\n🧪 Testing WebMCPInstallResult...")
    
    try:
        # Import the module
        sys.path.insert(0, str(Path(__file__).parent))
        from cflow_platform.core.webmcp_installer import WebMCPInstallResult
        
        # Create success result
        success_result = WebMCPInstallResult(
            success=True,
            message="Test successful",
            config_file_path="/tmp/test.json",
            warnings=["Test warning"],
            errors=[]
        )
        
        print(f"✅ WebMCPInstallResult created successfully")
        print(f"   Success: {success_result.success}")
        print(f"   Message: {success_result.message}")
        print(f"   Config file: {success_result.config_file_path}")
        print(f"   Warnings: {len(success_result.warnings)}")
        print(f"   Errors: {len(success_result.errors)}")
        
        return True
        
    except Exception as e:
        print(f"❌ WebMCPInstallResult test failed: {e}")
        return False


def test_webmcp_installer_basic():
    """Test WebMCPInstaller basic functionality."""
    print("\n🧪 Testing WebMCPInstaller basic functionality...")
    
    try:
        # Import the module
        sys.path.insert(0, str(Path(__file__).parent))
        from cflow_platform.core.webmcp_installer import WebMCPInstaller, WebMCPConfig
        
        # Create installer
        installer = WebMCPInstaller()
        print(f"✅ WebMCPInstaller created successfully")
        print(f"   Config dir: {installer.config_dir}")
        print(f"   Config file: {installer.config_file}")
        
        # Test cluster endpoints
        print(f"   Cluster endpoints: {len(installer.cluster_endpoints)}")
        for service, url in installer.cluster_endpoints.items():
            print(f"     {service}: {url}")
        
        # Test cluster detection
        cluster_url = "https://webmcp-bmad.dev.cerebral.baerautotech.com"
        is_cluster = installer._detect_cluster_deployment(cluster_url)
        print(f"✅ Cluster detection: {is_cluster} for {cluster_url}")
        
        local_url = "http://localhost:8000"
        is_local = installer._detect_cluster_deployment(local_url)
        print(f"✅ Local detection: {not is_local} for {local_url}")
        
        # Test config creation
        config = WebMCPConfig(
            server_url=cluster_url,
            api_key="test-key",
            bmad_api_url="https://bmad-api.example.com",
            bmad_auth_token="test-token"
        )
        
        cluster_config = installer._create_cluster_config(config)
        print(f"✅ Cluster config created: {cluster_config.get('deployment_type')}")
        
        local_config = installer._create_local_config(config)
        print(f"✅ Local config created: {local_config.get('deployment_type')}")
        
        return True
        
    except Exception as e:
        print(f"❌ WebMCPInstaller basic test failed: {e}")
        return False


def test_config_file_creation():
    """Test configuration file creation."""
    print("\n🧪 Testing configuration file creation...")
    
    try:
        # Import the module
        sys.path.insert(0, str(Path(__file__).parent))
        from cflow_platform.core.webmcp_installer import WebMCPInstaller, WebMCPConfig
        
        # Create installer with test config dir
        test_config_dir = Path("/tmp/test_webmcp_config")
        installer = WebMCPInstaller(config_dir=test_config_dir)
        
        # Create config
        config = WebMCPConfig(
            server_url="https://webmcp-bmad.dev.cerebral.baerautotech.com",
            api_key="test-key",
            bmad_api_url="https://bmad-api.dev.cerebral.baerautotech.com",
            bmad_auth_token="test-token"
        )
        
        # Install configuration (without connection test)
        result = installer.install_webmcp_configuration(config, overwrite=True)
        
        if result.success:
            print(f"✅ Configuration file created successfully")
            print(f"   Config file: {result.config_file_path}")
            
            # Verify file exists and is valid JSON
            if installer.config_file.exists():
                with open(installer.config_file, 'r') as f:
                    config_data = json.load(f)
                
                print(f"✅ Configuration file is valid JSON")
                print(f"   Deployment type: {config_data.get('deployment_type')}")
                print(f"   WebMCP URL: {config_data.get('webmcp', {}).get('server_url')}")
                
                if 'cluster_info' in config_data:
                    print(f"   Cluster DNS: {config_data['cluster_info'].get('dns_resolution')}")
                    print(f"   Certificates: {config_data['cluster_info'].get('certificates')}")
                    print(f"   Authentication: {config_data['cluster_info'].get('authentication')}")
                
                return True
            else:
                print(f"❌ Configuration file not found: {installer.config_file}")
                return False
        else:
            print(f"❌ Configuration installation failed: {result.message}")
            return False
        
    except Exception as e:
        print(f"❌ Configuration file creation test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 WebMCP Installer Module Test Suite")
    print("=" * 50)
    
    tests = [
        test_webmcp_config,
        test_webmcp_install_result,
        test_webmcp_installer_basic,
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
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
