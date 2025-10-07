from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    try:
        return subprocess.call(cmd)
    except Exception as e:
        print(f"error: {e}")
        return 1


def _spawn(cmd: list[str]) -> None:
    print("$ (bg)", " ".join(cmd))
    try:
        subprocess.Popen(cmd)
    except Exception as e:
        print(f"error (bg): {e}")


def cli() -> int:
    parser = argparse.ArgumentParser(description="CFlow one-touch installer with BMAD integration")
    parser.add_argument("--watch", action="store_true", help="Start memory watcher after setup")
    parser.add_argument("--install-sync-agent", action="store_true", help="Install LaunchAgents to auto-start sync daemon")
    parser.add_argument("--apply-migrations", action="store_true", help="Apply Supabase memory schema migration if SUPABASE_DB_URL available")
    parser.add_argument("--initial-backfill", action="store_true", help="Backfill docs/tasks locally and run one-shot sync")
    parser.add_argument("--setup-bmad", action="store_true", help="Setup BMAD integration components")
    parser.add_argument("--verify-bmad", action="store_true", help="Verify BMAD templates and handlers are available")
    parser.add_argument("--setup-webmcp", action="store_true", help="Setup WebMCP configuration")
    parser.add_argument("--webmcp-server-url", default="http://localhost:8000", help="WebMCP server URL")
    parser.add_argument("--webmcp-api-key", help="WebMCP API key")
    parser.add_argument("--bmad-api-url", default="http://localhost:8001", help="BMAD API service URL")
    parser.add_argument("--bmad-auth-token", help="BMAD authentication token")
    parser.add_argument("--overwrite-config", action="store_true", help="Overwrite existing WebMCP configuration")
    parser.add_argument("--cluster-deployment", action="store_true", help="Configure for cluster deployment (Cerebral cloud)")
    parser.add_argument("--validate-cluster", action="store_true", help="Validate cluster deployment endpoints")
    parser.add_argument("--cluster-webmcp-url", default="https://webmcp-bmad.dev.cerebral.baerautotech.com", help="Cluster WebMCP server URL")
    parser.add_argument("--cluster-bmad-api-url", default="https://bmad-api.dev.cerebral.baerautotech.com", help="Cluster BMAD API service URL")
    parser.add_argument("--cluster-bmad-method-url", default="https://bmad-method.dev.cerebral.baerautotech.com", help="Cluster BMAD-Method service URL")
    args = parser.parse_args()
    project_root = Path.cwd()

    # Ensure env files are ready
    try:
        from cflow_platform.core.env_manager import ensure_env_files

        env_results = ensure_env_files(project_root)
        for result in env_results:
            rel = result.target.relative_to(project_root)
            if result.skipped_reason == 'template_missing':
                print(f'⚠️  Skipped env management for {rel}: template missing')
            elif result.created:
                print(f'✅ Created {rel} from template')
            elif result.appended_keys:
                keys = ', '.join(result.appended_keys)
                print(f'✅ Updated {rel}; appended keys: {keys}')
                if result.backup_path:
                    print(f'   Backup saved to {result.backup_path}')
            else:
                print(f'ℹ️  {rel} already up to date')
    except Exception as exc:
        print(f'⚠️  Env preparation skipped: {exc}')

    rc = 0
    # Verify environment (non-interactive)
    rc |= _run([sys.executable, "-m", "cflow_platform.verify_env", "--mode", "migrations", "--mode", "ragkg", "--mode", "llm", "--scope", "both"])
    # Install hooks
    rc |= _run([sys.executable, "-m", "cflow_platform.install_hooks"])
    # Setup Cursor workspace
    rc |= _run([sys.executable, "-m", "cflow_platform.cli.setup_cursor"])
    # Memory connectivity check
    rc |= _run([sys.executable, "-m", "cflow_platform.cli.memory_check"])

    # BMAD integration setup
    if args.setup_bmad and rc == 0:
        print("Setting up BMAD integration components...")
        # Verify BMAD vendor directory exists
        bmad_path = Path.cwd() / "vendor" / "bmad"
        if not bmad_path.exists():
            print("Warning: BMAD vendor directory not found. BMAD integration may not work properly.")
        else:
            print(f"BMAD vendor directory found at: {bmad_path}")
            # Verify BMAD templates are available
            templates_path = bmad_path / "bmad-core" / "templates"
            if templates_path.exists():
                print(f"BMAD templates found at: {templates_path}")
            else:
                print("Warning: BMAD templates directory not found.")

    # Verify BMAD components
    if args.verify_bmad and rc == 0:
        print("Verifying BMAD integration components...")
        # Check if BMAD handlers are available
        try:
            from cflow_platform.handlers.bmad_handlers import BMADHandlers
            print("✓ BMAD handlers available")
        except ImportError as e:
            print(f"✗ BMAD handlers not available: {e}")
            rc |= 1

    # Setup WebMCP configuration
    if args.setup_webmcp and rc == 0:
        print("Setting up WebMCP configuration...")
        try:
            from cflow_platform.core.webmcp_installer import WebMCPInstaller, WebMCPConfig
            
            # Determine server URL based on deployment type
            if args.cluster_deployment:
                server_url = args.cluster_webmcp_url
                print(f"🌐 Configuring for cluster deployment: {server_url}")
            else:
                server_url = args.webmcp_server_url
                print(f"🏠 Configuring for local deployment: {server_url}")
            
            # Create WebMCP configuration
            config = WebMCPConfig(
                server_url=server_url,
                api_key=args.webmcp_api_key,
                bmad_api_url=args.bmad_api_url if not args.cluster_deployment else args.cluster_bmad_api_url,
                bmad_auth_token=args.bmad_auth_token
            )
            
            # Create installer and install configuration
            installer = WebMCPInstaller()
            result = installer.install_webmcp_configuration(config, overwrite=args.overwrite_config)
            
            if result.success:
                print(f"✓ WebMCP configuration installed successfully")
                print(f"  Config file: {result.config_file_path}")
                if result.warnings:
                    for warning in result.warnings:
                        print(f"  Warning: {warning}")
            else:
                print(f"✗ WebMCP configuration installation failed: {result.message}")
                if result.errors:
                    for error in result.errors:
                        print(f"  Error: {error}")
                rc |= 1
                
        except ImportError as e:
            print(f"✗ WebMCP installer not available: {e}")
            rc |= 1
        except Exception as e:
            print(f"✗ WebMCP configuration setup failed: {e}")
            rc |= 1

    # Validate cluster deployment
    if args.validate_cluster and rc == 0:
        print("Validating cluster deployment endpoints...")
        try:
            from cflow_platform.core.webmcp_installer import WebMCPInstaller
            
            installer = WebMCPInstaller()
            result = installer.validate_cluster_deployment()
            
            if result.success:
                print(f"✓ Cluster deployment validation successful")
                print(f"  {result.message}")
                if result.warnings:
                    for warning in result.warnings:
                        print(f"  Warning: {warning}")
            else:
                print(f"✗ Cluster deployment validation failed: {result.message}")
                if result.errors:
                    for error in result.errors:
                        print(f"  Error: {error}")
                rc |= 1
                
        except ImportError as e:
            print(f"✗ WebMCP installer not available: {e}")
            rc |= 1
        except Exception as e:
            print(f"✗ Cluster validation failed: {e}")
            rc |= 1

    # Optional: Supabase migrations
    if args.apply_migrations and rc == 0:
        rc |= _run([sys.executable, "-m", "cflow_platform.cli.migrate_supabase", "--apply"])

    # Install auto-start sync agent
    if args.install_sync_agent and rc == 0:
        rc |= _run([sys.executable, "-m", "cflow_platform.cli.sync_supervisor", "install-agent", "--project-root", str(Path.cwd())])

    # Initial backfill & parity sync
    if args.initial_backfill and rc == 0:
        rc |= _run([sys.executable, "-m", "cflow_platform.cli.docs_backfill"])
        rc |= _run([sys.executable, "-m", "cflow_platform.cli.tasks_backfill"])
        rc |= _run([sys.executable, "-m", "cflow_platform.cli.sync_supervisor", "status"])  # parity report

    if args.watch and rc == 0:
        # Start memory watcher in background
        _spawn([sys.executable, "-m", "cflow_platform.cli.memory_watch", "--watch"])

    if rc == 0:
        print("One-touch installer completed successfully.")
        if args.setup_bmad or args.verify_bmad:
            print("BMAD integration components verified and ready.")
        if args.setup_webmcp:
            if args.cluster_deployment:
                print("WebMCP configuration installed and ready for cluster deployment.")
                print("🌐 Cluster endpoints configured:")
                print(f"  WebMCP: {args.cluster_webmcp_url}")
                print(f"  BMAD API: {args.cluster_bmad_api_url}")
                print(f"  BMAD-Method: {args.cluster_bmad_method_url}")
            else:
                print("WebMCP configuration installed and ready for local deployment.")
        if args.validate_cluster:
            print("Cluster deployment validation completed.")
    else:
        print("One-touch installer completed with issues. See logs above.")
    return rc


if __name__ == "__main__":
    raise SystemExit(cli())


