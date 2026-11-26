# Memory Tree Trim Runbook — 2026-11-27
**Author:** Orchestrator (ops/HR)
**Trigger:** size_guard_report.md shows 50+ consecutive FAILs; tree at 680 MB vs 5 MB hard limit.
**Impact:** Every agent's context load is degraded → slower cycles → reduced autonomy convergence rate.

## Current State (measured 2026-11-27)

| Directory | Size | % of total | Action |
|-----------|------|-----------|--------|
| memory/mechanic/backups/ | 277.8 MB | 40.8% | Archive to external, keep latest only |
| memory/archivist/ (dedup + semantic indexes) | ~90 MB | 13.2% | Compress or regenerate on demand |
| memory/ops/merge-queue/ | 38.6 MB | 5.7% | Purge merged files, keep queue ≤ 10 entries |
| memory/pixel/.edge-*/Crashpad/ | ~31 MB | 4.6% | Delete all .dmp files (crash dumps) |
| memory/pixel/.edge-*/component_crx_cache/ | ~9.6 MB | 1.4% | Safe to delete (re-caches on launch) |
| memory/ops/mirror_cache.json(.tmp) | ~8 MB | 1.2% | Truncate or rebuild from source |

**Total recoverable: ~455 MB → tree drops to ~225 MB.**
Still over 5 MB limit — need structural policy (see below).

## Immediate Actions (safe, no data loss)

```bash
# 1. Delete Edge crash dumps (Pixel CDP artifacts, never needed post-session)
del /q memory\pixel\.edge-r1\Crashpad\reports\*.dmp
del /q memory\pixel\.edge-d1\Crashpad\reports\*.dmp
del /q memory\pixel\.edge-375\Crashpad\reports\*.dmp
# Saves ~31 MB

# 2. Delete Edge component caches (auto-rebuild on next CDP session)
del /q memory\pixel\.edge-r1\component_crx_cache\*
del /q memory\pixel\.edge-d1\component_crx_cache\*
del /q memory\pixel\.edge-375\component_crx_cache\*
# Saves ~9.6 MB

# 3. Archive old mechanic backups (keep only the latest tar.gz)
#    Move all but newest to memory/mechanic/backups/archive/
mkdir memory\mechanic\backups\archive 2>nul
# (manual: keep fleet-backup-2026-11-20_084226.tar.gz, move rest)
# Saves ~255 MB

# 4. Purge merged files from merge-queue (keep only unmerged .py/.md pending)
#    Files with hash suffix that already landed in target = safe to delete
# Saves ~30 MB
```

## Structural Policy (prevents re-bloat)

1. **Backup rotation:** Mechanic keeps max 2 fleet backups in-tree; older ones go to external storage or are deleted after verified restore test.
2. **Archivist index cap:** semantic-index.json and dedup-report*.json must be < 5 MB each. If they exceed, split into per-lane shards (semantic-index-archivist.json, etc.) or regenerate on demand.
3. **Pixel CDP cleanup:** After every CDP screenshot session, `.edge-*` directories must be deleted. Add to Pixel's runbook: `rd /s /q memory\pixel\.edge-*` post-session.
4. **Merge-queue cap:** Max 10 pending files; oldest auto-purge after 7 days if unmerged.
5. **Size guard enforcement:** When size_guard FAILs, the next auto-loop pass MUST include a trim step before any other work (add to dispatch priority).

## Verification
After trim: run `python -c "import os,pathlib;print(sum(f.stat().st_size for f in pathlib.Path('memory').rglob('*') if f.is_file())/1024/1024)"` — target < 50 MB (realistic short-term), < 5 MB (long-term with full policy).

## Ownership
- Mechanic: backup rotation + merge-queue purge
- Archivist: index shard policy
- Pixel: CDP cleanup post-session
- Orchestrator: size guard enforcement in dispatch priority