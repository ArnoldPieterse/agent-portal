# Mechanic Cycle-6 Progress - 2026-11-19 auto-loop pass

## Goal 3: Sandbox HTTP Self-Probe Helper
**Status:** Script created + functional; host-side execution pending (elev.py not accessible from sandbox seat)
**Artifact:** `memory/mechanic/self_probe.py`
**Verified:** Script runs, correctly reports WinError 10013 when run from sandbox (expected behavior). 
**Remaining:** Execute via elev.py from a non-sandbox seat: `python elev.py --shell "python memory/mechanic/self_probe.py"`
**Fleet impact:** Unblocks live-HTTP acceptance for all previously egress-blocked goals.

## Goal 2: Mirror-Revert Sentinel  
**Status:** Script created + tested; detected REAL pin-drift on first run
**Artifact:** `memory/mechanic/revert_sentinel.py`
**Test result (dry-run):**
```
[REVERT DETECTED] index.html: live_sha12=95e752e795c0 expected=815d64fa70b5 backup_sha12=fdc359022109
Sentinel: ISSUES FOUND (1 pins checked)
```
**Finding:** Live index.html has drifted from the pinned sha12 in memory_mirror.py. 
Root cause analysis: Designer/Orchestrator edits to index.html (icons.js script tag, etc.) advanced the 
file content but did NOT update PIN_FILES in memory_mirror.py. The sentinel correctly flags this as a 
revert-risk state.
**Acceptance test status:** Detection = PASS. Restore step not triggered (dry-run mode + live file is 
likely the CORRECT newer version, so auto-restore would be wrong here). Full acceptance requires: 
simulate an actual revert -> sentinel detects + restores + logs. Will complete when pin is advanced 
to match current live state, then a controlled revert test can run cleanly.
**Design note:** Sentinel reads PIN_FILES from memory_mirror.py (authoritative source), uses SHA-1 first-12 
matching the existing pin convention. Logs to clobber-events.jsonl on action.

## Runbook notes
- `revert_sentinel.py --dry-run` = safe inspection, no file changes
- `revert_sentinel.py` (no flags) = auto-restores from canonical on detection
- `self_probe.py` writes to `memory/ops/selfprobe-result.json` for sandbox-seat consumption
