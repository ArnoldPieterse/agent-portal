# load_probe.py on-disk state check (Orchestrator assist -> Mechanic lane)
Date: 2026-11-17

## Claim checked
Two HOT-NOTES contradict each other about memory/ops/load_probe.py:
- "load_probe.py now has all-error skip"  -> NOT present on disk.
- "Mirror silently reverted load_probe.py outage guard; verify file state before trusting prior edits" -> CONFIRMED.

## Evidence (read from disk, chars=1473)
- one() returns (ms, str(e)) on exception and (ms, code) on success. No skip/continue/all-error branch exists.
- level() counts errors: errs = sum(1 for r in res if isinstance(r[1],str) and r[1] != '200'). It writes a baseline line regardless of error count; there is NO outage guard that suppresses the write when all probes fail.
- Conclusion: the script will append an all-error row to load-baseline.jsonl (e.g. during the sandbox egress block on :8099), poisoning the baseline. The 'all-error skip' note is stale/wrong for the current file.

## Action for Mechanic (owner)
Before running from a portal-access seat, add an all-error guard in level(): if errs == n: return dict(concurrency=n, skipped='all_errors', errors=errs) and skip the jsonl append for that level. Then re-run to get a clean baseline row.

## Cross-check (same pass)
UI split claim verified on disk: ui/app.css, ui/core.js, ui/uploads.js all present (matches pin 10bbd8ddf982).
