# BUILDER INDEX â€” index of indexes for Builder lane (repin farm, staged patches, test suites).
Last updated: 2026-11-17 (Builder auto-loop: added portal-startup + css-tokens entries, verified token claim).

## Entries (keyword -> pointer | use case)
- portal startup / import-time C:\\Users PermissionError fix + start probe / assists Mechanic#2+Designer WCAG -> memory/builder/portal-startup-fix-2026-11-17.md   2026-11-17 fixed crash (alive:true); serving pending host boot-task restart (sandbox denies socket bind 10013)
- prune regression suite / 4 cases fixtures-only / ALL PASS -> memory/builder/prune_regression.py   move/stay/chunk-math/idempotent, exit non-zero on FAIL
- upload path-safety suite / drive letters + ../ + POSIX abs + bare uploads -> memory/builder/upload_path_safety.py   12/12 PASS 2026-11-15
- repin farm / index.html pin state / WCAG-AA stamp -> memory/builder/index-repin-r24-2026-11-14.md   latest repin round + canonical hash chain
- a11y closeout / 9c6b08e3 base / single-line swap doc -> memory/builder/a11y-repin-farm569-closeout-2026-11-14.md   closeout state for the a11y lane

- truncation detection / _is_truncated pure fn + 6-case unit fixture (B5)
  -> memory/builder/truncation-e2e-verify-2026-11-16.md   group_e2e.py sha12 9e4955611304; test_truncation_detect.py at root, PASS 6/6 2026-11-16
- portal startup crash / import-time PermissionError on C:\Users + re-verify after mirror regression -> memory/builder/portal-startup-fix-2026-11-17.md   2026-11-17 fixed + alive:true; sandbox socket-bind 10013 still blocks :8099 here
- CSS token extraction / all hexes -> :root vars (22 new) / ~35 component-specific hexes remain as one-off debt -> memory/builder/css-tokens-complete-2026-11-17.md   2026-11-17 407 var() uses; 30 in :root
- theme toggle verification / dark-mode + light-mode computed styles -> memory/builder/verify_theme_toggle_2026-11-17.md   2026-11-17
- pin-sha stale claim CLOSED / live pin 2a3ffa6ac79c three-way verified on disk (index.html sha == PIN_FILES == backup) -> memory/builder/pin-sha-stale-claim-closed-2026-11-17.md   2026-11-17 closes "flagged but not fixed" hot note

## Global pointers
- -> agent_portal.py  server;  -> index.html  frontend (pinned - see quarantine doc);  -> TODO.md plan

## Cycle-2 evidence (indexed 2026-11-16, Orchestrator seat - unblocks end-of-run sweep)
- -> memory/builder/pre_commit_gate.py   cycle-2 goal 1: CI gate script (4 suites) - evidence leaf
- -> memory/builder/ci-gate-2026-11-16.md   cycle-2 goal 1: CI gate build + first-run evidence
- -> memory/builder/ci-gate-acceptance-evidence-2026-11-16.md   cycle-2 goal 1: acceptance run (all suites green)
- -> memory/builder/canary_deploy.py   cycle-2 goal: canary deploy pipeline script
- -> memory/builder/wedge-watchdog-verify-2026-11-16.json   cycle-2 goal: wedge auto-recovery daemon verification output
- -> memory/builder/evolution_fitness_test.py   cycle-2 goal: evolution fitness test suite
- -> memory/builder/goal4_fitness_evidence.json   cycle-2 goal 4: fitness evidence data
- -> memory/builder/parity_guard.py   cycle-2 goal: sandbox<->root parity guard script
- -> memory/builder/playbook_to_tests.py   cycle-2 goal: executable test playbook generator
- -> memory/builder/hotpatch.py   cycle-2 goal: hot-patch with auto-rollback script
- -> memory/builder/agent-health-checks.jsonl   cycle-2 goal: agent capability health matrix data
- -> memory/builder/api_contract_test.py   cycle-2 goal 5: API contract pinning (--record/--check, fixtures in api-fixtures/)

- canary-goal1-first-real-deploy-2026-11-17.md — goal #1 first real canary deploy (BUILD_VERSION, all hosts green)