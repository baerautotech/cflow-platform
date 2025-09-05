Title: cflow-desktop-notify

Description: Minimal, optional desktop notification bridge (macOS only). Disabled by default.

Usage:

```
CFLOW_DESKTOP_NOTIFICATIONS=1 uv run cflow-desktop-notify --title "CFlow" --subtitle "Tests" "Suite completed green"
```

Notes:
- Requires macOS. Uses `osascript display notification`.
- Gate: Off by default. Set `CFLOW_DESKTOP_NOTIFICATIONS=1` to enable.
- Scope: Notification only; no file/system controls.


