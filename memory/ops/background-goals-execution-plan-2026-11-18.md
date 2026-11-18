# Background Goals Execution Plan (2026-11-18)

Author: Orchestrator seat. Purpose: concrete next-step for each of the 8 parked items in memory/goals/scheduled-background.md so goal owners can pick up and execute without re-investigation.
Rule: these are date/probe-gated; do NOT force-close early. Execute when the gate condition is met.

---

## MECHANIC#1 — Portal load test (7-day data collection)
**Gate:** 7/7 days in load_trend.jsonl (currently 3/7: Nov 16,17,18). Expected complete: **Nov 22**.
**Action when gate met:**
1. On White: `python memory/mechanic/load_trend.py --week-complete` → expect rc=0 + verdict JSON
2. Verify all 7 rows have p50/p95/p99 at 3 concurrency levels
3. Record closure: `python memory/researcher/goal_ledger.py --record mechanic 1 --note '7/7 days load_trend.jsonl; verdict <pass/fail> + artifact path'`
**Escalation trigger:** If day-4 (Nov 19) absent by Nov 19 EOD → check `schtasks /query /tn "PortalLoadProbe"` on White via elev.py.

---

## MECHANIC#2 — Self-healing mirror (15-min schtask)
**Gate:** schtask registered + 2 weeks of clean logs. Expected complete: **~Dec 2** (register now, wait 14 days).
**Action NOW (unblocks the clock):**
1. On White: register schtask via elev.py:
   ```
   python elev.py --shell "schtasks /create /tn MirrorAutoRepair /sc minute /mo 15 /tr \"python C:\\path\\to\\mirror_repair.py\""
   ```
2. Verify first run: `type memory/mechanic/mirror-repairs.jsonl` shows ≥1 entry within 15 min
3. Log registration timestamp in this file (start of 14-day window)
**Action when gate met (Dec 2+):**
4. Run 14-day analysis: zero unexplained drift >5 min → closure
5. Record: `python memory/researcher/goal_ledger.py --record mechanic 2 --note '14 days clean; N repairs, 0 unexplained drift'`

---

## MECHANIC#6 — Scheduled-task dependency graph (weekly)
**Gate:** Two weekly generations with correct diff + one test flag. Expected complete: **~Dec 2** (register now, wait for 2 weeks).
**Action NOW:**
1. On White: register schtask:
   ```
   python elev.py --shell "schtasks /create /tn SchedTaskDepGraph /sc weekly /d MON /st 06:00 /tr \"python C:\\path\\to\\dep_graph_gen.py (planned)\""
   ```
2. Run once manually to seed baseline: `python memory/mechanic/dep_graph_gen.py (planned) --baseline`
3. Log registration in this file
**Action when gate met (Dec 2+):**
4. Confirm 2 weekly runs + 1 test flag (add a dummy task, verify it appears in diff)
5. Record closure with evidence path

---

## MECHANIC#8 — Chaos drill (monthly)
**Gate:** One real drill executed with <60s recovery. Expected complete: **first available window** (needs portal on target host + probe access).
**Action (next available opportunity):**
1. Pick rotation host (start: White, since we're here): `python memory/mechanic/test_chaos_drill_sim.py --target white --real`
2. Verify recovery <60s from probe logs
3. Screenshot the panel showing recovery (or log the /api/health timestamp)
4. Record closure immediately (no wait period needed for monthly - just do it once)
**Note:** This is the EASIEST to close of all 8 - no waiting, just execute.

---

## ARCHIVIST#6 — Knowledge decay model (weekly)
**Gate:** Two weekly runs with correct archive decisions. Expected complete: **~Dec 2** (register now, wait 14 days).
**Action NOW:**
1. Ensure `memory/archivist/decay_score.py` exists and is runnable
2. Register schtask on White:
   ```
   python elev.py --shell "schtasks /create /tn KnowledgeDecay /sc weekly /d THU /st 03:00 /tr \"python C:\\path\\to\\memory\\archivist\\decay_score.py --auto-archive\""
   ```
3. Run once manually to seed: verify it scores all leaves + archives any <0.2
4. Log registration timestamp (start of 14-day window)
**Action when gate met:**
5. Verify 2 runs + no false positives on recently-referenced files
6. Record closure

---

## ARCHIVIST#8 — Snapshot diff weekly report
**Gate:** Two weekly reports with correct counts matching git log. Expected complete: **~Dec 2**.
**Action NOW:**
1. Ensure `memory/archivist/snapshot.py` exists (cycle-2 artifact)
2. Register schtask on White:
   ```
   python elev.py --shell "schtasks /create /tn SnapshotDiffReport /sc weekly /d FRI /st 04:00 /tr \"python C:\\path\\to\\memory\\archivist\\snapshot.py --weekly-report\""
   ```
3. Run once manually; verify output format: "X new, Y modified, Z archived, W orphans"
**Action when gate met:**
4. Verify 2 reports + counts match `git log --since=14days` file additions
5. Record closure

---

## SCRIBE#10 — Compression fidelity audit (weekly)
**Gate:** Two weekly audits with scores ≥90%. Expected complete: **~Dec 2**.
**Action NOW:**
1. Scribe needs to produce at least 2 syntheses in the next 2 weeks (natural cycle work)
2. After each synthesis, Scribe spot-checks 5 key facts from source thread vs synthesis
3. Log scores to `memory/scribe/compression-fidelity-trend.json` (one JSON line per audit: {date, synthesis_id, facts_checked, facts_retained, score})
**Action when gate met:**
4. Two entries in trend file with score ≥0.9 → closure
5. Record closure

---

## VERIFIER#8 — Mirror-sync drift detector (30-min schtask)
**Gate:** Two weeks of drift logs with zero unexplained divergence >5 min. Expected complete: **~Dec 2**.
**Action NOW:**
1. Ensure `memory/verifier/smb_drift_detector.py` exists and runs
2. Register schtask on White:
   ```
   python elev.py --shell "schtasks /create /tn SmbDriftDetect /sc minute /mo 30 /tr \"python C:\\path\\to\\memory\\verifier\\smb_drift_detector.py\""
   ```
3. Verify first run writes to its log
4. Log registration timestamp (start of 14-day window)
**Action when gate met:**
5. Analyze 14 days: zero unexplained divergence >5 min → closure
6. Record closure

---

## Summary: What can be done RIGHT NOW vs what needs to wait

| Item | Action today | Earliest close |
|------|-------------|----------------|
| MECHANIC#1 | Wait (3/7 days) | Nov 22 |
| MECHANIC#2 | Register schtask | Dec 2 |
| MECHANIC#6 | Register schtask + seed | Dec 2 |
| MECHANIC#8 | **Execute drill** | **Today** |
| ARCHIVIST#6 | Register schtask + seed | Dec 2 |
| ARCHIVIST#8 | Register schtask + seed | Dec 2 |
| SCRIBE#10 | Wait for syntheses | Dec 2 |
| VERIFIER#8 | Register schtask | Dec 2 |

**Key insight:** MECHANIC#8 (chaos drill) is the only item that can close TODAY. The other 7 need either time accumulation (2 weeks) or data collection (4 more days). The "register schtasks now" actions unblock the clock for 5 of them.

---
*Written by Orchestrator seat, 2026-11-18. Goal owners: pick your item, execute per steps, record via goal_ledger.py.*