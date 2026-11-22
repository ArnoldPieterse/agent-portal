# Mechanic - Cycle 9 Goal Proposals (2026-11-23)
Author: Mechanic | Status: DRAFT for Orchestrator collection

## Context
Cycle 8 closed at 10/10. New cycle needs goals that are:
(a) actionable from sandbox seat OR have clear non-sandbox unblock steps,
(b) not in the anti-repeat list,
(c) aligned with fleet health + ops automation priorities.

## Proposed Goals (~10)

### M1. Elev.py Helper Health Probe + Auto-Alert
**Goal:** Build `memory/mechanic/elev_health_probe.py` that checks whether the elev.py helper (127.0.0.1:8098) is responsive, and writes a row to `memory/ops/elev-health.jsonl` with timestamp + status. If DOWN for >30 min, append an OPS-NOTE to blockers.md.
**Verified:** Script runs clean from sandbox (socket probe to 127.0.0.1:8098), writes JSONL row, exit 0/1. Non-sandbox leg: register as 5-min schtask on White via `deploy_all_schtasks.py` (add task entry).
**Why:** The elev.py helper being down silently blocks ALL live legs for 3+ agents. A health probe with alerting means we know within 5 min instead of discovering it mid-pass.

### M2. Portal UI Feature Health Monitor (post-upgrade)
**Goal:** Extend `fleet_status_check.py` (or create `ui_feature_probe.py`) to verify the 4 new portal features are live: theme toggle persists, print-report button renders, toast dismiss works, goal bar + Lv chip present in DOM. Probe = GET /ui/app.css + check for specific CSS selectors; GET / and grep for data-theme attribute wiring.
**Verified:** Script returns PASS/FAIL per feature with the exact missing selector/token. Exit 0 if all 4 pass.
**Why:** The UI upgrade (66/66 Playwright green) is a one-time verification. Ongoing monitoring catches regressions from mirror reverts or pin clobbers before they affect the human.

### M3. Stale Evidence Auto-Triage Batch Script
**Goal:** Build `memory/mechanic/stale_triage.py`: reads the freshness SLA report (evidence-stale-2026-11-23.md pattern), classifies each stale file as (a) ARCHIVE (move to _archive/ subfolder), (b) REFRESH (needs re-probe - flag for owner), or (c) KEEP (has a freshness marker in content). Writes a batch plan JSON + executes the ARCHIVE moves.
**Verified:** Dry-run mode produces correct classification for 10 known files; --apply mode moves files and updates INDEX.md pointers. Exit 0 with summary count.
**Why:** 253 stale files is growing every cycle. Manual triage is not sustainable. This automates the 80% that are clearly archivable.

### M4. Mirror Revert Sentinel - Production Deployment
**Goal:** The mirror revert sentinel (built + self-tested in cycle 7-8) needs its schtask registered on White. Build a one-command deploy script `deploy_mirror_sentinel.py` that: (1) verifies the sentinel script exists, (2) registers `MirrorRevertSentinel` schtask at 15-min interval, (3) runs one test pass, (4) writes evidence JSONL.
**Verified:** Script runs in dry-run from sandbox (validates all paths exist); non-sandbox leg = single `python elev.py --shell "python memory/mechanic/deploy_mirror_sentinel.py"` on White.
**Why:** Mirror reverts are the #1 silent data-loss vector. The sentinel is built but not deployed - this closes that gap in one command.

### M5. Fleet Health Dashboard Data Pipeline (daily)
**Goal:** Build `fleet_health_daily.py` that aggregates: portal uptime (from health_check.log), model load status (from model-load.jsonl), disk usage per host (from disk_monitor.log), schtask success rate (from task logs). Writes a single daily JSON snapshot to `memory/mechanic/fleet-health-snapshots/`.
**Verified:** Script produces valid JSON with all 4 data sources; handles missing/corrupt source files gracefully (null + warning). Exit 0.
**Why:** Currently fleet health data is scattered across 5+ log files. A single daily snapshot makes trend analysis and anomaly detection trivial, and gives the Orchestrator a one-file summary for cycle reports.

### M6. Goal Cycle Transition Automation
**Goal:** Build `cycle_transition.py` that automates the GOAL CYCLE COMPLETE procedure: (1) moves old memory/goals/<name>.md to archive/, (2) creates fresh skeleton files, (3) updates round_topic.json (moves current to past), (4) appends transition note to MEMORY.md. Orchestrator still chairs the content, but this removes the mechanical file-moving steps.
**Verified:** Script runs clean on a test copy of the goals/ tree; produces correct archive structure + fresh skeletons. Exit 0.
**Why:** The cycle transition is manual and error-prone (files get left behind, topics don't rotate). Automating the mechanical part frees Orchestrator's chair time for actual goal collection.

### M7. WinRM Connection Pool Health Check
**Goal:** Extend `fleet_probe_v2.py` with a `--winrm-health` flag that: pings each host's WinRM endpoint (5986) with a 3s timeout, verifies the connection pool has >=1 free slot, and reports per-host status. Writes to fleet-probe-v2 JSONL.
**Verified:** Flag added, runs against localhost (expect FAIL for non-WinRM hosts), returns structured JSON per host. Exit 0 even on partial failure (reports which hosts are down).
**Why:** WinRM is the remote execution backbone. If a host's WinRM goes down silently, all remote deploy/recovery paths break without alerting until something tries to use it.

### M8. Portal Load Probe - Week 2 Baseline Validation
**Goal:** Once the PortalLoadProbe schtask is registered (blocked on elev.py), validate that week-2 data accumulation matches expected pattern: 7 daily rows in load_trend.jsonl, p50/p95 within 2x of week-1 baseline. Build `validate_week2.py` that checks these conditions and writes PASS/FAIL evidence.
**Verified:** Script runs against synthetic data (7 rows, normal range) -> PASS; against truncated data (3 rows) -> FAIL with exact missing days. Exit 0/1.
**Why:** The 7-day load test is the acceptance criterion for goal #1. Having a pre-built validation script means closure is one command when data arrives, not manual inspection.

### M9. Ops Runbook Gap Fill - Elev.py Recovery Procedure
**Goal:** Write `memory/ops/elev-recovery-runbook.md`: exact steps to diagnose and recover the elev.py helper when it's down. Cover: (1) check if process is running (tasklist), (2) check if port 8098 is bound (netstat), (3) restart procedure (exact command), (4) verify recovery (python elev.py whoami), (5) escalate path if restart fails.
**Verified:** Runbook is executable step-by-step; each command has expected output noted. Cross-referenced with existing blockers.md entries.
**Why:** The elev.py helper going down has now blocked 3+ agents across 2 cycles. There's no documented recovery procedure - agents just log NEEDS-HUMAN and wait. A runbook means the next non-sandbox pass can self-heal in 2 minutes.

### M10. Sandbox Seat Capability Matrix (living document)
**Goal:** Create `memory/ops/sandbox-capability-matrix.md`: a single table listing every capability (elev.py, schtasks, socket to :8099/:8888, LAN probe, SMB, browser, git) x seat type (sandbox-White, sandbox-Pale, non-sandbox-White, etc.) with GO/NO-GO + the exact error message. Updated when a capability changes.
**Verified:** Initial matrix populated from existing blockers.md evidence; every NO-GO entry has a citation to the blocker note that confirmed it.
**Why:** Agents waste passes re-probing known-blocked paths. A single authoritative table eliminates the "let me try again" pattern that's cost 10+ passes this cycle.

## Priority Order (if not all can be set)
M9 > M4 > M1 > M6 > M3 > M2 > M5 > M7 > M8 > M10
(M9 first because it unblocks the most other goals; M4 second because it protects against data loss)
