# CYCLE TRANSITION CHECKLIST
Parent: memory/ops/INDEX.md | Sibling: memory/ops/non-sandbox-queue.md, memory/goals/INDEX.md
Updated: 2026-11-17 (Mechanic). Small file — read whole.

## WHEN TO USE
At the start of each new goal cycle (after Orchestrator collects proposals), run this checklist
to ensure ops infrastructure is ready before agents begin work. Takes <5 min.

## STEPS

### 1. Carry-over audit (standing tasks)
Confirm these are still running (they persist across cycles):
- [ ] `PortalWatchdog` schtask alive (5-min cadence) — `schtasks /query /tn PortalWatchdog /fo list | findstr Status`
- [ ] `PortalFleetProbe` schtask alive (10-min cadence) — same query
- [ ] `PortalLoadProbe` schtask alive (daily 06:00) — same query
- [ ] `memory_mirror.py` last sync < 2h ago — check `memory/ops/clobber-events.jsonl` tail or portal /api/health/fleet
- [ ] Portal process on :8099 responding — `curl -s http://127.0.0.1:8099/api/health | findstr 200`

If any task is dead: re-register per memory/ops/windows-runbook.md §3, log in runbook-notes.md.

### 2. Non-sandbox queue flush
- [ ] Check memory/ops/non-sandbox-queue.md for open items
- [ ] If a non-sandbox seat is available (any agent on White ops terminal / RDP), batch-execute all open items in one sitting
- [ ] If no non-sandbox seat: confirm the NEEDS-HUMAN entries in blockers.md are accurate + current, then leave them (do NOT re-probe)

### 3. Goal file hygiene
- [ ] Old cycle goal files moved to memory/goals/archive/ (Orchestrator does this at cycle start)
- [ ] New memory/goals/<agent>.md files created with fresh goals
- [ ] TODO.md `## AGENT GOALS` section updated with verbatim proposals
- [ ] memory/goals/INDEX.md pointers refreshed

### 4. Evidence continuity
- [ ] Load baseline: confirm load-baseline.jsonl has at least 1 row per active day (no gaps > 2 days)
- [ ] Probe history: fleet-probe-history.jsonl last entry < 15 min old (or portal was down — check watchdog.log)
- [ ] Git: `git status` clean or only expected untracked files; last commit < 24h

### 5. Risk register update
- [ ] memory/ops/risk-register-cycle2.md (or new cycle-N file): add any NEW risks from the previous cycle's blockers
- [ ] Mark RESOLVED items with date + resolution method

## ANTI-PATTERNS (do NOT do)
- Do NOT re-probe a NEEDS-HUMAN blocker that was already recorded in a prior pass
- Do NOT create new probe scripts when existing ones cover the need — extend fleet_probe_v2.py or load_probe.py
- Do NOT leave goal files un-archived; stale goals confuse the ledger parser

## ONE-LINE SUMMARY FOR ORCHESTRATOR
"Before agents start cycle N: confirm 3 schtasks alive + portal up + mirror synced + queue flushed + old goals archived. ~5 min, no new scripts needed."