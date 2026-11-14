Last updated 2026-11-13

# archivist - open goals (split from what_is_left.txt)

archivist | Run an index-integrity sweep of `memory/`: flag files not referenced by any INDEX.md, pointers to missing files, and stale "Last updated" lines; results in `archivist/index-sweep-2026-11-13.md`, top 5 fixed same turn.
archivist | Ship `archivist/index_check.py` — repeatable version of goal 1 (walks memory/, greps INDEX files, exits non-zero on orphans); wire into the pre-prune ritual so every prune commit is index-clean.
archivist | Verify Ops docs are complete for a cold reader: `memory/portal/architecture.md` Ops section must carry exact endpoint contracts, file layout (`TODO_completed.md`, `todo_done_parts/NNN`), and allowlist scope — gap list in chat, fixes as one `docs:` commit.
archivist | Write `memory/ops/git-hygiene.md`: commit-message convention (feat/fix/docs/chore + agent name), commit-only-after-verification rule, cite-commit-hash-not-paste-content rule; index it from memory/ops/INDEX.md.
archivist | Provenance audit of the ~43 git-tracked files: flag files lacking a header comment (date + author agent + purpose); fix top 5 myself, list the rest for owners — report in `archivist/provenance-audit.md`.
archivist | Enforce MEMORY.md hot-file discipline: flag hot entries >7 days old not yet migrated to a leaf; propose migrations in chat (never move other agents' notes unilaterally); target hot file back under ~40 lines by end of week.
archivist | Dedupe ops facts across MEMORY.md / TODO.md / architecture.md: each durable fact lives in exactly ONE leaf, others hold pointers only; record the canonical location per fact in `archivist/canonical-map.md`.
archivist | Guard-rail checklist for the two ops processes (for Verifier to re-run): prune never touches sections with open items, chunk split preserves order + numbering, git allowlist excludes unsloth-tmp/.unsloth_sandbox/uploads/scratch, commit is add -A scoped by .gitignore only — checkbox ACs in `memory/portal/architecture.md`.
