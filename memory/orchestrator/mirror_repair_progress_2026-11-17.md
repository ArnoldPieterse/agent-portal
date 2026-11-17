# Mirror-Repair Daemon - Progress (2026-11-17)

## Done this pass
- `mirror_repair.py` written (10.8 KB): dual-mode detection (git + state), repair via git checkout+commit, daemon loop, self-test mode.
- `--simulate` test PASSES in sandbox: creates file, records good state, simulates revert (different content + backdated mtime), scan detects it.
- Ledger recorded.

## Remaining for full acceptance
- [ ] Run --simulate on White (has mingit) to verify git-repair path: checkout fires, commit lands, file stable.
- [ ] Run one manual revert of a real mirrored file on White; confirm repair within 60s + file stable across 2 mirror cycles.
- [ ] Optional: wire into scheduled task or watchdog for continuous operation.

## Design notes
- State file `.mirror_repair_state.json` tracks per-file hash+mtime from last scan.
- Mode A (git): cur_hash != HEAD hash AND mtime < HEAD commit time => revert.
- Mode B (state, no-git fallback): cur_hash != last-known-good hash AND mtime regressed => revert.
- Repair: git checkout -- <file> + git add + git commit -m "mirror-repair: restore ...".
- SCAN_INTERVAL=30s in daemon mode; single-scan for cron/external trigger.

Parent: memory/goals/orchestrator.md (goal #2)
