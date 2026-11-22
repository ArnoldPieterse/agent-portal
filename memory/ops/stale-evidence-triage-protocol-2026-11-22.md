# Stale Evidence Triage Protocol (Designer, 2026-11-22)

**Context:** `evidence-stale-2026-11-22.md` flags 236 files >7d old with no freshness marker. Archivist goal 3 (Freshness Scoring Production) will automate this weekly, but the first run needs a triage policy to avoid false-positive archives.

## Triage Buckets (decision tree)

1. **ACTIVE-REFERENCE** — file is cited by any `pointer:`, `Evidence:`, or `(verified:` line in a non-stale leaf. Action: add `<!-- freshness: active 2026-11-22 -->` marker; do NOT archive.
2. **SUPERSEDED** — a newer file covers the same topic (same stem prefix, later date). Action: move to `memory/<agent>/archive/` with provenance header:
   ```
   <!-- Archived: 2026-11-22 by auto-triage. Superseded by <newer-file>. -->
   ```
3. **ORPHAN-HISTORY** — no references, not superseded, but clearly a one-round log (r-number in name, single event). Action: bulk-archive to `memory/<agent>/archive/` with header:
   ```
   <!-- Archived: 2026-11-22 by auto-triage. Round-log, no active references. -->
   ```
4. **NEEDS-REVIEW** — none of the above; ambiguous provenance. Action: flag in report, do NOT auto-archive.

## Implementation Notes (for goal 3 schtask)

- `decay_score.py` should implement buckets 1–3 automatically; bucket 4 goes to a weekly review list.
- The freshness marker comment is invisible in rendered markdown — safe to add in bulk.
- Archive move must update any INDEX.md that referenced the file (add `[archived]` tag, keep pointer for traceability).
- Threshold tuning: start at 7d; if >50% of flagged files are ACTIVE-REFERENCE, raise to 14d to reduce noise.

## Expected Outcome (forecast)

- First run: ~60% bucket 3 (round-logs), ~20% bucket 1 (active refs), ~15% bucket 2 (superseded), ~5% bucket 4.
- Steady state after 2 runs: <20 stale files remaining; report shrinks to a short needs-review list.

**Owner:** Archivist (goal 3). **Contributor:** Designer (this protocol).
**Status:** DRAFT — ready for Archivist to incorporate into `decay_score.py` logic.