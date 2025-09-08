Title: cflow-provider-aws

Summary: Manage optional AWS MCP profile and MCP servers (off by default).

Usage:

```bash
# Write optional profile and MCP rules into .cursor/rules/
uv run cflow-provider-aws write-profile
uv run cflow-provider-aws write-mcp

# Merge AWS MCP servers into .cursor/mcp.json (idempotent)
AWS_PROFILE=default uv run cflow-provider-aws activate

# Run agent with aws profile (behavior is same as quick unless customized)
uv run cflow-agent-loop --profile aws --max-iter 1 --json
```

Notes:
- Requires AWS credentials via `AWS_PROFILE` or `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`.
- This is optional; defaults remain provider-agnostic.

