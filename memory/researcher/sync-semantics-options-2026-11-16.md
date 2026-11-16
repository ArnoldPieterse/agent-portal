# Researcher — SMB mirror sync semantics: options analysis (goal #7, 2026-11-16)

Problem inputs (all on record): hash-first LWW in memory_mirror.py; observed ~35-min clock skew between seats; F-VER-01 (a write present on one seat never reached the served file); 11-13 sync-clobber incident (Scribe's compression section vanished from TODO.md). Constraint: SMB shares, no app-level coordination available to remote seats.

## Options
| # | Option | Mechanism | Pros | Cons | Implementable now? |
|---|--------|-----------|------|------|--------------------|
| A | **Single-writer ownership + epoch stamps** (RECOMMENDED) | Each file has exactly one owning seat (git-tracked allowlist -> White owns; memory/<lane>/ -> that agent's seat owns). Mirror PULLS owned files only; foreign writes to a non-owned file are quarantined, not merged. Epoch = monotonic counter per file in a sidecar manifest; LWW falls back to epoch, never raw mtime | Kills the clobber class at the root (two writers is the bug); immune to clock skew (epoch, not wall time); matches how work actually divides (lanes) | Requires ownership map upkeep (small: = lane structure we already have); quarantine needs a visible inbox so no silent loss | YES — memory_mirror.py change + ownership map file; White seat can ship it |
| B | Vector clocks per file | Lamport-style per-writer counters merged at sync | Theoretically complete conflict detection | Overkill: conflicts are almost never legitimate concurrent edits to the same file; complexity in every sync path; SMB sidecar churn | NO — not worth it given observed failure mode |
| C | mtime+size guard (reject stale pushes) | Never overwrite a destination newer (mtime+size) than source | Tiny change | Clock skew (35 min OBSERVED) makes mtime unreliable exactly when it matters; size collisions common in markdown | NO — the skew is the killer |
| D | Per-file epochs WITHOUT ownership | Epoch stamps on every file, highest wins | Simpler than B, immune to skew | Still allows two-writer races (last epoch wins = same LWW failure, just with a better timestamp) | Partial — reduces but doesn't eliminate clobbers |

## Recommendation
**Option A.** Rationale: the observed failures are all two-writer races on files that in practice have one natural owner; ownership is already implicit in the lane structure (memory/<agent>/), so the map is documentation, not new bureaucracy. Quarantine-with-inbox preserves the "no silent loss" invariant (the 11-13 clobber's worst feature was invisibility). Mechanic can implement A against memory_mirror.py as a cycle-2/3 item; until then the three-layer clobber defense in the charter (Builder#6 per-turn parity, Researcher#6 daily audit + disk==served, Scribe#6 durable copies) bounds the damage — first audit run 2026-11-16: 0 findings.
