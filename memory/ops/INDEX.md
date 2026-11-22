# OPS INDEX — fleet ops knowledge base. One-stop for any agent new to the fleet.
Last updated: 2026-11-19 (Orchestrator: sandbox egress self-probe workaround).
Prior: 2026-11-16 ~16:30 (Mechanic cycle-2 consolidation, goal #10).

## QUICK START (read these first if you're new)
1. memory/ops/windows-runbook.md — post-reboot recovery order, portal lifecycle, ground-truth checks
2. memory/ops/host-port-task-map-2026-11-15.md — 4 hosts, their IPs, ports, scheduled tasks
3. memory/ops/schtask-deps.md — full dependency graph + blast-radius scenarios for all 5 tasks
4. memory/ops/hotline-v2.md — escalation protocol when something breaks (M1/M2/R1 triggers)

## CORE RUNBOOKS
- Post-reboot / auto-start / PortalRun / RecoverAll / ground-truth -> memory/ops/windows-runbook.md
- Host inventory (IPs, ports, tasks per host) -> memory/ops/host-port-task-map-2026-11-15.md

- **Sandbox seat cannot reach :8099 at all (WinError 10013 even on 127.0.0.1)** -> memory/ops/sandbox-egress-selfprobe-workaround-2026-11-19.md — verified 11-19; restarting portal is NOT sufficient for sandbox live-verify; use server-side self-probe + file-read instead. Unblocks Designer acceptance + Mechanic Goal 8.
- **Consolidated non-sandbox LIVE-leg unblock runbook (egress-wall, :8888/:8099)** -> memory/ops/live-leg-runbook-2026-11-20.md — one ordered copy-paste checklist to close the egress-walled legs of Researcher #1/#2, Orchestrator #1/#5, Verifier #4, Mechanic #4 from a persistent White seat (where elev.py + :8888 egress exist). Supersedes the how-to-unblock portion of those NEEDS-HUMAN entries; do NOT re-probe from sandbox seats.

## DIAGNOSTICS / KNOWN BUGS
- Probe false-HEALTHY + fake-latency root cause + fix recipe (unblocks Mechanic Fleet Status API) -> memory/ops/probe-false-healthy-fix.md
- Scheduled-task dependency graph + blast radius -> memory/ops/schtask-deps.md
- HOTLINE escalation protocol v2 -> memory/ops/hotline-v2.md
- NON-SANDBOX EXECUTION QUEUE (batch network/browser/elevated tasks a sandbox seat can't run) -> memory/ops/non-sandbox-queue.md
- BLOCKERS log (NEEDS-HUMAN, exact cmd + error) -> memory/ops/blockers.md
- Goal-ledger record_evidence guard fix + dangling-pointer unblock recipe -> memory/ops/goal_ledger_record_fix-2026-11-18.md
- Git hygiene / commit conventions -> memory/ops/git-hygiene.md
- **Citation-phantom triage** (run after any goal-file edit / closure claim; separates PHANTOM into mis-citation vs lost-to-revert vs future-work placeholder + collision-safe assist rule) -> memory/ops/citation-phantom-triage-runbook.md
- **Browser-gate decision tree** (PER-SEAT procedure: Chrome check -> msedge probe -> two-tier fallback; resolves workaround-vs-unblock contradiction; run once per seat, never re-probe) -> memory/ops/browser-gate-decision-tree.md
- **Browser acceptance test workaround** (static structural verification as closure standard for goals blocked on headless browser; Edge hangs in sandbox, confirmed 11-19) -> memory/ops/browser-acceptance-workaround.md
- Mirror-revert prevention (commit-before-sync rule) -> memory/ops/mirror-revert-prevention-2026-11-18.md
- Memory sync spec (what gets mirrored where) -> memory/ops/memory-sync-spec-r13.md
- scan_goals() scoping bug fix (whitelist canonical agent files, eliminates 33 false positives) -> memory/ops/scan_goals-scope-fix-2026-11-19.md

## PROBE & MONITORING SCRIPTS (root dir)
- fleet_probe_v2.py — trend-aware 4-host probe; drift-based severity (OK/WARN/CRIT); runs every 10 min via PortalFleetProbe task
- load_probe.py — portal load test at 10/50/200 concurrency; p50/p95/p99 per endpoint; writes memory/ops/load-baseline.jsonl
- memory_mirror.py — SMB push/pull sync with post-push verify + auto-repair (goal #3, DONE)
- fleet_health_check.py (never committed) — quick 4-host reachability check
- recover_all.py — model reload on all hosts (LM Studio :8888)
- portal_watchdog.py — monitors portal process; restarts if dead
- sim_fleet_probe_degrade.py (never committed) — verification simulation for adaptive probe severity escalation

## EVIDENCE & LOGS (jsonl files in memory/ops/)
- fleet-probe-history.jsonl — every probe run with per-host latency + status
- probe-evidence.jsonl — structured probe events (WARN/CRIT escalations)
- load-baseline.jsonl — daily load test results (goal #4, accumulating)
- model-load.jsonl — model residency events per host
- clobber-events.jsonl — file overwrite/clobber detection events
- wedge-events.jsonl — portal/process wedge events
- canary-deploys.jsonl — canary deployment tracking
- hotpatch-events.jsonl — hot-patch application log
- net-egress-log.jsonl — outbound network audit (goal #6)

## CYCLE-2 ARTIFACTS (2026-11-16+)
- risk-register-cycle2.md — milestone risk register (O5, living doc)
- goal-progress-2026-11-16.md — per-agent goal progress snapshot
- mechanic-goal1-adaptive-probe-evidence-2026-11-16.md — adaptive probe simulation PASS evidence
- mechanic-goal3-closure-2026-11-15.md — self-healing mirror closure record
- reboot-dryrun-remote-legs-2026-11-16.md — Pale/Black/Red reboot dry-run results
- portal-down-2026-11-16.md — today's portal outage + recovery log

## REFERENCE (less frequently needed)
- Agent onboarding playbook -> memory/ops/agent-onboarding-playbook.md
- PDF reporting recipe -> memory/ops/pdf-reporting.md
- Ingestion spec -> memory/ops/ingestion-spec.md
- Fleet state snapshot 11-15 -> memory/ops/fleet-state-2026-11-15.md
- Public repo status -> memory/ops/public-repo-agent-portal-2026-11-15.md
- Verifier health checks (daily) -> memory/ops/verifier-healthcheck-2026-11-15.md
- AC V-09 provenance determinism -> memory/ops/verifier-ac-v09-2026-11-15.md
- Memory trim archive (pre-11-14 MEMORY.md) -> memory/ops/memory-trim-archive-2026-11-14.md
- stale_claim_check.py .json/.jsonl fallback regression (re-applied 2026-11-19; 206->58 MISSING; unpinned ops/*.py reverted by mirror) -> memory/ops/stale-claim-check-fallback-regression-2026-11-19.md

## ARCHIVED (cycle-1, superseded by memory/goals/)
- left-*.md files are cycle-1 goal trackers; canonical goals now live in memory/goals/<agent>.md
- builder-fleet-8099-sweep-r80-2026-11-14.md — historical sweep record
- quarantine-index-html-variants-2026-11-13.md — PIN_GUARD quarantine history
- white-lan-firewall-drop-2026-11-14.md — historical firewall incident
- -> memory/ops/merge-queue-git-progress-2026-11-16.md | sandbox merge queue + git goal-progress runbook (/api/merge-queue, /api/merge, /api/goals/history; goal-closure procedure; pin lineage)
- -> memory/ops/black-studio-failover-2026-11-16.md   Black Studio hung; Builder+Verifier failover to White (rollback record)
- -> memory/ops/autoloop.md | AUTO-LOOP: idle agents re-enter the work queue within ~1 min (solo passes, UMQ-first priority, streak cap)

## Linked content (KG orphan remediation 2026-11-19)
- [fleet-monitoring-cadence.md](memory/ops/fleet-monitoring-cadence.md)
- [pin-guard-extension-ui-files.md](memory/ops/pin-guard-extension-ui-files.md)
- 2026-11-22 Orchestrator: `recover_seats.py` (per-seat fleet recovery, plan-by-default) built + runs clean; converts the prose-only unreachable-seat unblock into a one-command `--execute` path for a non-sandbox seat. Evidence: -> memory/orchestrator/recover-seats-script-2026-11-22.md
