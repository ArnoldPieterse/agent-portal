# Orphan-folder audit — root `archivist/` (r42, 2026-11-14, Archivist)
Method: full listing + md5 of root `archivist/` vs `memory/archivist/`; grep of every INDEX for references; live run of both goal-2 checkers and the copied provenance script.

## Findings
- **F1 (established)** — Root-level `archivist/` holds 7 files, none present under `memory/archivist/`: REPAIR_2026-11-13.md (4715 B / e982110a), f1-index-patch-20261113.md (2040 B / f3a31650), fleet-md5-discrepancy-note-20261113.md (2610 B / 4d71c6e7), goals-2026-11-13.md (2754 B / efe6cc4e), index-integrity-2026-11-14.md (3711 B / da18d2f6), index_check.py (4426 B / 7dec653f), provenance_audit.py (3104 B / 289b7ee2).
- **F2 (inference, flagged)** — The folder is outside every governance surface: the root INDEX FILE ACCESS rule lists only TODO.md / MEMORY.md / memory/ / agents.json / agent_portal.py as synced; git allowlist and index_check.py both scope to memory/. So these 7 files are invisible to mirror, git, and the integrity sweep. (Scope claim inferred from the FILE ACCESS rule + checker code, not from observing a sync event.)
- **F3 (established)** — Root `memory/INDEX.md` has NO sub-index line for `memory/archivist/` (grep 0 hits) → the whole module is unreachable from the root dictionary.
- **F4 (established)** — Module INDEX checker pointer reads `-> archivist/index_check.py`, which repo-root-relative resolves to the STRAY folder, not `memory/archivist/index_check.py`. Dangling on any seat lacking the stray folder.
- **F5 (established; supersession = inference)** — Two divergent goal-2 checkers exist: stray 4426 B / 7dec653f (mtime 11-13 18:53; ORPHANS/BROKEN/STALE, token regex, same-dir resolution) vs canonical `memory/archivist/index_check.py` 2772 B / e5862568 (mtime 11-13 19:18; DANGLING/ORPHANS/STALE arrow parser). Canonical v1 live run this round: exit 1, 10 "dangling" incl. obvious parser false positives (`-> pointer` prose token; unresolved `../architecture.md`, `bugs/*.md` relatives), 5 stale INDEX dates. mtime alone does NOT decide supersession (canonical is 25 min newer but feature-leaner) → **adjudicate on White** (run both against canonical tree, keep/merge winner). No seat-side overwrite performed.
- **F6 (established)** — `goals-2026-11-13.md` is a non-canonical drop-copy of my 10 posted goals; canonical = `memory/goals/archivist.md` (2470 B / 26774969) per root INDEX.
- **F7 (established content; status = gap)** — REPAIR / F1-patch / F2-note are self-labelled STAGED patches. Which blocks actually landed on White is NOT verifiable from this seat → Verifier/Orchestrator confirm before the stray folder is deleted.

## Actions taken this round (seat-safe: new files only, no existing-file edits)
- Copied 5 unique .md files into `memory/archivist/` byte-exact (md5 re-verified after copy, all OK).
- Copied `provenance_audit.py` with ONE intended line fix (`ROOT = parent.parent` → `parents[2]`) so it runs from its new home; live run: exit 1, 262 candidates, 44 missing headers (goal-6 baseline, 218 OK). New md5 d7df4e2b.
- Did NOT copy stray `index_check.py` (F5 divergence) and did NOT delete root `archivist/` (destructive → Arnold's bundle after White confirms copies).

## Staged apply-bundle items (verbatim lines in `memory/archivist/index-pointer-batch-r42.md`)
1. Root INDEX: add archivist sub-index line (F3).
2. Module INDEX: 6 entries for the canonicalized files (F1/F6 coverage).
3. Adjudicate checkers v1/v2 on White, then fix module pointer to the winner's path (F4/F5).
4. Delete root `archivist/` (7 files) once White confirms copies byte-exact (F1/F7).

## Gaps (honest)
- F7 block-level apply status unknown from this seat.
- Whether the stray folder also exists in other seats' sandboxes is not verifiable here (portal serves both roots by relative path, so likely shared; mirror scope is per-file either way).
