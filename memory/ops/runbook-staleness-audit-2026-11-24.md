# Runbook Staleness Audit - 2026-11-24 (Scribe, Tuesday idle-task)

## Scope
Checked 5 operational runbooks for file-path references that no longer resolve.

## Findings

### A. Moved files (24 refs — path changed, file exists elsewhere)
Runbooks reference scripts by bare filename or old path; the scripts now live in lane dirs.

| Runbook | Stale ref | Actual location |
|---------|-----------|-----------------|
| memory-tree-runbook.md | citation_map.py | memory/archivist/citation_map.py |
| memory-tree-runbook.md | decay_score.py | memory/archivist/decay_score.py |
| memory-tree-runbook.md | dup_detect.py | memory/archivist/dup_detect.py |
| memory-tree-runbook.md | kb_search.py | memory/archivist/kb_search.py |
| memory-tree-runbook.md | knowledge_graph_v3.py | memory/archivist/knowledge_graph_v3.py |
| memory-tree-runbook.md | memory_health.py | memory/archivist/memory_health.py |
| memory-tree-runbook.md | orphan_remediation.py | memory/archivist/orphan_remediation.py |
| memory-tree-runbook.md | search-index.json | memory/archivist/search-index.json |
| memory-tree-runbook.md | snapshot.py | memory/archivist/snapshot.py |
| mechanic/runbook.md | backup.py | memory/mechanic/backup.py |
| mechanic/runbook.md | deploy_one_host.py | memory/mechanic/deploy_one_host.py |
| mechanic/runbook.md | disk_monitor.py | memory/mechanic/disk_monitor.py |
| mechanic/runbook.md | health_check.py | memory/mechanic/health_check.py |
| mechanic/runbook.md | log_rotate.py | memory/mechanic/log_rotate.py |
| mechanic/runbook.md | memory_mirror_fixed.py | memory/mechanic/memory_mirror_fixed.py |
| mechanic/runbook.md | net_probe.py | memory/mechanic/net_probe.py |
| mechanic/runbook.md | postmortem_gen.py | memory/mechanic/postmortem_gen.py |
| mechanic/runbook.md | revert_sentinel.py | memory/mechanic/revert_sentinel.py |
| boot-deployment-runbook.md | deploy_boot_task.py | memory/ops/deploy_boot_task.py |
| boot-deployment-runbook.md | deploy_startup_folder.py | memory/ops/deploy_startup_folder.py |
| citation-phantom-triage-runbook.md | extract_decisions.py | memory/scribe/extract_decisions.py |
| citation-phantom-triage-runbook.md | weekly_digest.py | memory/archivist/weekly_digest.py |
| citation-phantom-triage-runbook.md | winrm_pool.py | memory/mechanic/winrm_pool.py |
| citation-phantom-triage-runbook.md | winrm_sspi_client.py | memory/mechanic/winrm_sspi_client.py |

**Root cause:** Scripts were organized into lane directories (archivist/, mechanic/, scribe/) but runbooks written earlier still use bare filenames or the old flat layout.

### B. Genuinely missing (9 refs — file does not exist anywhere)
| Ref | Likely explanation |
|-----|--------------------|
| _boot_fleet.vbs | Renamed to boot_recovery.vbs (memory/ops/) |
| _boot_recover.vbs | Same as above |
| FleetBootRecovery.vbs | Same — current name is boot_recovery.vbs |
| portal_hidden.vbs | Never created or removed; no replacement found |
| recover_hidden.vbs | Same |
| fleet_reload_result.json | Temporary artifact, cleaned up |
| recover_result.json | Temporary artifact, cleaned up |
| serial_e2e_wait.py | Removed; functionality likely in run_steps.py |
| hotload-log.json | Typo — actual file is memory/ops/hotload-log.jsonl |

## Impact Assessment
- **Category A (moved):** Low risk for humans reading the runbook, but HIGH risk for autonomous execution. If a remediation script tries to `python citation_map.py` from repo root, it will fail with FileNotFoundError. The closed-loop autonomy lane depends on these paths being correct.
- **Category B (missing):** Medium risk. The VBS boot scripts were consolidated; the temp JSON files are expected to be ephemeral.

## Recommended Fix
1. Update all 24 Category-A references in the 5 runbooks to use full relative paths from repo root.
2. For Category-B: replace `FleetBootRecovery.vbs` / `_boot_*.vbs` refs with `memory/ops/boot_recovery.vbs`; mark temp JSON files as ephemeral (not expected to persist).
3. Add a CI-style check (could be part of Verifier's pointer integrity pass) that validates all file references in runbooks resolve.

## Effort Estimate
~15 min for the path fixes (mechanical search-and-replace); ~5 min for the ephemeral-file annotations.
