# Rest-of-goals: attempts + decision map (Scribe synthesis)

Provenance: source=synthesis (Scribe) | date=2026-11-18 | confidence=high | ttl=7d
Trigger: user ask "everyone hand in your attempts to completing the rest of the goals, then the goal owners can choose the best solutions out of the list."
Scope: the 8 items parked at memory/goals/scheduled-background.md (main lane is 0 open per TODO.md). Every claim below traces to a named on-disk file.

## What "the rest" is
Main lane = 0 open substantive goals (TODO.md top, 2026-11-18 ~10:0x). Remaining work = the background scheduled list. NOTE DISCREPANCY: MEMORY.md says "10 items" moved to background but scheduled-background.md holds **8** — flagged for Orchestrator to reconcile; I do not silently pick a side.

## Per-goal state (built vs remaining)
All 8 are already BUILT; the open work is registration + cadence, not design.

| Goal | Built (evidence on disk) | Exact remaining step | Owner |
|---|---|---|---|
| ARCHIVIST#6 decay model | memory/archivist/decay_score.py + decay-report.md (732 leaves, 0 flagged <0.35) | register weekly schtask; add auto-archive (<0.2 -> memory/archive/ w/ pointer) + recently-referenced<0.5 alert | Archivist |
| ARCHIVIST#8 snapshot diff | memory/archivist/snapshot-diff-20261117.md (+110/-0/~36, 0 deletions) | register weekly schtask; emit one-line chat summary + leaf | Archivist |
| MECHANIC#1 load test | memory/mechanic/fleet_load_probe.py functional; load_trend.jsonl = 1 line; schtask NOT registered | register FleetLoadProbe via elev.py (exact cmd in memory/goals/mechanic-goal1-forecast-2026-11-18.md); collect to 7 dates; run --week-complete | Mechanic |
| MECHANIC#2 mirror heal | memory/mechanic/mirror_heal.py + register_mirror_heal_task.py (goal2_mirror_heal_productionized-2026-11-17.md) | register MirrorHeal schtask via elev.py; 2-week clean-repair window | Mechanic |
| MECHANIC#6 dep-gen | memory/mechanic/goal6-dep-gen-baseline-verified-2026-11-18.md (week0 baseline + diff test PASS) | 2 REAL weekly generations from schtasks /query on White | Mechanic |
| MECHANIC#8 chaos drill | memory/ops/chaos_drill.py built, dry-run PASS (goal8-chaos-drill-built-2026-11-18.md) | register monthly schtask; 1 LIVE drill <60s recovery + panel screenshot | Mechanic |
| SCRIBE#10 compression fidelity | see section 6 (two audits already on disk, >=90%) | one more audit next calendar week to satisfy the "weekly" cadence caveat | Scribe |
| VERIFIER#8 smb drift detector | memory/verifier/smb_drift_detector.py (5446 bytes) exists | register 30-min schtask; 2-week drift log, zero unexplained >5min divergence | Verifier |

## The unifying blocker (the real "rest")
Six of eight (ARCHIVIST#6/#8, MECHANIC#1/#2/#6/#8, VERIFIER#8) gate on the SAME thing: **registering a schtask from this sandbox seat**, which fails with COM "Class not registered" (documented in memory/goals/mechanic-goal1-forecast-2026-11-18.md). Per the run [SHELL] note, admin works via `python elev.py` and elevation is NOT a blocker — so the unblock step for all six is one batched registration pass on White via elev.py, then each goal closes on its own date/probe gate. No new design needed; do not re-open these as solution problems.

## 6. SCRIBE#10 (mine) — actual state + my attempt
CORRECTED this pass: two audits are ALREADY on disk, so this is NOT a fresh build:
- memory/scribe/compression-fidelity-audit-2026-11-18.md — audit 1/2, cycle-3 set, mean retention 93.8%, fact-loss items named.
- memory/scribe/compression-fidelity-audit2-2026-11-18.md — audit 2/2, distinct 11-16 set, 92%, fact-loss named.
- Closure file: memory/scribe/goal10-compression-fidelity-closure-2026-11-18.md — acceptance "two weekly audits + scores + fact-loss named" MET on substance (both >=90%).
- CAVEAT (from that closure file): both audits are same-day (2026-11-18), not a full calendar week apart. So the only remaining step = one more audit next calendar week to satisfy the literal "weekly" cadence. My contribution this pass = this decision map itself, which is a synthesis product that will be scored in that next audit (and my method — key-fact checklist + explicit "lost" array — keeps compress-without-inventing auditable).

## Recommendation to goal owners (the "choose the best" part)
- The 6 non-Scribe items are NOT solution-design problems anymore — they are **scheduling + cadence** problems. Best solution for all six = one batched schtask-registration pass by Mechanic via elev.py on White, then let each run on its stated cadence and close on the date/probe gate. No new code; do not re-open design.
- SCR#10 (mine) needs only one more weekly audit next calendar week — attempt/method already in place.
- Open for Orchestrator: reconcile the "10 vs 8" background-item count discrepancy.
