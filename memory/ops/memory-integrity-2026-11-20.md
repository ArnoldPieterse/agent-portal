# Memory Tree Integrity Report
Run: 2026-11-20 | Status: **FAIL (263 issues)**

| Check | Result | Count |
|---|---|---|
| Orphaned files | FAIL | 68 |
| Broken pointers | FAIL | 177 |
| Circular refs | FAIL | 2 |
| INDEX size budget | FAIL | 16 |

## Orphaned Files
- `memory\mechanic\postmortems\20261118-103848_test_portal_down.md`
- `memory\mechanic\postmortems\20261118-120631_test-incident.md`
- `memory\mechanic\postmortems\20261118-124537_test_incident.md`
- `memory\mechanic\postmortems\20261118-155747_untitled.md`
- `memory\mechanic\postmortems\20261118-204430_untitled.md`
- `memory\mechanic\postmortems\20261118-211827_verification_run.md`
- `memory\mechanic\postmortems\20261118-232110_portal_auto-restart_failure.md`
- `memory\mechanic\postmortems\20261118-sandbox-firewall-port-bind.md`
- `memory\ops\.pytest_cache\README.md`
- `memory\ops\handoffs\mechanic-4-2026-11-20.md`
- `memory\ops\handoffs\orchestrator-1-2026-11-20.md`
- `memory\ops\handoffs\verifier-4-2026-11-20.md`
- `memory\ops\incidents\2026-11-16-fleet-portal_down.md`
- `memory\ops\incidents\2026-11-17-fleet-portal_down.md`
- `memory\ops\incidents\2026-11-18-fleet-portal_down.md`
- `memory\ops\incidents\2026-11-19-fleet-portal_down.md`
- `memory\ops\incidents\2026-11-20-black-host_down.md`
- `memory\ops\incidents\2026-11-20-fleet-portal_down.md`
- `memory\ops\incidents\2026-11-20-researcher-wedged.md`
- `memory\ops\loadtest\closure_runbook.md`
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
- `memory\scribe\_v2_fix\idx_ok.md`
- `memory\scribe\_v2_fix\sized.md`
- `memory\scribe\briefings\archivist-briefing.md`
- `memory\scribe\briefings\builder-briefing.md`
- `memory\scribe\briefings\designer-briefing.md`
- `memory\scribe\briefings\mechanic-briefing.md`
- `memory\scribe\briefings\orchestrator-briefing.md`
- `memory\scribe\briefings\researcher-briefing.example.md`
- `memory\scribe\briefings\researcher-briefing.md`
- `memory\scribe\briefings\scribe-briefing.md`
- `memory\scribe\briefings\verifier-briefing.md`
- `memory\scribe\cards\anti-stall.md`
- `memory\scribe\cards\hotload.md`
- `memory\scribe\cards\mirror.md`
- `memory\scribe\cards\pin-file.md`
- `memory\scribe\test-handoffs\handoff-1.md`
- ... and 18 more

## Broken Pointers
- `memory\goals\INDEX.md` -> `retro-cycle-7.md`
- `memory\researcher\INDEX.md` -> `ui-slices-audit-2026-11-17.md`
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
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../mechanic/ac_a2_live_leg_r20.py`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../mechanic/ac_a2_live_leg_r20.py`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../designer/apply_designer_scale_patch.py`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../mechanic/postmortem_gen.py`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../archivist/knowledge_graph.py`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../designer/design_breakpoint_check.py`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../mechanic/auto_restart.py`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../mechanic/ac_a2_live_leg_r20.py`
- `memory\archivist\xref-fix-log-2026-11-19.md` -> `../mechanic/ac_a2_live_leg_r20.py`
- ... and 127 more

## Circular References
- C:\Users\White\.unsloth\studio\sandbox\_default\memory\archivist\INDEX.md -> C:\Users\White\.unsloth\studio\sandbox\_default\memory\archivist\INDEX.md
- C:\Users\White\.unsloth\studio\sandbox\_default\memory\workspace\INDEX.md -> C:\Users\White\.unsloth\studio\sandbox\_default\memory\workspace\INDEX.md

## Oversized INDEX Files
- `memory\archivist\INDEX.md`: 4452 chars (budget 1600)
- `memory\builder\INDEX.md`: 10484 chars (budget 1600)
- `memory\designer\INDEX.md`: 6055 chars (budget 1600)
- `memory\goals\INDEX.md`: 4898 chars (budget 1600)
- `memory\INDEX.md`: 2334 chars (budget 1600)
- `memory\llm\INDEX.md`: 1768 chars (budget 1600)
- `memory\mechanic\INDEX.md`: 3679 chars (budget 1600)
- `memory\ops\INDEX.md`: 7265 chars (budget 1600)
- `memory\orchestrator\INDEX.md`: 8994 chars (budget 1600)
- `memory\portal\bugs\INDEX.md`: 3452 chars (budget 1600)
- `memory\portal\INDEX.md`: 4174 chars (budget 1600)
- `memory\researcher\INDEX.md`: 76454 chars (budget 1600)
- `memory\scribe\INDEX.md`: 2746 chars (budget 1600)
- `memory\synthesis\INDEX.md`: 5155 chars (budget 1600)
- `memory\verifier\INDEX.md`: 18251 chars (budget 1600)
- `memory\workspace\INDEX.md`: 49475 chars (budget 1600)
