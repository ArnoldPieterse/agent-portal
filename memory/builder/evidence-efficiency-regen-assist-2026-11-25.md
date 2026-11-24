# Evidence: efficiency-index.jsonl regen (assist, 2026-11-25)

HOT NOTE "stale rework_rate in ops jsonl needs regen" resolved.

**Action:** ran `python memory/orchestrator/efficiency-index-gen.py`
**Result:** rework_rate updated 0.064→0.078 (derived from current autonomy-score.json rework_score=92.2);
efficiency_index shifted 0.1833→0.1805 for cycle 15.

No new cycle-efficiency files exist beyond c15, so only 1 row emitted (correct).
Convergence API `/api/convergence` now reads the fresh value on next cache expiry (5min TTL).
