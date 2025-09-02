Title: cflow-sync

Description: Manage the CerebraFlow sync daemon and utilities.

Subcommands:

```
uv run cflow-sync start --project-root $PWD   # start daemon
uv run cflow-sync status                      # show daemon + parity report
uv run cflow-sync stop                        # stop daemon
uv run cflow-sync install-agent --project-root $PWD  # install LaunchAgents (auto-start/KeepAlive/watch)
uv run cflow-sync uninstall-agent                    # uninstall LaunchAgents
```

Notes:
- Agent plist uses osascript notifications on restart failures.

