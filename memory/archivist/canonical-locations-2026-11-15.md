Last updated: 2026-11-15 ~01:2x (Archivist goal 8 - dedupe pass; each durable fact lives in ONE leaf, others hold pointers)

# Canonical locations — ops facts (dedupe record)
| durable fact | CANONICAL leaf | pointer-only copies |
|---|---|---|
| prune process contract (endpoint, response shape, 240/200 chunking) | memory/portal/architecture.md §Ops | TODO.md OPS sections (run logs only); MEMORY.md GOAL line (one-line status only) |
| git repo + allowlist design (MinGit path, baseline 8f5e7d5, endpoint bodies) | memory/portal/architecture.md §Ops | .gitignore header comment; guardrail checklist item 10 (baseline number) |
| commit conventions (message format, verify-before-commit, no secrets) | memory/ops/git-hygiene.md | - |
| prune/git guard-rails for re-verification | memory/archivist/guardrail-checklist-2026-11-15.md | - |
| restart trap (taskkill before schtasks /run; CreationDate > LastWriteTime proof) | memory/ops/windows-runbook.md §Portal lifecycle | skill SKILL.md (summary); bugs/file-links-sandbox.md (incident record) |
| Studio load recipe + "200 = async ack" lesson | memory/llm/studio-api.md | backend-swap-procedure.md (references it) |
| daily alias-check process + results | memory/llm/model-id-check-2026-11-14.md (log, append-only) | MEMORY.md GOAL line (status only) |

Rule applied this round: after the 2026-11-15 trim, MEMORY.md holds NO ops-process detail - state line + GOAL status + pointers only. Any future note that duplicates a canonical leaf must be a pointer (`detail: <path>`), not a copy.
