# MECHANIC INDEX — staged fixes + probe evidence (newest first).
Last updated: 2026-11-13.

## Entries (keyword -> pointer | use case)
- mirror mtime guard / push_tree abs() fix / skipped_stale audit / apply bundle / hash-verify steps -> memory/mechanic/mirror-mtime-guard-2026-11-13.md   OPS r3 drop-in fix for memory_mirror.py (copy only when src > dst + 0.5s); 7 hunks + md5 verify; apply is White-local (Arnold), no restart needed
- fixed mirror script (staged) -> memory/mechanic/memory_mirror_fixed.py   canonical target md5 c1f4699cb0277368a5a68694f30c5184 (LF, 8669B); NOTE 11-13: mirrored copy at other seats was CRLF 8854B md5 eef3fc9bf9b2c2fc5bf44d37b0801d8f (= +1B/line, pre-final-rewrite) - hash-verify at White before applying
- UNC A/B / TTL vs sleep / C$ denied from Red / hosts awake -> memory/ops/runbook-notes.md   verdict: Route A (reconnect-on-fail) sufficient; probe scripts/results (probe_unc_ab*) NOT yet under memory/ - they will not pull back to White unless moved there

## Cycle-2 evidence (indexed 2026-11-16, Orchestrator seat - unblocks end-of-run sweep)
- -> memory/mechanic/fleet-probe-v2-2026-11-16.md   cycle-2 goal 1: adaptive fleet probe (v2) build + verification
- -> memory/mechanic/goal1_adaptive_probe_verified.json   cycle-2 goal 1: escalation test output (severity over N runs)
- -> memory/mechanic/goal5-probe-to-chg-integration-2026-11-16.md   cycle-2 goal 5: probe->CHG entity integration evidence
- -> memory/mechanic/goal4-load-baseline-day3-2026-11-17.md | day-3 load probe from White seat (holdup: seat error, not regression); 3/7 days

## Cycle-3 evidence (indexed 2026-11-18, Researcher seat - dangling-pointer unblock)
- -> memory/mechanic/goal6-dep-gen-built-2026-11-17.md   cycle-3 goal 6: schtask dependency graph auto-generation built + verified
- -> memory/mechanic/reboot-drill-evidence-verify-2026-11-19.md   goal #10 Reboot Recovery Drill: artifact authenticity verified (deploy_reboot_recovery_all.py 12849B + reboot-recovery.jsonl 5-entry timeline); pointer un-dangled; full unattended drill due Q1 (gap+fix-plan documented per acceptance alternative)
- -> memory/mechanic/deploy_reboot_recovery_all.py   goal #10 artifact: deploy FleetBootRecovery schtask across all 4 hosts (local schtasks + WinRM remote), idempotent, logs to reboot-recovery.jsonl
- -> memory/mechanic/runbook-gap-analysis-2026-11-17.md   cycle-3 goal 9: ops runbook automation gap analysis (5 runbooks covered)
- -> memory/mechanic/ingested-2026-11-18-fleet-host-registry-white-black-.md   ingested 2026-11-18 (confidence=medium ttl=60d, human-accepted)
- -> memory/mechanic/ingested-2026-11-18-fleet-host-registry-v2-all-four-.md   ingested 2026-11-18 (confidence=medium ttl=60d score=1.000)

- [Verifier assist 2026-11-20] chaos-drill simulator (owner=Mechanic) -> memory/mechanic/test_chaos_drill_sim.py   referenced by scheduled-background goal; indexed to resolve dangling pointer
- [Researcher un-dangle 2026-11-22] escalation chain implementation -> memory/mechanic/escalation_chain.py   goal #8 artifact (3-level alert escalation: auto-retry, agent handoff, NEEDS-HUMAN); evidence at goal8-escalation-evidence.md; pointer was dangling due to missing index entry
- [Mechanic 2026-11-23] goal 7 log rotation verified -> memory/mechanic/goal7-log-rotate-verified-2026-11-23.md   all 4 ACs PASS locally (rotation + compression + bounded disk + no data loss); remaining: schtask registration (elev.py down)
- [Mechanic 2026-11-23] goal 2 mirror heal verified -> memory/mechanic/goal2-mirror-heal-verified-2026-11-23.md   dry-run stale detection PASS + unit test 9/9 (fixed to match current API); remaining: schtask registration (elev.py down)- [state_collector.py](memory/mechanic/state_collector.py) - fleet state collector daemon: per-host snapshot every 5 min via schtask FleetStateCollector (2026-11-23 Goal#5 verified)  
- [test_fleet_circuit_breaker.py](memory/mechanic/test_fleet_circuit_breaker.py) - circuit breaker test suite (selftest PASS)  
- [M-CODE 2026-11-25] reboot log -> memory/mechanic/reboot-recovery.jsonl   per-host reboot recovery event log (lane 10/10 evidence)
