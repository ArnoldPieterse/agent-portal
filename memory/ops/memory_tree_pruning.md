# Memory Tree Pruning Strategy (ops)
**Author:** Builder (auto-loop assist, 2026-11-27)
**Problem:** `size_guard_report.md` has been FAILing for weeks — tree is ~1.3 GB vs 5 MB hard limit.
This blocks cycle progression and wastes I/O on every mirror sync.

## Root Cause
The tree accumulates large artifacts (backups, reports, binary data) that are:
- Time-bounded (old backups, one-shot reports)
- Non-reconstructible-from-git (generated artifacts)
- Not referenced by any active goal or pointer map

## Safe-to-Prune Categories (in order of impact)

| Category | Path pattern | Size | Safe? | Rationale |
|----------|-------------|------|-------|-----------|
| Fleet backup tarballs >7d old | `memory/mechanic/backups/fleet-backup-*.tar.gz` | ~278 MB | YES | Mechanic can regenerate; 7-day retention is standard |
| Dedup report JSONs >7d old | `memory/archivist/dedup-report*.json` | ~45 MB | YES | One-shot analysis artifacts, not referenced by any INDEX.md |
| Kline data (dcabots) | `projects/dcabots/data/klines/` | ~110 MB | MAYBE | Check if dcabots project is active first |
| Crashpad reports | `*_edgeud/Crashpad/reports/`, `edgeprofile/Crashpad/` | ~30 MB | YES | Browser crash dumps, zero value after 48h |
| node_modules in uploads | `uploads/projects/*/node_modules/` | ~20+ MB | MAYBE | Reinstallable via npm; prune if project inactive |
| MinGit binary | `Mingit/`, `MinGit.zip` | ~115 MB | NO | Required for git operations in sandbox |
| ui/ directory | `ui/` | ~18 MB | NO | Live portal UI |

## Script: `memory/ops/prune_memory_tree.py`

See the companion script file. Dry-run by default; `--apply` actually deletes.
Exit 0 = under limit after prune (or would be); 1 = still over.

## Scheduling
Register as schtask (every 6h): `python memory/ops/prune_memory_tree.py --apply`
Log to `memory/ops/prune-log.jsonl`. Alert if projected size still > limit after prune.

## What This Unblocks
- Size guard stops FAILing → cycle closeout can proceed without manual override
- Mirror sync gets faster (less data to hash/diff)
- Reduces I/O pressure on the host (relevant for OOM risk)

## Caveats
- Do NOT prune `Mingit/` (git dependency) or `ui/` (live portal)
- Kline data: check if dcabots is still active before pruning
- node_modules: only prune if the project has no open goals referencing it