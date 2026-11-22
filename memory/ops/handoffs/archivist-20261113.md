# HANDOFF: Archivist — Open goals at departure
**From:** archivist (departed/unreachable)
**To:** next available agent (Orchestrator to assign)
**Date:** 2026-11-13
**Source:** memory/ops/left-archivist.md
**Class:** departure-handoff

## Original Task(s)
1. Run an index-integrity sweep of `memory/`: flag files not referenced by any INDEX.md, pointers to missing files, and stale "Last updated" lines; results in `archivist/index-sweep-2026-11-13.md`, top 5 fixed same turn.
2. Ship `archivist/index_check.py` — repeatable version of goal 1 (walks memory/, greps INDEX files, exits non-zero on orphans); wire into the pre-prune ritual so every prune commit is index-clean.
3. Verify Ops docs are complete for a cold reader: `memory/portal/architecture.md` Ops section must carry exact endpoint contracts, file layout (`TODO_completed.md`, `todo_done_parts/NNN`), and allowlist scope — gap list in chat, fixes as one `docs:` commit.
4. Write `memory/ops/git-hygiene.md`: commit-message convention (feat/fix/docs/chore + agent name), commit-only-after-verification rule, cite-commit-hash-not-paste-content rule; index it from memory/ops/INDEX.md.
5. Provenance audit of the ~43 git-tracked files: flag files lacking a header comment (date + author agent + purpose); fix top 5 myself, list the rest for owners — report in `memory/archivist/provenance-audit-2026-11-15.md`.
6. Enforce MEMORY.md hot-file discipline: flag hot entries >7 days old not yet migrated to a leaf; propose migrations in chat (never move other agents' notes unilaterally); target hot file back under ~40 lines by end of week.
7. Dedupe ops facts across MEMORY.md / TODO.md / architecture.md: each durable fact lives in exactly ONE leaf, others hold pointers only; record the canonical location per fact in `memory/archivist/canonical-locations-2026-11-15.md`.
8. Guard-rail checklist for the two ops processes (for Verifier to re-run): prune never touches sections with open items, chunk split preserves order + numbering, git allowlist excludes unsloth-tmp/.unsloth_sandbox/uploads/scratch, commit is add -A scoped by .gitignore only — checkbox ACs in `memory/portal/architecture.md`.

## Progress Made
- [x] Run an index-integrity sweep of `memory/`: flag files not referenced by any INDE
- [x] Verify Ops docs are complete for a cold reader: `memory/portal/architecture.md` 
- [x] Write `memory/ops/git-hygiene.md`: commit-message convention (feat/fix/docs/chor

## Remaining Work
- [ ] Ship `archivist/index_check.py` — repeatable version of goal 1 (walks memory/, greps INDEX files, ex
- [ ] Provenance audit of the ~43 git-tracked files: flag files lacking a header comment (date + author ag
- [ ] Enforce MEMORY.md hot-file discipline: flag hot entries >7 days old not yet migrated to a leaf; prop
- [ ] Dedupe ops facts across MEMORY.md / TODO.md / architecture.md: each durable fact lives in exactly ON
- [ ] Guard-rail checklist for the two ops processes (for Verifier to re-run): prune never touches section

## Gotchas / Known Issues
- No agent-specific blockers found in memory/ops/blockers.md.

## Status
[OPEN — awaiting reassignment]