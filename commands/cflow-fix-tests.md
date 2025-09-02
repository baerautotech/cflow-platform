---
name: Fix tests with cflow
command: |
  cflow-agent-loop --profile quick --max-iter 3
description: Run the autonomous loop to fix failing tests with minimal edits
---