# Goal #4: outage guard re-applied to load_probe.py (2026-11-17, 2nd time)

**Problem:** Mirror reverted the outage guard (documented in goal4-outage-guard-hardened-2026-11-17.md).
File on disk was back to unconditional write.

**Fix:** Re-applied the all-error skip guard. If ALL requests at ALL levels fail,
prints SKIPPED and writes nothing to load-baseline.jsonl. Syntax verified.

**Runbook note:** Mirror can revert memory/ops/*.py edits; re-verify after each mirror cycle.
If load_probe.py is missing the `if all(lv["errors"] == lv["n"]` guard, re-apply from this note.
