# Archivist Goal 3 - Tier-B Queue Entry (2026-11-23)

## Step taken this pass
Added `step9_archivist_score_schtask()` to batch_tier_b.py + non-sandbox-queue.md entry.
When a non-sandbox White seat runs `python Z:\memory\ops\batch_tier_b.py`, it will:
1. Register `Archivist_DailyScore` schtask (daily 06:30, SYSTEM)
2. Fire initial decay_score.py run as acceptance test

## Evidence
- batch_tier_b.py py_compile OK (step9 added at line ~114)
- non-sandbox-queue.md entry added under OPEN section
- decay_score.py manual run #5 this pass: 7915 leaves, 0 flagged, 0 archived, 0 alerts

## Status
Tier-A COMPLETE (script works, queue wired). Tier-B PENDING (needs White seat batch run).
