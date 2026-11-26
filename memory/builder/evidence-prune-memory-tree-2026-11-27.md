# EVIDENCE — Builder ops contribution: Memory Tree Pruning (2026-11-27)

**Type:** Ops improvement (option b from auto-loop options)
**Problem:** size_guard_report FAILing for weeks; tree at 1.3 GB vs 5 MB limit.

**Deliverables:**
1. `memory/ops/memory_tree_pruning.md` — strategy doc with safe-to-prune categories table
2. `memory/ops/prune_memory_tree.py` — executable pruning script (dry-run default, --apply to delete)

**Dry-run result (2026-11-27):**
- 13 files identified as safely prunable
- 352.1 MB reclaimable (26.7% of total tree)
- Top items: fleet-backup tarballs (278 MB, 6-7d old), dedup-report JSONs (44 MB, 6-7d old), crashpad dumps (30 MB)
- Projected size after prune: 966 MB (still over target due to MinGit, kline data, node_modules — those need manual decisions)

**Next steps for Mechanic/Orchestrator:**
- Run `python memory/ops/prune_memory_tree.py --apply` to reclaim the 352 MB
- Decide on dcabots kline data (110 MB) and AstroCalendar node_modules (~50 MB)
- Register schtask for periodic pruning (every 6h)
