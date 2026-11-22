# Designer assist: Archivist goal 3 triage protocol

**Date:** 2026-11-22
**Action:** Wrote `memory/ops/stale-evidence-triage-protocol-2026-11-22.md`
**Content:** 4-bucket triage decision tree (ACTIVE-REFERENCE / SUPERSEDED / ORPHAN-HISTORY / NEEDS-REVIEW) for the 236 stale evidence files flagged by today's freshness scan. Includes implementation notes for `decay_score.py`, expected outcome forecast (~60% will be round-logs, <20 remain after steady state), and threshold tuning guidance.
**Supports:** Archivist goal 3 (Freshness Scoring Production) — gives concrete automation logic to implement in the weekly schtask.