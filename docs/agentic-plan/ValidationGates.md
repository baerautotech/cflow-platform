## Validation Gates

- [x] Gate A: 1.1 + 1.3 pass; pytest runner + parser validated
- [ ] Gate B: 1.2 e2e: fix seeded failing test via minimal edit + lint + re‑run → green
- [ ] Gate C: 2.x reasoning: bounded SRP plans with success checks
- [ ] Gate D: 3.x sandbox: no network; limits enforced; policy tests pass
- [ ] Gate E: Docs/search integration: Context7 + internet search wired; sources shown
- [ ] Gate F: Docs complete; pre‑commit green; telemetry opt‑in with clear defaults

- [ ] Gate P: Provider configured for Cerebral Server cluster; local fallback validated
- [ ] Gate M: Memory checkpoints created; iteration roll‑forward after restart
- [ ] Gate RAG: Cursor artifacts mirrored into CerebralMemory; RAG lookups return latest versions
- [ ] Gate VEC: Apple Silicon MPS embedder used locally; vectors stored in Chroma + pgvector; model/dims recorded
- [ ] Gate RDB: Relational retrieval via Supabase; referential integrity and indices verified; realtime healthy
- [ ] Gate R: Restart budgets enforced; structured restart reasons emitted; no infinite loops
- [ ] Gate Cmt: Commits only when hooks pass and tests are green; disabled by default

Reference: `https://martinfowler.com/articles/build-own-coding-agent.html?utm_source=tldrai`

