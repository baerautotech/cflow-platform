#!/usr/bin/env python3
"""
Setup script for BMAD CLI

This script sets up the BMAD CLI for local development and testing.
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_bmad_cli():
    """Set up the BMAD CLI."""
    print("🚀 Setting up BMAD CLI...")
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    bmad_cli_path = project_root / "cflow_platform" / "cli" / "bmad_cli.py"
    
    # Check if the BMAD CLI file exists
    if not bmad_cli_path.exists():
        print("❌ BMAD CLI file not found. Please ensure bmad_cli.py exists.")
        return False
    
    # Make the CLI executable
    try:
        os.chmod(bmad_cli_path, 0o755)
        print("✅ Made BMAD CLI executable")
    except Exception as e:
        print(f"⚠️  Could not make BMAD CLI executable: {e}")
    
    # Create a symlink in the project root for easy access
    symlink_path = project_root / "bmad"
    try:
        if symlink_path.exists():
            symlink_path.unlink()
        symlink_path.symlink_to(bmad_cli_path)
        print(f"✅ Created symlink: {symlink_path} -> {bmad_cli_path}")
    except Exception as e:
        print(f"⚠️  Could not create symlink: {e}")
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    
    required_packages = ["click", "httpx"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n📦 Install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("\n🎉 BMAD CLI setup complete!")
    print("\n📖 Usage:")
    print("  # Check if BMAD API service is running")
    print("  ./bmad health")
    print()
    print("  # List available BMAD tools")
    print("  ./bmad list-tools")
    print()
    print("  # Detect project type")
    print("  ./bmad detect-project-type --has-existing-code --has-tests --project-size medium")
    print()
    print("  # Document an existing project")
    print("  ./bmad document-project /path/to/project --focus-areas 'backend,api'")
    print()
    print("  # Create brownfield PRD")
    print("  ./bmad create-brownfield-prd 'My Project'")
    print()
    print("  # List expansion packs")
    print("  ./bmad list-expansion-packs")
    print()
    print("  # Install an expansion pack")
    print("  ./bmad install-pack bmad-creative-writing")
    print()
    print("  # Get service statistics")
    print("  ./bmad stats")
    print()
    print("  # Show local tool registry")
    print("  ./bmad local-tool-registry")
    
    return True


if __name__ == "__main__":
    success = setup_bmad_cli()
    sys.exit(0 if success else 1)
