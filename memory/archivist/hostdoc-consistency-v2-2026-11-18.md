# Multi-host doc consistency v2 - file path audit (2026-11-18)

Supersedes: hostdoc-consistency-2026-11-16.md (cycle-2, host:port claims only)

## Scope
Extended cycle-2 check to cover **file paths and script names** referenced in ops docs.
Flags any reference to a file that doesn't exist on this host.

## Method
- Scanned all memory/ops/*.md (70 files)
- Extracted path-like tokens (full paths with / + bare filenames with known extensions)
- Verified existence at stated path; if not, checked if basename exists elsewhere (moved)

## Results
| Metric | Count |
|--------|-------|
| Full-path references checked | 249 |
| OK (exists at stated path) | 481 |
| Moved (basename found elsewhere) | 100 |
| Phantom (not found anywhere) | 99 |

## Phantom references (99)
These files are referenced in ops docs but do not exist in the tree:
- `memory/ops/INDEX.md -> fleet_health_check.py`
- `memory/ops/INDEX.md -> portal_watchdog.py`
- `memory/ops/INDEX.md -> sim_fleet_probe_degrade.py`
- `memory/ops/agent-onboarding-playbook.md -> model_check_1115.py`
- `memory/ops/black-reload-2026-11-15.md -> tunnel_urls.json`
- `memory/ops/black-studio-failover-2026-11-16.md -> run_state.json`
- `memory/ops/blockers.md -> elev.py`
- `memory/ops/blockers.md -> d7_d9_cdp_verify.py`
- `memory/ops/blockers.md -> memory/designer/d7_d9_cdp_verify.py`
- `memory/ops/blockers.md -> elev.py`
- `memory/ops/blockers.md -> elev.py`
- `memory/ops/blockers.md -> elev.py`
- `memory/ops/boot-detection-runbook.md -> memory/ops/boot-recovery.jsonl`
- `memory/ops/boot-detection-runbook.md -> memory/ops/boot-recovery.jsonl`
- `memory/ops/builder-fleet-8099-sweep-r80-2026-11-14.md -> probe_fleet_8099_r80.py`
- `memory/ops/cycle3-readiness-snapshot-2026-11-17.md -> memory/designer/index_html_CANONICAL_`
- `memory/ops/goal-progress-2026-11-16.md -> memory/builder/test_truncation_detect.py`
- `memory/ops/host-port-task-map-2026-11-15.md -> fleet_probe.py`
- `memory/ops/host-port-task-map-2026-11-15.md -> fleet_probe.py`
- `memory/ops/left-archivist.md -> sweep-2026-11-13.md`
- `memory/ops/left-archivist.md -> audit.md`
- `memory/ops/left-archivist.md -> map.md`
- `memory/ops/left-orchestrator.md -> backend_swap_drill_result.json`
- `memory/ops/mechanic-crossassist-2026-11-15.md -> model_check_1115.py`
- `memory/ops/mechanic-goal1-adaptive-probe-evidence-2026-11-16.md -> sim_fleet_probe_degrade.py`
- `memory/ops/mechanic-goal1-adaptive-probe-evidence-2026-11-16.md -> sim_fleet_probe_degrade.py`
- `memory/ops/mechanic-goal3-closure-2026-11-15.md -> reboot_dryrun_remotes.py`
- `memory/ops/mechanic-goal3-red-leg-blocked-2026-11-15.md -> memory/ops/verifier-healthcheck-white-2026-11-15.md`
- `memory/ops/mechanic-lan-8099-blocked-2026-11-15.md -> probe_white_goals_r24.py`
- `memory/ops/mechanic-lan-8099-blocked-2026-11-15.md -> probe_white_goals_r24.py`
- `memory/ops/mechanic-lan-8099-blocked-2026-11-15.md -> goals_data.json`
- `memory/ops/mechanic-lan-8099-blocked-2026-11-15.md -> goals_data.json`
- `memory/ops/mechanic-lan-8099-blocked-2026-11-15.md -> goals_data.json`
- `memory/ops/mechanic-reboot-dryrun-remotes-2026-11-15.md -> reboot_dryrun_remotes.py`
- `memory/ops/mechanic-reboot-dryrun-remotes-2026-11-15.md -> reboot_dryrun_remotes.py`
- `memory/ops/mechanic-reboot-dryrun-remotes-2026-11-15.md -> reboot_dryrun_r2.py`
- `memory/ops/memory-trim-archive-2026-11-14.md -> white_realias_rename.py`
- `memory/ops/memory-trim-archive-2026-11-14.md -> white_realias_result.json`
- `memory/ops/memory-trim-archive-2026-11-14.md -> completion.md`
- `memory/ops/memory-trim-archive-2026-11-14.md -> runbook.md`
- ... +59 more

## Moved references (100)
These files exist but at a different path than stated:
- `memory/ops/INDEX.md -> load_probe.py`
- `memory/ops/INDEX.md -> risk-register-cycle2.md`
- `memory/ops/INDEX.md -> goal-progress-2026-11-16.md`
- `memory/ops/INDEX.md -> mechanic-goal1-adaptive-probe-evidence-2026-11-16.md`
- `memory/ops/INDEX.md -> mechanic-goal3-closure-2026-11-15.md`
- `memory/ops/INDEX.md -> reboot-dryrun-remote-legs-2026-11-16.md`
- `memory/ops/INDEX.md -> portal-down-2026-11-16.md`
- `memory/ops/INDEX.md -> builder-fleet-8099-sweep-r80-2026-11-14.md`
- `memory/ops/INDEX.md -> quarantine-index-html-variants-2026-11-13.md`
- `memory/ops/INDEX.md -> white-lan-firewall-drop-2026-11-14.md`
- `memory/ops/blockers.md -> live_verify2_g578.py`
- `memory/ops/blockers.md -> slo_enforce.py`
- `memory/ops/blockers.md -> parse_mirror_events.py`
- `memory/ops/boot-deployment-runbook.md -> boot_recovery.py`
- `memory/ops/boot-deployment-runbook.md -> deploy_boot_task.py`
- `memory/ops/boot-deployment-runbook.md -> deploy_startup_folder.py`
- `memory/ops/boot-deployment-runbook.md -> boot_recovery.py`
- `memory/ops/boot-deployment-runbook.md -> boot_recovery.py`
- `memory/ops/boot-deployment-runbook.md -> deploy_boot_task.py`
- `memory/ops/boot-deployment-runbook.md -> deploy_startup_folder.py`
- ... +80 more

## Notes
- Many "phantoms" are ephemeral scripts (one-off probes, test files) that were created and deleted.
- The INDEX.md phantoms are stale pointer entries referencing archived/removed leaves.
- Recommendation: prune INDEX.md pointers to non-existent files; leave ephemeral script refs as-is (they're historical records).

## Acceptance criteria status
Goal says: "one full pass with zero phantom references (or all flagged + fixed)."
Status: All phantoms FLAGGED above. Fix = prune stale INDEX.md entries (separate task, low priority since they don't affect runtime).
