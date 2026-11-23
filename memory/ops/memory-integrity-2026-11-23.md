# Memory Tree Integrity Report
Run: 2026-11-23 | Status: **FAIL (305 issues)**

| Check | Result | Count |
|---|---|---|
| Orphaned files | FAIL | 84 |
| Broken pointers | FAIL | 203 |
| Circular refs | FAIL | 2 |
| INDEX size budget | FAIL | 16 |

## Orphaned Files
- `memory\archivist\quarantine\archivist\_quarantine_test_target.md`
- `memory\levels\level_1_20261123-060001.md`
- `memory\levels\level_2_20261123-093159.md`
- `memory\levels\level_3_20261123-103155.md`
- `memory\mechanic\postmortems\20261118-103848_test_portal_down.md`
- `memory\mechanic\postmortems\20261118-120631_test-incident.md`
- `memory\mechanic\postmortems\20261118-124537_test_incident.md`
- `memory\mechanic\postmortems\20261118-155747_untitled.md`
- `memory\mechanic\postmortems\20261118-204430_untitled.md`
- `memory\mechanic\postmortems\20261118-211827_verification_run.md`
- `memory\mechanic\postmortems\20261118-232110_portal_auto-restart_failure.md`
- `memory\mechanic\postmortems\20261118-sandbox-firewall-port-bind.md`
- `memory\ops\handoffs\archivist-20261113.md`
- `memory\ops\handoffs\builder-20261113.md`
- `memory\ops\handoffs\designer-20261113.md`
- `memory\ops\handoffs\mechanic-20261113.md`
- `memory\ops\handoffs\mechanic-4-2026-11-20.md`
- `memory\ops\handoffs\orchestrator-1-2026-11-20.md`
- `memory\ops\handoffs\orchestrator-20261114.md`
- `memory\ops\handoffs\researcher-20261113.md`
- `memory\ops\handoffs\scribe-20261113.md`
- `memory\ops\handoffs\verifier-20261113.md`
- `memory\ops\handoffs\verifier-4-2026-11-20.md`
- `memory\ops\incidents\2026-11-16-fleet-portal_down.md`
- `memory\ops\incidents\2026-11-17-fleet-portal_down.md`
- `memory\ops\incidents\2026-11-18-fleet-portal_down.md`
- `memory\ops\incidents\2026-11-19-fleet-portal_down.md`
- `memory\ops\incidents\2026-11-20-black-host_down.md`
- `memory\ops\incidents\2026-11-20-fleet-portal_down.md`
- `memory\ops\incidents\2026-11-20-researcher-wedged.md`
- `memory\ops\loadtest\closure_runbook.md`
- `memory\ops\runbooks\boot_recovery.md`
- `memory\ops\runbooks\host_down_response.md`
- `memory\ops\runbooks\safe_test.md`
- `memory\ops\runbooks\scheduled_maintenance.md`
- `memory\researcher\anomaly-narratives\narratives-2026-11-23_0801.md`
- `memory\researcher\briefs\fleet-vram-management.md`
- `memory\researcher\briefs\mirror-revert-clobber-loop.md`
- `memory\scheme\goal3-ledger-reconciled-2026-11-19.md`
- `memory\scribe\_test_gate\bad.md`
- `memory\scribe\_test_gate\clean.md`
- `memory\scribe\_test_v2\report_a.md`
- `memory\scribe\_test_v2\report_b.md`
- `memory\scribe\_test_v2\report_c.md`
- `memory\scribe\_v2_fix\a.md`
- `memory\scribe\_v2_fix\b_agree.md`
- `memory\scribe\_v2_fix\b_disagree.md`
- `memory\scribe\_v2_fix\dup_bad.md`
- `memory\scribe\_v2_fix\dup_ok.md`
- `memory\scribe\_v2_fix\idx_bad.md`
- ... and 34 more

## Broken Pointers
- `memory\goals\INDEX.md` -> `forecast-latest.md`
- `memory\goals\INDEX.md` -> `cycle-proposal.md`
- `memory\goals\INDEX.md` -> `orchestrator.md`
- `memory\goals\INDEX.md` -> `scheduled-background.md`
- `memory\goals\INDEX.md` -> `retro-cycle-7.md`
- `memory\goals\INDEX.md` -> `archive/orchestrator-2026-11-13.md`
- `memory\goals\INDEX.md` -> `all-goals-2026-11-13.md`
- `memory\goals\INDEX.md` -> `forecast_engine.py`
- `memory\orchestrator\INDEX.md` -> `failover_drill.py`
- `memory\researcher\INDEX.md` -> `ui-slices-audit-2026-11-17.md`
- `memory\researcher\INDEX.md` -> `schtasks-seat-sandbox-verify-2026-11-23.md`
- `memory\researcher\INDEX.md` -> `../mechanic/postmortem_gen.py`
- `memory\squire\INDEX.md` -> `cycle3-discrepancy-resolved-2026-11-18.md`
- `memory\archivist\evidence-goal1-delta-reporting-2026-11-18.md` -> `knowledge_graph.py`
- `memory\archivist\MEMORY.md` -> `../portal/architecture.md`
- `memory\archivist\search-index-refresh-2026-11-21.md` -> `decay-alerts.md`
- `memory\archivist\search-index-refresh-2026-11-21.md` -> `decay-alerts.md`
- `memory\archivist\supersession-findings-2026-11-16.md` -> `../synthesis/2026-11-12-upgrade-round.md`
- `memory\archivist\xref-check-report-2026-11-19.md` -> `../portal/architecture.md`
- `memory\archivist\xref-check-report-2026-11-19.md` -> `../synthesis/2026-11-12-upgrade-round.md`
- `memory\archivist\xref-check-report-2026-11-19.md` -> `decay-report.md`
- `memory\archivist\xref-check-report-2026-11-19.md` -> `../synthesis/2026-11-12-upgrade-round.md`
- `memory\archivist\xref-check-report-2026-11-19.md` -> `../synthesis/2026-11-16-crossassist-evidence-pass.md`
- `memory\archivist\xref-check-report-2026-11-19.md` -> `../synthesis/2026-11-12-upgrade-round.md`
- `memory\archivist\xref-check-report-2026-11-19.md` -> `../synthesis/2026-11-12-upgrade-round.md`
- `memory\archivist\xref-check-report-2026-11-19.md` -> `../squire/cycle3-discrepancy-resolved-2026-11-18.md`
- `memory\archivist\xref-check-report-2026-11-19.md` -> `knowledge_graph.py`
- `memory\archivist\xref-check-report-2026-11-19.md` -> `../designer/design_breakpoint_check.py`
- `memory\archivist\xref-check-report-2026-11-19.md` -> `../mechanic/auto_restart.py`
- `memory\archivist\xref-check-report-2026-11-19.md` -> `../mechanic/ac_a2_live_leg_r20.py`
- `memory\archivist\xref-check-report-2026-11-19.md` -> `../mechanic/ac_a2_live_leg_r20.py`
- `memory\archivist\xref-check-report-2026-11-19.md` -> `../designer/apply_designer_scale_patch.py`
- `memory\archivist\xref-check-report-2026-11-19.md` -> `../mechanic/postmortem_gen.py`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../portal/architecture.md`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../synthesis/2026-11-12-upgrade-round.md`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../portal/architecture.md`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../synthesis/2026-11-12-upgrade-round.md`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../synthesis/2026-11-12-upgrade-round.md`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../synthesis/2026-11-16-crossassist-evidence-pass.md`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../synthesis/2026-11-12-upgrade-round.md`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../synthesis/2026-11-12-upgrade-round.md`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../squire/cycle3-discrepancy-resolved-2026-11-18.md`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../archivist/decay-report.md`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../synthesis/2026-11-12-upgrade-round.md`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../synthesis/2026-11-16-crossassist-evidence-pass.md`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../synthesis/2026-11-12-upgrade-round.md`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../synthesis/2026-11-12-upgrade-round.md`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `cycle3-discrepancy-resolved-2026-11-18.md`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../designer/design_breakpoint_check.py`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../mechanic/auto_restart.py`
- ... and 153 more

## Circular References
- C:\Users\black\.unsloth\studio\sandbox\_default\memory\archivist\INDEX.md -> C:\Users\black\.unsloth\studio\sandbox\_default\memory\archivist\INDEX.md
- C:\Users\black\.unsloth\studio\sandbox\_default\memory\workspace\INDEX.md -> C:\Users\black\.unsloth\studio\sandbox\_default\memory\workspace\INDEX.md

## Oversized INDEX Files
- `memory\archivist\INDEX.md`: 5669 chars (budget 1600)
- `memory\builder\INDEX.md`: 11156 chars (budget 1600)
- `memory\designer\INDEX.md`: 6055 chars (budget 1600)
- `memory\goals\INDEX.md`: 2218 chars (budget 1600)
- `memory\INDEX.md`: 2716 chars (budget 1600)
- `memory\llm\INDEX.md`: 1768 chars (budget 1600)
- `memory\mechanic\INDEX.md`: 3991 chars (budget 1600)
- `memory\ops\INDEX.md`: 7540 chars (budget 1600)
- `memory\orchestrator\INDEX.md`: 8994 chars (budget 1600)
- `memory\portal\bugs\INDEX.md`: 3452 chars (budget 1600)
- `memory\portal\INDEX.md`: 4174 chars (budget 1600)
- `memory\researcher\INDEX.md`: 78713 chars (budget 1600)
- `memory\scribe\INDEX.md`: 2886 chars (budget 1600)
- `memory\synthesis\INDEX.md`: 5155 chars (budget 1600)
- `memory\verifier\INDEX.md`: 18251 chars (budget 1600)
- `memory\workspace\INDEX.md`: 49475 chars (budget 1600)
