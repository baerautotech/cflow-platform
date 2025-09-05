from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any


def _has_aws_env_credentials() -> bool:
    access_key = (os.getenv("AWS_ACCESS_KEY_ID") or "").strip()
    secret_key = (os.getenv("AWS_SECRET_ACCESS_KEY") or "").strip()
    session_token = (os.getenv("AWS_SESSION_TOKEN") or "").strip()
    profile = (os.getenv("AWS_PROFILE") or "").strip()
    # Accept either explicit key pair, or a named/default profile which we will treat as available
    if access_key and secret_key:
        return True
    if profile:
        return True
    # Fallback: presence of ~/.aws/credentials file with at least one profile stanza
    try:
        creds = Path.home() / ".aws" / "credentials"
        if creds.exists() and creds.is_file():
            content = creds.read_text(encoding="utf-8", errors="ignore")
            # Very light heuristic: look for a bracketed profile header
            return "[" in content and "]" in content
    except Exception:
        pass
    return False


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_aws_profile(repo_root: Path) -> Path:
    """Create an optional Cursor instruction profile named 'aws' (off by default)."""
    data: Dict[str, Any] = {
        "name": "aws",
        "description": "Optional AWS profile (non-default). Enables cloud MCPs when explicitly activated.",
        # Policies are advisory; core loop remains identical to 'quick' unless you customize
        "policies": {
            "minimal_edits": True,
            "fail_closed_lint": True,
            "sandbox_python": True,
            "cloud_mcp": True,
            "notes": "This profile is disabled by default. Activate AWS MCP separately.",
        },
    }
    out_path = repo_root / ".cursor" / "rules" / "aws.profile.json"
    _write_json(out_path, data)
    return out_path


def write_aws_mcp_rule(repo_root: Path) -> Path:
    """Create a rules-scoped MCP config for AWS-related MCP servers (not auto-activated)."""
    # We intentionally do not modify .cursor/mcp.json automatically; activation is an explicit step
    # The command/args here assume you will install the corresponding MCP servers yourself.
    # They are kept under rules/ to remain off by default.
    data: Dict[str, Any] = {
        "mcpServers": {
            # Example: AWS Docs MCP (optional). Requires npm package install by the user.
            "aws-docs": {
                "command": "npx",
                "args": ["-y", "@aws-labs/mcp-aws-docs@latest"],
                "env": {
                    # Pass-through of common AWS env vars when present
                    "AWS_PROFILE": os.getenv("AWS_PROFILE", ""),
                    "AWS_REGION": os.getenv("AWS_REGION", ""),
                    "AWS_DEFAULT_REGION": os.getenv("AWS_DEFAULT_REGION", ""),
                },
            },
            # Example: AWS CLI MCP bridge (optional). Requires npm package install by the user.
            "aws-cli": {
                "command": "npx",
                "args": ["-y", "@aws-labs/mcp-aws-cli@latest"],
                "env": {
                    "AWS_PROFILE": os.getenv("AWS_PROFILE", ""),
                    "AWS_REGION": os.getenv("AWS_REGION", ""),
                    "AWS_DEFAULT_REGION": os.getenv("AWS_DEFAULT_REGION", ""),
                },
            },
        }
    }
    out_path = repo_root / ".cursor" / "rules" / "aws.mcp.json"
    _write_json(out_path, data)
    return out_path


def activate_aws_mcp(repo_root: Path) -> Dict[str, Any]:
    """Merge rules/aws.mcp.json into .cursor/mcp.json if credentials exist; remain idempotent."""
    # Gate by credentials
    if not _has_aws_env_credentials():
        return {
            "success": False,
            "error": "aws_credentials_missing",
            "message": "AWS credentials/profile not detected. Set AWS_PROFILE or AWS_ACCESS_KEY_ID/SECRET first.",
        }
    rules_mcp = repo_root / ".cursor" / "rules" / "aws.mcp.json"
    if not rules_mcp.exists():
        write_aws_mcp_rule(repo_root)
    try:
        rules_data = json.loads(rules_mcp.read_text(encoding="utf-8"))
        if not isinstance(rules_data, dict):
            raise ValueError("Invalid aws.mcp.json structure")
    except Exception as e:
        return {"success": False, "error": "invalid_rules_mcp", "message": str(e)}

    target_path = repo_root / ".cursor" / "mcp.json"
    try:
        if target_path.exists():
            base_data = json.loads(target_path.read_text(encoding="utf-8"))
            if not isinstance(base_data, dict):
                base_data = {}
        else:
            base_data = {}
    except Exception:
        base_data = {}

    base_servers = dict((base_data.get("mcpServers") or {}))
    new_servers = dict((rules_data.get("mcpServers") or {}))
    # Shallow merge by server key; do not overwrite existing by default
    for name, cfg in new_servers.items():
        if name not in base_servers:
            base_servers[name] = cfg
    out_data = {**base_data, "mcpServers": base_servers}
    _write_json(target_path, out_data)
    return {"success": True, "written": str(target_path), "servers": list(new_servers.keys())}


def cli() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Manage optional AWS provider profile and MCP config (off by default)")
    parser.add_argument("command", choices=["write-profile", "write-mcp", "activate"], help="Operation to perform")
    parser.add_argument("--project-root", dest="project_root", default=str(Path.cwd()), help="Project root (defaults to CWD)")
    args = parser.parse_args()

    root = Path(args.project_root)
    if args.command == "write-profile":
        out = write_aws_profile(root)
        print(json.dumps({"success": True, "written": str(out)}))
        return 0
    if args.command == "write-mcp":
        out = write_aws_mcp_rule(root)
        print(json.dumps({"success": True, "written": str(out)}))
        return 0
    if args.command == "activate":
        res = activate_aws_mcp(root)
        print(json.dumps(res))
        return 0 if res.get("success") else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(cli())


