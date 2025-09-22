#!/usr/bin/env python3
"""
Test script for the updated One-Touch Installer with cluster deployment support.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n🧪 Testing: {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print(f"Error: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - EXCEPTION: {e}")
        return False


def test_one_touch_installer():
    """Test the One-Touch Installer functionality."""
    print("🚀 Testing One-Touch Installer with Cluster Deployment Support")
    print("=" * 70)
    
    # Test basic help
    success = run_command(
        [sys.executable, "-m", "cflow_platform.cli.one_touch_installer", "--help"],
        "Help command"
    )
    
    # Test cluster validation
    success &= run_command(
        [sys.executable, "-m", "cflow_platform.cli.one_touch_installer", "--validate-cluster"],
        "Cluster deployment validation"
    )
    
    # Test WebMCP setup for cluster deployment
    success &= run_command(
        [sys.executable, "-m", "cflow_platform.cli.one_touch_installer", 
         "--setup-webmcp", "--cluster-deployment", "--overwrite-config"],
        "WebMCP setup for cluster deployment"
    )
    
    # Test WebMCP setup for local deployment
    success &= run_command(
        [sys.executable, "-m", "cflow_platform.cli.one_touch_installer", 
         "--setup-webmcp", "--overwrite-config"],
        "WebMCP setup for local deployment"
    )
    
    # Test BMAD verification
    success &= run_command(
        [sys.executable, "-m", "cflow_platform.cli.one_touch_installer", "--verify-bmad"],
        "BMAD components verification"
    )
    
    # Test custom cluster URLs
    success &= run_command(
        [sys.executable, "-m", "cflow_platform.cli.one_touch_installer", 
         "--setup-webmcp", "--cluster-deployment", 
         "--cluster-webmcp-url", "https://custom-webmcp.example.com",
         "--cluster-bmad-api-url", "https://custom-bmad-api.example.com",
         "--cluster-bmad-method-url", "https://custom-bmad-method.example.com",
         "--overwrite-config"],
        "Custom cluster URLs configuration"
    )
    
    # Test configuration file creation
    config_file = Path.home() / ".cerebraflow" / "webmcp" / "config.json"
    if config_file.exists():
        print(f"✅ Configuration file created: {config_file}")
        try:
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"✅ Configuration valid JSON")
            print(f"   Deployment type: {config.get('deployment_type', 'unknown')}")
            if 'webmcp' in config:
                print(f"   WebMCP URL: {config['webmcp'].get('server_url', 'unknown')}")
            if 'cluster_info' in config:
                print(f"   Cluster DNS: {config['cluster_info'].get('dns_resolution', 'unknown')}")
        except Exception as e:
            print(f"❌ Configuration file invalid: {e}")
            success = False
    else:
        print(f"❌ Configuration file not found: {config_file}")
        success = False
    
    return success


def test_webmcp_installer_module():
    """Test the WebMCP installer module directly."""
    print("\n🔧 Testing WebMCP Installer Module")
    print("=" * 50)
    
    try:
        from cflow_platform.core.webmcp_installer import WebMCPInstaller, WebMCPConfig, WebMCPInstallResult
        
        # Test WebMCPConfig creation
        config = WebMCPConfig(
            server_url="https://test.example.com",
            api_key="test-key",
            bmad_api_url="https://bmad-api.example.com",
            bmad_auth_token="test-token"
        )
        print("✅ WebMCPConfig creation")
        
        # Test WebMCPInstaller creation
        installer = WebMCPInstaller()
        print("✅ WebMCPInstaller creation")
        
        # Test cluster endpoint detection
        is_cluster = installer._detect_cluster_deployment("https://webmcp-bmad.dev.cerebral.baerautotech.com")
        if is_cluster:
            print("✅ Cluster deployment detection")
        else:
            print("❌ Cluster deployment detection failed")
            return False
        
        # Test local endpoint detection
        is_local = installer._detect_cluster_deployment("http://localhost:8000")
        if not is_local:
            print("✅ Local deployment detection")
        else:
            print("❌ Local deployment detection failed")
            return False
        
        # Test configuration creation
        cluster_config = installer._create_cluster_config(config)
        if cluster_config.get('deployment_type') == 'cluster':
            print("✅ Cluster configuration creation")
        else:
            print("❌ Cluster configuration creation failed")
            return False
        
        local_config = installer._create_local_config(config)
        if local_config.get('deployment_type') == 'local':
            print("✅ Local configuration creation")
        else:
            print("❌ Local configuration creation failed")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ WebMCP installer module import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ WebMCP installer module test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 One-Touch Installer Test Suite")
    print("=" * 50)
    
    # Test WebMCP installer module
    module_success = test_webmcp_installer_module()
    
    # Test One-Touch installer
    installer_success = test_one_touch_installer()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 30)
    print(f"WebMCP Installer Module: {'✅ PASS' if module_success else '❌ FAIL'}")
    print(f"One-Touch Installer: {'✅ PASS' if installer_success else '❌ FAIL'}")
    
    overall_success = module_success and installer_success
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 One-Touch Installer is ready for cluster deployment!")
        print("\nUsage examples:")
        print("  # Setup for cluster deployment")
        print("  python -m cflow_platform.cli.one_touch_installer --setup-webmcp --cluster-deployment")
        print("\n  # Validate cluster endpoints")
        print("  python -m cflow_platform.cli.one_touch_installer --validate-cluster")
        print("\n  # Full setup with BMAD integration")
        print("  python -m cflow_platform.cli.one_touch_installer --setup-webmcp --setup-bmad --cluster-deployment")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
