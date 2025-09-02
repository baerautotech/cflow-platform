## Feedback Loops and Reflection

- Parse failures; summarize root causes
- After edits, compare outcomes vs. plan success checks
- Record lessons learned and constraints updates in memory

### Structured Problem Solving

- Maintain a concise hypothesis list tied to failing tests
- For each plan step, define: intended change, expected effect, success signal
- If the same failures persist across N iterations, trigger restart with trimmed context

### Checkpointing

- Write per-iteration checkpoints to `.cerebraflow/progress/iteration_<n>.mdc`
- Store episodic entries via CerebralMemory with rich metadata (artifact_path, iteration, task_id)

Reference: `https://martinfowler.com/articles/build-own-coding-agent.html?utm_source=tldrai`

