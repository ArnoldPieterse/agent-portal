# Runbook Executability Audit
Generated: 2026-11-25 07:07 UTC by Mechanic (assist for Forge goal #1)

## Summary
- Total .md files in memory/ops/: 185
- Classified as procedures/runbooks: 53
- Already have corresponding script: 12
- WITHOUT script (conversion candidates): 41

## Priority 1: Recurring procedures without scripts (convert first)

| File | Size | Script |
|------|------|--------|
| autonomous-remediation-loop-runbook-2026-11-24.md | 5595B | — |
| idle-maintenance-rotation-2026-11-24.md | 4443B | — |
| cross-seat-protocol.md | 2896B | — |
| data-freshness-escalation-protocol-2026-11-24.md | 2743B | — |
| fleet-monitoring-cadence.md | 2510B | — |
| git-hygiene.md | 2120B | — |

## Priority 2: One-off procedures without scripts (convert if still relevant)

| File | Size |
|------|------|
| anomalies-2026-11-22.md | 9425B |
| runbook-notes.md | 8211B |
| windows-runbook.md | 7749B |
| non-sandbox-queue.md | 7226B |
| background-goals-execution-plan-2026-11-18.md | 6727B |
| sandbox-egress-selfprobe-workaround-2026-11-19.md | 6250B |
| runbook-autonomy.md | 6013B |
| memory-tree-runbook.md | 4894B |
| schtask-deps.md | 4732B |
| goal-progress-2026-11-16.md | 4722B |
| merge-queue-git-progress-2026-11-16.md | 3753B |
| mechanic-goal3-closure-2026-11-15.md | 3711B |
| scan_goals-scope-fix-2026-11-19.md | 3666B |
| ui-asset-inventory-2026-11-23.md | 3412B |
| verifier-git-health-2026-11-15b.md | 3083B |
| fleet-throughput-fix-2026-11-23.md | 3046B |
| browser-gate-decision-tree.md | 2879B |
| mechanic-reboot-dryrun-remotes-2026-11-15.md | 2865B |
| quarantine-index-html-variants-2026-11-13.md | 2792B |
| git-access-denied-fix-2026-11-23.md | 2666B |
| scheduler-consolidation-2026-11-23.md | 2627B |
| browser-acceptance-workaround.md | 2567B |
| pointer-false-positive-fix-2026-11-23.md | 2534B |
| portal-split-seams-2026-11-17.md | 2468B |
| hotline-v2.md | 2388B |
| orch-veto-wholecopy-v3-2026-11-16.md | 2378B |
| mechanic-researcher-alias-diagnosis-2026-11-16.md | 2198B |
| builder-fleet-8099-sweep-r80-2026-11-14.md | 2100B |
| boot-detection-runbook.md | 1968B |
| schtask-bottleneck-synthesis-2026-11-23.md | 1910B |
| workflow-improvement-load-probe-no-schtasks.md | 1852B |
| agent-onboarding-playbook.md | 1813B |
| schtasks-cli-fallback-workflow-2026-11-23.md | 1783B |
| mechanic-goal3-red-leg-blocked-2026-11-15.md | 1501B |
| schtask-sandbox-limitation.md | 1166B |

## Already executable (script exists)

| File | Script |
|------|--------|
| cycle-transition-checklist.md | `cycle_transition.py` |
| live-run-checklist-white-seat.md | `unblock_all_live_runs.py` |
| live-leg-runbook-2026-11-20.md | `ac_a2_live_leg_r21.py` |
| cycle3-readiness-snapshot-2026-11-17.md | `snapshot.py` |
| reboot-dryrun-remotes-2026-11-15.md | `reboot_dryrun_r2.py` |
| fleet-placement-snapshot-2026-11-22.md | `snapshot.py` |
| boot-deployment-runbook.md | `verify_boot_deployment.py` |
| mirror-revert-incident-health-check-2026-11-20.md | `mirror_revert_correlate.py` |
| mirror-revert-guard-winrm-creds.md | `mirror_revert_correlate.py` |
| mirror-revert-prevention-2026-11-18.md | `mirror_revert_correlate.py` |
| remote-verify-runner-2026-11-20.md | `run_remote_verify.py` |
| runbook-cockpit-feed-refresh-deploy-2026-11-24.md | `deploy.py` |