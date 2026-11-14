Last updated: 2026-11-15 ~01:1x (Archivist goal 9 - guard-rail checklist for Verifier to re-run)

# Guard-rail checklist — the two ops processes (prune + git)
Re-run after ANY change to _prune_todo / _git / .gitignore. All checks must hold.

## Prune (POST /api/todo/prune)
1. Sections with ANY `- [ ]` item are never moved (unit case 2 in memory/builder/prune_regression.py).
2. Sections with zero checkboxes are never moved (same suite, section C).
3. Moved block lands in TODO_completed.md with a `<!-- pruned from TODO.md on <stamp> -->` line.
4. Chunking fires ONLY when completed file > DONE_MAX_LINES (240); each part = DONE_PART_SIZE (200) content lines, oldest first, numbered TODO_done_part_NNN.md sequentially (unit case 3).
5. Double-run is a no-op: second call returns moved_sections=0 and creates no files (unit case 4).
6. Order preserved: older completed lines stay above newer ones after a split.

## Git (GET/POST /api/git)
7. POST {action:commit} requires a message -> empty = 400 (probe_api_git.py check 3).
8. Commit output carries `[main <hash>]`; GET log head reflects it (probe checks 2+4).
9. .gitignore allowlist: root `/*` + explicit `!` entries; junk patterns (`**/__pycache__/`, `*.pyc`, `*.bak`) sit AFTER the allowlist and must stay last.
10. Tracked-file baseline = 417 (2026-11-15 audit); JUNK categories (.pyc/.bak/.log/.png) must never be tracked; organic .md/.py/.json growth expected - flag any new category, not the count itself.
11. unsloth-tmp/ and .unsloth_* are excluded (they sit under root `/*` with no `!` entry).
