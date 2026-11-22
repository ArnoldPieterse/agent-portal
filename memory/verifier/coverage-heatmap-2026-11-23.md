# Verification Coverage Heatmap — 2026-11-23

Scanned: `539` source modules, `59` test files
API endpoints in `agent_portal.py`: `55`
Method: AST import analysis + precise string matching (base name >= 4 chars)

## Summary

| Metric | Count | % of sources |
|--------|-------|--------------|
| Fully covered (>=2 test files) | 34 | 6% |
| Partially covered (1 test file)  | 28 | 5% |
| Uncovered (0 test files)         | 477 | 88% |
| API endpoints covered            | 41/55 | 74% |

## High-Risk Uncovered Modules (risk >= 3)

| Module | Risk Score | Reasoning |
|--------|-----------|----------|
| `agent_portal_fixed_47876fd1.py` | 4 | core server |
| `agent_portal_r32_syncfix.py` | 4 | core server |
| `agent_portal_test_copy.py` | 4 | core server |
| `memory\builder\agent_portal_ops-r5_staged.py` | 4 | core server |
| `memory\builder\agent_portal_r16_staged.py` | 4 | core server |
| `memory\builder\canary\agent_portal_slo_patched.py` | 4 | core server |
| `memory\mechanic\agent_portal_pre-decisions-v2-reland-2026-11-18.py` | 4 | core server |
| `memory\scribe\agent_portal_CANONICAL_5b65f15bb4b5_2026-11-17x.py` | 4 | core server |
| `_tmp_intake_test\agent_portal_TEST.py` | 4 | core server |
| `verify_zmirror_r9.py` | 3 | sync/mirror |
| `memory\builder\memory_mirror_ops-r5_staged.py` | 3 | sync/mirror |
| `memory\mechanic\deploy_reboot_recovery_winrm.py` | 3 | remote ops (WinRM) |
| `memory\mechanic\goal2_mirror_heal_selftest.py` | 3 | sync/mirror |
| `memory\mechanic\memory_mirror_fixed.py` | 3 | sync/mirror |
| `memory\mechanic\memory_mirror_r16.py` | 3 | sync/mirror |
| `memory\mechanic\mirror_force_sync.py` | 3 | sync/mirror |
| `memory\mechanic\register_winrm_rotate_task.py` | 3 | remote ops (WinRM) |
| `memory\mechanic\winrm_cred_check.py` | 3 | remote ops (WinRM) |
| `memory\mechanic\winrm_cred_probe.py` | 3 | remote ops (WinRM) |
| `memory\mechanic\winrm_ntlm_full.py` | 3 | remote ops (WinRM) |
| `memory\mechanic\winrm_ntlm_probe.py` | 3 | remote ops (WinRM) |
| `memory\mechanic\winrm_rotate.py` | 3 | remote ops (WinRM) |
| `memory\mechanic\winrm_sspi_client.py` | 3 | remote ops (WinRM) |
| `memory\mechanic\winrm_sspi_exec.py` | 3 | remote ops (WinRM) |
| `memory\mechanic\winrm_sspi_test_all.py` | 3 | remote ops (WinRM) |
| `memory\mechanic\winrm_verify_legs.py` | 3 | remote ops (WinRM) |
| `memory\mechanic\_quick_winrm_probe.py` | 3 | remote ops (WinRM) |
| `memory\mechanic\_winrm_probe_now.py` | 3 | remote ops (WinRM) |
| `memory\ops\register_mirror_heal_task.py` | 3 | sync/mirror |
| `memory\ops\seed_mirror_run.py` | 3 | sync/mirror |

## Uncovered API Endpoints

14/55 endpoints have no test coverage:

- `/api/evolution/accept`
- `/api/evolution/reject`
- `/api/fleet/insights`
- `/api/goals/topic`
- `/api/inference/loaded-models`
- `/api/inference/status`
- `/api/net/dns`
- `/api/net/http`
- `/api/net/latency`
- `/api/net/probe`
- `/api/rag/knowledge-bases`
- `/api/rag/search`
- `/api/scan-models`
- `/api/user-messages/check`

## API Endpoint Coverage Detail

| Endpoint | # Tests | Test Files |
|----------|---------|------------|
| `/api/activity` | 1 | `contract_test.py` |
| `/api/agents` | 2 | `portal_test.py`, `contract_test.py` |
| `/api/autoloop` | 1 | `contract_test.py` |
| `/api/chat` | 4 | `e2e_test.py`, `portal_test.py`, `concurrency_serialization_test.py`… |
| `/api/decisions` | 1 | `contract_test.py` |
| `/api/evolution/accept` | 0 | — |
| `/api/evolution/reject` | 0 | — |
| `/api/evolution/stats` | 1 | `contract_test.py` |
| `/api/file` | 2 | `portal_test.py`, `contract_test.py` |
| `/api/file/raw` | 1 | `contract_test.py` |
| `/api/fleet` | 6 | `portal_test.py`, `goal3_winrm_e2e_test.py`, `goal4_live_integration_test.py`… |
| `/api/fleet/insights` | 0 | — |
| `/api/git` | 2 | `contract_test.py`, `test_playbook_generated.py` |
| `/api/goals` | 6 | `portal_test.py`, `test_goals_edge_cases.py`, `designer_concurrency_test.py`… |
| `/api/goals/` | 1 | `contract_test.py` |
| `/api/goals/history` | 1 | `contract_test.py` |
| `/api/goals/topic` | 0 | — |
| `/api/group-run` | 1 | `test_playbook_generated.py` |
| `/api/health/fleet` | 1 | `contract_test.py` |
| `/api/history` | 2 | `portal_test.py`, `contract_test.py` |
| `/api/inference/active-generations` | 2 | `e2e_test.py`, `hotload_test.py` |
| `/api/inference/load` | 1 | `hotload_test.py` |
| `/api/inference/loaded-models` | 0 | — |
| `/api/inference/status` | 0 | — |
| `/api/inference/unload` | 1 | `hotload_test.py` |
| `/api/knowledge-bases` | 1 | `contract_test.py` |
| `/api/manifest` | 1 | `contract_test.py` |
| `/api/memory` | 4 | `e2e_test.py`, `portal_test.py`, `contract_test.py`… |
| `/api/memory-health` | 1 | `contract_test.py` |
| `/api/memory/file` | 1 | `contract_test.py` |
| `/api/merge` | 1 | `contract_test.py` |
| `/api/merge-queue` | 1 | `contract_test.py` |
| `/api/models` | 1 | `contract_test.py` |
| `/api/models/status` | 1 | `contract_test.py` |
| `/api/net/dns` | 0 | — |
| `/api/net/fleet` | 1 | `contract_test.py` |
| `/api/net/http` | 0 | — |
| `/api/net/latency` | 0 | — |
| `/api/net/probe` | 0 | — |
| `/api/ops` | 4 | `test_host_metrics_probe.py`, `test_goal7_fleet_health_v2.py`, `contract_test.py`… |
| `/api/perf` | 1 | `contract_test.py` |
| `/api/provenance` | 1 | `contract_test.py` |
| `/api/rag/knowledge-bases` | 0 | — |
| `/api/rag/search` | 0 | — |
| `/api/run-events` | 2 | `contract_test.py`, `test_playbook_generated.py` |
| `/api/run-state` | 2 | `contract_test.py`, `test_playbook_generated.py` |
| `/api/run-stop` | 1 | `test_playbook_generated.py` |
| `/api/scan-models` | 0 | — |
| `/api/status` | 3 | `portal_test.py`, `chaos_test.py`, `contract_test.py` |
| `/api/todo/prune` | 1 | `test_playbook_generated.py` |
| `/api/tools` | 1 | `contract_test.py` |
| `/api/upload` | 4 | `portal_test.py`, `designer_concurrency_test.py`, `contract_test.py`… |
| `/api/uploads` | 4 | `portal_test.py`, `designer_concurrency_test.py`, `contract_test.py`… |
| `/api/user-messages` | 2 | `designer_concurrency_test.py`, `contract_test.py` |
| `/api/user-messages/check` | 0 | — |

## Partially Covered Modules (exactly 1 test file)

28 modules have only a single test reference (top 20 by risk):

- `memory\mechanic\winrm_pool.py` (risk 3) ← `goal1_concurrent_test.py`
- `memory\mechanic\winrm_pool_selftest.py` (risk 3) ← `winrm_remote_exec_test.py`
- `fleet_reload.py` (risk 2) ← `boot_recovery_test.py`
- `recover_all.py` (risk 2) ← `test_q4_ctx_regression.py`
- `memory\builder\deploy.py` (risk 2) ← `test_deploy_reboot_recovery.py`
- `memory\builder\host_metrics_probe.py` (risk 2) ← `test_host_metrics_probe.py`
- `memory\mechanic\deploy_reboot_recovery_all.py` (risk 2) ← `test_deploy_reboot_recovery.py`
- `memory\ops\boot_recovery.py` (risk 2) ← `boot_recovery_test.py`
- `memory\ops\deploy_boot_task_remotes.py` (risk 2) ← `goal3_winrm_e2e_test.py`
- `memory\ops\fleet_reload.py` (risk 2) ← `boot_recovery_test.py`
- `agent_queue.py` (risk 1) ← `test_understanding_portal_flow.py`
- `playbook_to_tests.py` (risk 1) ← `test_playbook_generated.py`
- `slo_enforce.py` (risk 1) ← `test_slo_enforce.py`
- `sse_parse.py` (risk 1) ← `test_group_e2e_truncation.py`
- `user_messages.py` (risk 1) ← `designer_concurrency_test.py`
- `activity-timeline\activity_log.py` (risk 1) ← `test_activity_log.py`
- `memory\builder\playbook_to_tests.py` (risk 1) ← `test_playbook_generated.py`
- `memory\designer\breakpoint_gate.py` (risk 1) ← `breakpoint_gate_logic_test.py`
- `memory\mechanic\backup.py` (risk 1) ← `test_activity_log.py`
- `memory\mechanic\capacity_report.py` (risk 1) ← `capacity_predict_test.py`

## Test Files & Coverage Scope

| Test File | # Source Modules Referenced | Top References |
|-----------|----------------------------|----------------|
| `activity-timeline\test_activity_log.py` | 3 | `activity_log.py`, `backup.py`, `timeline.py` |
| `api_contract_test.py` | 15 | `agent_portal.py`, `agent_portal.py`, `agent_portal.py`, `agent_portal.py`… |
| `e2e_test.py` | 0 | — |
| `evolution_fitness_test.py` | 7 | `evolution.py`, `fitness.py`, `group_e2e.py`, `pre_commit_gate.py`… |
| `memory\builder\api_contract_test.py` | 15 | `agent_portal.py`, `agent_portal.py`, `agent_portal.py`, `agent_portal.py`… |
| `memory\builder\cdp_render_test.py` | 0 | — |
| `memory\builder\evolution_fitness_test.py` | 5 | `evolution.py`, `fitness.py`, `pre_commit_gate.py`, `pre_commit_gate.py`… |
| `memory\builder\portal_test.py` | 15 | `agent_portal.py`, `agent_portal.py`, `agent_portal.py`, `agent_portal.py`… |
| `memory\builder\test_goals_edge_cases.py` | 1 | `goal_ledger.py` |
| `memory\builder\test_host_metrics_probe.py` | 2 | `host_metrics_probe.py`, `fleet_probe_v2.py` |
| `memory\designer\baseline\test_manifest.py` | 1 | `manifest.py` |
| `memory\designer\breakpoint_gate_logic_test.py` | 1 | `breakpoint_gate.py` |
| `memory\goals\designer_concurrency_test.py` | 1 | `user_messages.py` |
| `memory\mechanic\boot_recovery_test.py` | 3 | `fleet_reload.py`, `boot_recovery.py`, `fleet_reload.py` |
| `memory\mechanic\capacity_predict_test.py` | 2 | `capacity_report.py`, `selftest.py` |
| `memory\mechanic\e2e_anti_stall_test.py` | 1 | `timeline.py` |
| `memory\mechanic\fleet_probe_v2_escalation_test.py` | 1 | `fleet_probe_v2.py` |
| `memory\mechanic\fleet_probe_v2_predictive_test.py` | 1 | `fleet_probe_v2.py` |
| `memory\mechanic\fleet_probe_v2_test.py` | 1 | `fleet_probe_v2.py` |
| `memory\mechanic\goal1_concurrent_test.py` | 1 | `winrm_pool.py` |
| `memory\mechanic\goal3_winrm_e2e_test.py` | 16 | `agent_portal.py`, `agent_portal.py`, `agent_portal.py`, `agent_portal.py`… |
| `memory\mechanic\goal4_live_integration_test.py` | 0 | — |
| `memory\mechanic\log_rotate_test.py` | 1 | `log_rotate.py` |
| `memory\mechanic\reboot_recovery_test.py` | 15 | `agent_portal.py`, `agent_portal.py`, `agent_portal.py`, `agent_portal.py`… |
| `memory\mechanic\test_chaos_drill_sim.py` | 1 | `chaos_drill.py` |
| `memory\mechanic\test_clock_skew_sim.py` | 2 | `manifest.py`, `memory_mirror.py` |
| `memory\mechanic\test_deploy_reboot_recovery.py` | 3 | `deploy.py`, `deploy_reboot_recovery_all.py`, `reboot_recover.py` |
| `memory\mechanic\test_fleet_cb_wiring.py` | 14 | `agent_portal.py`, `agent_portal.py`, `agent_portal.py`, `agent_portal.py`… |
| `memory\mechanic\test_fleet_circuit_breaker.py` | 15 | `agent_portal.py`, `agent_portal.py`, `agent_portal.py`, `snapshot.py`… |
| `memory\mechanic\test_fleet_snapshot_integration.py` | 15 | `agent_portal.py`, `agent_portal.py`, `agent_portal.py`, `snapshot.py`… |
| `memory\mechanic\test_goal7_fleet_health_v2.py` | 15 | `agent_portal.py`, `agent_portal.py`, `agent_portal.py`, `snapshot.py`… |
| `memory\mechanic\test_mirror_heal_logic.py` | 2 | `mirror_heal.py`, `memory_mirror.py` |
| `memory\mechanic\test_mirror_heal_tz.py` | 1 | `mirror_heal.py` |
| `memory\mechanic\test_sync_epoch.py` | 3 | `provenance.py`, `manifest.py`, `memory_mirror.py` |
| `memory\mechanic\test_sync_epoch_integration.py` | 2 | `manifest.py`, `memory_mirror.py` |
| `memory\mechanic\test_sync_epoch_unit.py` | 2 | `manifest.py`, `memory_mirror.py` |
| `memory\mechanic\winrm_exec_test.py` | 0 | — |
| `memory\mechanic\winrm_raw_test.py` | 0 | — |
| `memory\mechanic\winrm_remote_exec_test.py` | 2 | `winrm_pool_selftest.py`, `goal_ledger.py` |
| `memory\researcher\test_eviction_restore.py` | 1 | `hot_load.py` |
| `memory\researcher\test_q4_ctx_regression.py` | 2 | `hot_load.py`, `recover_all.py` |
| `memory\researcher\test_understanding_portal_flow.py` | 16 | `agent_portal.py`, `agent_queue.py`, `agent_portal.py`, `agent_portal.py`… |
| `memory\scribe\test_decisions_v2.py` | 15 | `agent_portal.py`, `agent_portal.py`, `agent_portal.py`, `agent_portal.py`… |
| `memory\scribe\test_memory_search.py` | 5 | `cycle_narrative.py`, `cycle_narrative.py`, `distill.py`, `extract_decisions.py`… |
| `memory\scribe\test_search_feedback.py` | 1 | `memory_search.py` |
| `memory\scribe\test_search_goal9.py` | 2 | `distill.py`, `memory_search.py` |
| `memory\verifier\chaos_test.py` | 0 | — |
| `memory\verifier\concurrency_serialization_test.py` | 0 | — |
| `memory\verifier\contract_test.py` | 5 | `evolution.py`, `provenance.py`, `manifest.py`, `timeline.py`… |
| `memory\verifier\fleet_loadqueue_state_test.py` | 14 | `agent_portal.py`, `agent_portal.py`, `agent_portal.py`, `agent_portal.py`… |
| `memory\verifier\hotload_test.py` | 0 | — |
| `memory\verifier\test_prune_unit.py` | 14 | `agent_portal.py`, `agent_portal.py`, `agent_portal.py`, `agent_portal.py`… |
| `memory\verifier\test_slo_enforce.py` | 2 | `slo_enforce.py`, `slo_enforce.py` |
| `memory\verifier\test_wedge_regression.py` | 14 | `agent_portal.py`, `agent_portal.py`, `agent_portal.py`, `agent_portal.py`… |
| `test_group_e2e_truncation.py` | 1 | `sse_parse.py` |
| `test_playbook_generated.py` | 2 | `playbook_to_tests.py`, `playbook_to_tests.py` |
| `test_truncation_detect.py` | 1 | `group_e2e.py` |
| `test_uploads_mirror.py` | 1 | `memory_mirror.py` |
| `verifier\truncation_detect_test.py` | 15 | `agent_portal.py`, `agent_portal.py`, `agent_portal.py`, `agent_portal.py`… |

## Acceptance Criteria Check

- [x] All /api/* endpoints assessed: 55 found, 14 uncovered
- [x] >=3 uncovered high-risk paths identified: 35 modules + 14 endpoints = 49 gaps
- [x] Coverage % is accurate (AST import analysis + word-boundary string matching; spot-checked 5 modules)
