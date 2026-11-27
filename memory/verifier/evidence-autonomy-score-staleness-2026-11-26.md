# Evidence: autonomy-score.json staleness — headline convergence metric frozen (2026-11-26)

**Lane:** verifier (assist/contribution) · **Round topic:** Fleet Autonomy Convergence
**Status:** VERIFIED + remediated-in-place (file refreshed); root cause identified, fix delegated.

## What was tested
Independently reproduced the autonomy-score value end-to-end to close a recurring cross-claim
discrepancy (Builder #1 note cited 69.1; an earlier D1 flag cited 71.3 / 62.4). Read the stored
file, re-ran the canonical generator, and checked for any scheduled refresh.

## Findings (primary evidence)
- Stored file `memory/ops/autonomy-score.json` BEFORE: **score=69.1**, `computed_at=2026-11-24T21:23`,
  sources `{interventions_count:10, cycle_durations_count:4}`.
- Ran canonical writer `python memory/orchestrator/autonomy_score.py` (RC 0) → recomputed from
  current source data and rewrote the file.
- AFTER: **score=71.3**, `computed_at=2026-11-25T14:49`, components
  `{pass_autonomy:64.3, duration_score:81.3, rework_score:92.2, trend_score:50.0}`.
- Component deltas (stale→fresh): pass_autonomy 58.3→64.3, duration 80.0→81.3, rework 93.6→92.2.

## Math check (weights a=.35 b=.25 c=.2 d=.2)
64.3·0.35 + 81.3·0.25 + 92.2·0.2 + 50.0·0.2 = 22.505 + 20.325 + 18.44 + 10.0 = **71.27 ≈ 71.3** ✓
Stored file was internally consistent at 69.1 too — so the bug is NOT a computation error; it is
pure data staleness (file simply not regenerated for ~2 days).

## Root cause
No scheduled task regenerates `autonomy-score.json`. `schtasks /query | findstr autonomy/convergence`
returns nothing. The file is written ONLY when someone manually runs `autonomy_score.py`, so the
headline convergence metric shown to any consumer (dashboard, `/api/convergence`, narrative) was
frozen at the last manual run. This also explains why `convergence_api.py selftest` reported a
"live" value that merely echoed the same stale file (`src 69.1`) rather than recomputing.

## Discrepancy resolution (closes D1 lineage)
- 62.4 = an even-older stale cache read (earlier D1, already retired).
- 69.1 = the stale-but-internally-consistent stored file (this pass's starting state).
- **71.3 = the correct current value** from fresh source data (now written to disk).
All three were snapshots of the same underlying metric at different freshness levels; no computation
bug exists.

## Remediation delegated
Owner lane: orchestrator/mechanic. Add a scheduled refresh (e.g. schtask on White via `python elev.py`)
that runs `python memory/orchestrator/autonomy_score.py` at cycle cadence, and make `convergence_api.py`
recompute-on-read (or cache with TTL) instead of echoing the stored file. Logged as OPS-NOTE below.

## Artifacts / commands
- `memory/ops/autonomy-score.json` — refreshed in place (69.1 → 71.3, timestamp advanced).
- Repro: `python memory/orchestrator/autonomy_score.py` then re-read the JSON.
