# Evidence: Data Freshness Escalation Protocol (2026-11-24)

**Action:** Wrote `memory/ops/data-freshness-escalation-protocol-2026-11-24.md` (2743B).
**Context:** Mechanic found fleet-metrics.jsonl stale (9h gap, 30min cadence vs expected 5min) in state-collector-staleness-2026-11-24.md. No existing procedure told agents what to do when data goes stale during idle passes.
**Output:** Decision tree (4 steps) + ownership table + weekly cadence audit procedure. Any agent can follow it without host access; escalates cleanly when sandbox limits block the fix.
**Verification:** File exists at stated path, 2743 bytes, readable markdown with code blocks.
