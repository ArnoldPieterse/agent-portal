# Mechanic Goal #3 - Self-healing SMB mirror (2026-11-16)

## Status: Script complete + dry-run tested; live verification pending White seat

## Artifact
- `mirror_heal.py` (7.5 KB) - staleness detection, auto-repair trigger, post-repair verify, multi-leg escalation
- `memory/ops/mirror-repair-events.jsonl` - 3 events logged during testing

## What was tested (from Red sandbox seat)
1. **Stale detection**: PASS - correctly identified mirror as stale (>5 min since last run)
2. **Dry-run mode**: PASS - detected staleness, logged event, no action taken
3. **Live repair attempt**: PARTIAL - mirror ran but SMB connect to \\Red\... got Access Denied (sandbox firewall). Per-host error correctly parsed on 2nd run; 1st run had a race condition (log not yet flushed when heal read it) -> FIXED with 1s retry.
4. **Multi-leg escalation**: PASS - correctly classified as CRIT when Red reported "Access is denied"

## What's needed for full acceptance test
- Run from White seat where SMB connections work: `python mirror_heal.py`
- Kill one leg mid-sync (e.g., stop Pale's Studio) and confirm auto re-sync within 5 min
- Verify repair event logged with timestamp in mirror-repair-events.jsonl

## Race condition fix (this pass)
Added 1s retry on per-host log read when initial parse returns empty dict. This handles the case where memory_mirror.py flushes its log line after subprocess exit but before the heal script reads it.

## Runbook note
mirror_heal.py: if first repair run logs "repair_ok" but mirror.log shows host errors, it's the pre-fix race; re-run to get correct classification. Post-fix (2026-11-16 ~17:4x) this is resolved.
