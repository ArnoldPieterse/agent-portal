# BUILDER INDEX — index of indexes for Builder lane (repin farm, staged patches, test suites).
Last updated: 2026-11-27 (this pass = ledger-upkeep: regenerated stale root goal_ledger.json; fleet 79->89/111, mechanic 2->10)
- evidence-ledger-regen-mechanic-closeout-2026-11-27.md -> goal_ledger.json (root)   **ASSIST (owner: Mechanic)**: root SSOT goal_ledger.json was stale (fleet 79/111=71%, mechanic 2/10) vs live parse 89/111=80%, mechanic 10/10; regenerated via `goal_ledger.py --json`; verified written file flips mechanic to 10/10 (all via=marker); spot-checked goal #9 audit 8/8 runbooks exist on disk. Did NOT re-do Mechanic's work nor re-fight the marker-revert wall.
- assist-archivist-goal1-autonomy-progression-2026-11-26.md -> memory/archivist/autonomy_progression.py   **ASSIST (owner: Archivist, goal #1)**: runnable model builder + selftest 6/6 PASS exit 0; fleet-level progression VERIFIED R^2=0.7729 on 5 real cycles (logistic/saturation > linear 0.441), interventions/cycle flat (R^2=0.755, not escalating), steady-state(85%) already crossed by c18; per-agent ranking + trend classes from maturity scorecard (directional only — single snapshot, no fabricated per-agent R^2); artifacts autonomy-progression.json/.md. Remaining: capture >=3 dated per-agent snapshots to promote per-agent ETAs to verified.
- knowledge_stream_smoke_test_evidence_2026-11-26.md -> memory/builder/knowledge_stream_smoke_test.py   **CONTRIBUTION (MIND LAB idea)**: "verify knowledge streams feed the portal"; smoke test execs real MIND LAB source in isolated temp HERE + stubbed umq_add; 13/13 PASS exit 0 — T2 JS<->Python vein bit-parity 11368/11368 (neg coords + >2^31 seeds), idea->portal feed (fed_to_portal:True + umq_add broadcast), solidify->solidified.jsonl, full-stream determinism
- swap_guard_evidence_2026-11-26.md -> memory/builder/swap_guard_evidence_2026-11-26.md   **Goal 9 REACHED**: Model-Swap Convergence Guard (swap_guard.py); 4 pre-flight checks (in-flight goals, VRAM, alias resolution, FSM state); selftest ALL PASS 6 assertions; live run blocked Builder with 3 in-flight goals; before/after snapshots emit agents_json_sha+fsm_state for Forge
- event_bus_evidence_2026-11-26.md -> memory/builder/event_bus_evidence_2026-11-26.md   **Goal 3 REACHED**: Convergence Event Bus (event_bus.py); append-only JSONL + in-process pub/sub + SSE + cursor replay; selftest ALL PASS 5 assertions (broadcast 0.5ms, replay correct, bounded backpressure); live emit+replay verified
- convergence_fsm_evidence_2026-11-26.md -> memory/builder/convergence_fsm_evidence_2026-11-26.md   **Goal 1 REACHED**: Convergence State-Machine SSOT (convergence_fsm.py); selftest PASS 15 legal accepted + illegal rejected/logged; fleet-mode.json stamped fsm_state+fsm_validated; writer+controller+sentinel all emit through FSM
- seat_draft_autonomy_evidence_2026-11-26.md -> memory/builder/seat_draft_autonomy_evidence_2026-11-26.md   **Goal 7 REACHED**: Seat-Draft Autonomy Validator v2 (seat_draft_autonomy.py); 7 human-gate patterns; selftest PASS (gate flagged on line, clean passes, reproducible); live builder.md 7 clean/3 flagged
- regression_dispatcher_evidence_2026-11-26.md -> memory/builder/regression_dispatcher_evidence_2026-11-26.md   **Goal 8 REACHED**: Convergence Regression Auto-Remediation Dispatcher (regression_dispatcher.py); detect->act consumes convergence_fsm; on REGRESSING opens EXACTLY ONE remediation goal in correct lane (cause->lane map) + tracks via remediation-tracker.jsonl; idempotent (no dup, close-twice no-op); closure stamps [REACHED] + flips FSM ->CONVERGING; selftest PASS all 3 ACs
- touch_census_evidence_2026-11-26.md -> memory/builder/touch_census_evidence_2026-11-26.md   **Goal 6 REACHED**: Human-Touchpoint Census + Removal Tracker (touch_census.py); selftest PASS (seeded set reproduced, deterministic, removal drops count 4->3); live census 10 touches -> 7 removable-now/3 removable-later
- contracts_evidence_2026-11-26.md -> memory/builder/contracts_evidence_2026-11-26.md   **Goal 5 REACHED**: Data-Contract Registry + Lint (contracts.py); 8 contracts registered; --lint PASS on live files; selftest PASS (seeded missing-field caught w/ exact path, type-drift caught, stubs parseable)
- infra_health_evidence_2026-11-26.md -> memory/builder/infra_health_evidence_2026-11-26.md   **Goal 4 REACHED**: Autonomy-Infra Self-Health Probe (infra_health.py); selftest PASS (clean->all healthy, cleared-marker flagged missing, stale flagged); live run all_healthy:true on real artifacts; JSONL schema stable
- cycle20_goalsetting_evidence_2026-11-26.md -> memory/builder/cycle20_goalsetting_evidence_2026-11-26.md   Cycle 20 goals proposed: 10 goals (autonomous closeout + self-healing infra + steady-state contracts); all new vs closed_topics.json
- cycle18_goalsetting_evidence_2026-11-25.md -> memory/builder/cycle18_goalsetting_evidence_2026-11-25.md   Cycle 18 goals proposed: 10 goals, Fleet Autonomy Convergence
- assist_mechanic_g1_seattrend_2026-11-25.md -> memory/builder/assist_mechanic_g1_seattrend_2026-11-25.md   Assist (owner Mechanic): seat_probe.py latency-trend->degrading; selftest 5/5 PASS
- goal_inherit_evidence_2026-11-25.md -> memory/builder/goal_inherit_evidence_2026-11-25.md   Goal #7: cross-cycle inheritance generator; selftest 3/3 PASS
- convergence_trend_evidence_2026-11-25.md -> memory/builder/convergence_trend_evidence_2026-11-25.md   Goal #8: /api/convergence/trend endpoint; 5 pts/metric, cache OK
- seat_draft_validate_evidence_2026-11-25.md -> memory/builder/seat_draft_validate_evidence_2026-11-25.md   Goal #9: draft validation pipeline; 80 goals/8 files, 77P/3F
- cycle_retro_gen_evidence_2026-11-25.md -> memory/builder/cycle_retro_gen_evidence_2026-11-25.md   Goal #10: retro generator; 7 sections, all refs resolve
- intervention-logger-evidence-2026-11-25.md -> memory/builder/intervention-logger-evidence-2026-11-25.md   Goal #4: pattern-based human intervention detection; selftest 9/9 PASS
- steady-state-scheduler-evidence-2026-11-25.md -> memory/builder/steady-state-scheduler-evidence-2026-11-25.md   Goal #3: scheduler adapts cadence daily<->biweekly on STEADY-STATE; selftest 6/6 PASS
- evidence-cockpit-frontend-2026-11-24.md -> memory/builder/evidence-cockpit-frontend-2026-11-24.md
- evidence-cockpit-feed-loop-verified-2026-11-24.md -> memory/builder/evidence-cockpit-feed-loop-verified-2026-11-24.md   proves full detect->remediate loop: feed_refresh.py -> cockpit_staleness_monitor FRESH (assists Verifier #2 cycle-14)   closes 4 cycle-7 cockpit UNCITED claims (goals #2/#5/#6/#8 cite ui/cockpit.js, outside memory/ scan pattern); ground truth re-verified 2026-11-24
- Policy Conflict Detector / scans memory/ops policy files + runbooks for overlapping rules prescribing different actions on the same trigger; --scan/--selftest/--fixture -> memory/builder/policy_conflict.py (13.7KB; report -> memory/ops/policy-conflict-report.json)
- Archivist goal #2 assist / knowledge_graph_v3.py + 'evidence'(118) + 'dependency'(57) edge types; all 6 types present, 1722 edges, JSON 2.0MB; remaining AC = git temporal run on White -> memory/builder/kgv3-edge-types-assist-archivist-goal2-2026-11-21.md (Builder assist: Mechanic Goal 1 concurrent pool load test — 8 parallel cmds PASS, no cross-contamination)

<483 chars of arguments you sent, already written to memory/builder/INDEX.md; elided to save room. Not tool output; the file on disk holds it.
- Goal#2 api-client layer / ui/api-client.js built (150L): DI retry core (exp backoff+jitter, max3), TTL-30s cache, 17 typed wrappers, UMD; static gate PASS; node test authored; REMAINING wire core.js + run node test -> memory/builder/api_client_layer_increment1-2026-11-20.md
- Goal#1 component-refactor regression / 0 document.createElement left in core.js; reference-integrity PASS (all UI.* refs resolve: icon/iconSized->⚠missing:icons.js, emptyState/skeleton->⚠missing:core.js); script order icons<components<core OK; structural substitute for pixel diff (no browser in sandbox) -> memory/builder/component_refactor_regression_2026-11-20.md   2026-11-20 own goal #1 closure support
- citation audit / Archivist goal #2 assist: built+ran citation_audit.py, 49 external URLs live-checked, filtered accuracy ~86%, 5 genuinely dead links identified -> memory/builder/citation-audit-assist-archivist-goal2-2026-11-19.md | memory/archivist/citation_audit.py + memory/archivist/citation-audit-cycle5-report.md
- anti-phantom claim guard / verify_claims.py scans goal files, flags verified-markers whose cited artifact is missing; found 4 archivist PHANTOMs explaining the 2/10 stall -> memory/builder/evidence-verify-claims-guard-2026-11-19.md | memory/ops/verify_claims.py + memory/ops/claim-phantom-report.md
- Designer Goal#6 skeleton screens / .skeleton CSS + shimmer keyframe in app.css:314-318; UI.skeleton() helper core.js:460; pre-fetch injection core.js:474-476; per-load re-inject w/ dataset.loaded guard uploads.js:330+348; prefers-reduced-motion wrap app.css:346-350 -> memory/builder/designer-goal6-skeleton-2026-11-19.md   2026-11-19 cross-assist (owner: Designer); option (c) verified leaf recreated
- Designer Goal#2 padding consolidation / last 5 hardcoded px in padding/margin -> var(--sp-*); --sp-2 added to tokens.css; 0 remaining, 210 total sp refs -> memory/builder/assist-designer-goal2-padding-2026-11-19.md   2026-11-19 cross-assist (owner: Designer); option (d)
- Designer Goal#1 JS-scope tokenization / 20 raw hex -> var() across 4 JS files + 13 new tokens in tokens.css / raw reduced ~56 to 4 -> memory/builder/designer-goal1-js-tokenization-2026-11-19.md   2026-11-19 cross-assist (owner: Designer); option (d)
- log_rotate.py WinError 183 fix / shift loop crashed on Windows when .log.5 already existed (prior run died mid-rotation) / clear rename target before os.rename + repro test -> memory/builder/log_rotate_winerror183-fix-2026-11-18.md   2026-11-18 cross-assist (owner: Mechanic); PASS steady-state + 5 repeat rotations
- phantom-open repair / Researcher goals 7 & 8 `(verified:` missing closing paren → dashboard saw them OPEN though evidence leaves existed / formatting-only fix, all 8 goal files now balanced -> memory/builder/researcher-goals7-8-paren-repair-2026-11-18.md   2026-11-18 cross-assist (owner: Researcher); option (c) ledger/evidence upkeep
- Designer Goal#1 token audit / INDEPENDENT re-parse CONFIRMS 36 hard-coded hex outside BOTH token blocks (:root dark + [data-theme=light] light) = matches ORCH-VERIFY; line-by-line list + closure path for Designer -> memory/builder/designer-goal1-token-verify-2026-11-18.md   2026-11-18 cross-assist (owner: Designer); NOT closed - Designer still owns the var() replacement
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
- -> ⚠missing:memory/builder/agent-health-checks.jsonl   cycle-2 goal: agent capability health matrix data
- -> memory/builder/api_contract_test.py   cycle-2 goal 5: API contract pinning (--record/--check, fixtures in api-fixtures/)

- canary-goal1-first-real-deploy-2026-11-17.md � goal #1 first real canary deploy (BUILD_VERSION, all hosts green)
- scribe-g4-memhealth-dom-node-2026-11-18.md — 2026-11-18 Builder cross-assist: added #memHealthBody to index.html (Scribe goal #4)
- durable-check-scribe-goal6-2026-11-18.md — 2026-11-18 Builder cross-assist: durable_check.py built + CI-wired (Scribe goal #6)
- designer-goal5-components-2026-11-18.md — 2026-11-18 Builder cross-assist: wrote memory/portal/components.md (6 components + token table) for Designer goal #5
- designer-goal8-state-patterns-2026-11-18.md — 2026-11-18 Builder cross-assist: implemented .state-loading/.state-error/.state-empty/.state-conn-lost in ui/app.css (all tokens, 0 hex) + documented in components.md §7 (Designer goal #8)
- designer-goal2-fleet-states-2026-11-18.md — 2026-11-18 Builder cross-assist: loading/error/empty states + responsive SVG added to ui/fleet_topology.js (sha12=294aaca2ec20) + CSS in app.css (Designer goal #2, partial - screenshots still needed)
- assist-designer-goal1-tokens-2026-11-19.md — 2026-11-19 Builder cross-assist: replaced last 3 hard-coded hex (#3ddc84 x2, #4cd964) with var(--ok); post-fix scan = 0 truly hard-coded hex outside token definitions (Designer goal #1, near-closure; remaining hex only in var() fallbacks)
- designer_goal5_notif_verify_2026-11-19.md — 2026-11-19 Builder cross-assist: static verification of Designer goal #5 notification system (toast+bell fully implemented, all 4 triggers wired, CSS present); browser-rendering leg remains

- Designer Goal#10 print reverify / Orchestrator stale-overclaim flag REFUTED: #printReportBtn + page-break-after both present in live ui/core.js+app.css; sole gap = browser visual check -> memory/builder/designer-goal10-print-reverify-2026-11-19.md   2026-11-19 cross-assist (owner: Designer); option (c) stale-claim closure

## Linked content (KG orphan remediation 2026-11-19)
- [MEMORY.md](memory/builder/MEMORY.md)
- [TODO.md](memory/builder/TODO.md)
- [anomaly-ar14-writepath-evidence.md](memory/builder/anomaly-ar14-writepath-evidence.md)
- Goal#4 error boundary / showPanelError 5/5 panels wired (actBody, fleetBody, gitStatus, goalsBody, filesList); in-process verification PASS; live browser test pending -> memory/builder/error_boundary_increment3-2026-11-20.md
- Assist Mechanic G7: perf_profile.py --run-once flag + FleetPerfProfile added to register_tasks.py (selftest PASS, schedulable) -> memory/builder/assist-mechanic-g7-perf-profile-2026-11-20.md
- Archivist Goal#4 circular-ref confirm / the 2 "circular ref" flags are A->A self-pointers (archivist/INDEX.md L10 auto-self-entry; workspace/INDEX.md L76 regex over-match of inline code) -> 0 genuine cycles, final box satisfied -> memory/builder/xref-circular-refs-artifact-confirm-2026-11-21.md   2026-11-21 cross-assist (owner: Archivist)
- Archivist Goal#2 temporal AC: knowledge_graph_v3.py report now prints `temporal (any: git|mtime)`; full-tree run 7663/7663 (100%) >= 50% AC met (additive change, graph content unchanged, no git init) -> memory/builder/kgv3-temporal-ac-assist-archivist-goal2-2026-11-22.md   2026-11-22 cross-assist (owner: Archivist)
- [playbook_runner.py](memory/builder/playbook_runner.py) - markdown playbook parser/executor with step-level rollback (cycle-2 goal 1, verified 2026-11-18)
- [runbook_exec.py](memory/builder/runbook_exec.py) - runbook parser + executor: parses memory/ops/runbooks/*.md into steps (command/expected_output/timeout/rollback), --dry-run, --simulate-failure N triggers rollback of prior steps; 2026-11-23 Goal#9 verified (safe_test.md: 3 steps parsed; failure@2 -> rollback + full report)
- assist_scribe_g4_convergence_digests_2026-11-25.md -> memory/builder/assist_scribe_g4_convergence_digests_2026-11-25.md   Assist (owner Scribe): convergence-digests.jsonl 3 entries, all metrics + watch items verified
- evidence_goal1_prioritizer_2026-11-25.md -> memory/builder/evidence_goal1_prioritizer_2026-11-25.md   Goal #1 (verified): goal_prioritizer.py convergence-informed ranking; selftest 5/5 PASS
- evidence-stealth-workflows-2026-11-26.md -> memory/builder/evidence-stealth-workflows-2026-11-26.md   Goal #11: top-3 workflows packaged, 21/21 tests PASS
- evidence-js-brace-balance-2026-11-26.md -> memory/builder/evidence-js-brace-balance-2026-11-26.md   Assist (owner Forge/Pixel): brace-balance check 28 ui/*.js; 19 PASS, 9 FP (regex/template limitation); node --check required as primary gate
- cycle19_goalsetting_evidence_2026-11-26.md -> memory/builder/cycle19_goalsetting_evidence_2026-11-26.md   Cycle 19 goals proposed: 10 goals, post-convergence sustainability
