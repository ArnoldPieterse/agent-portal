# BUILDER INDEX — index of indexes for Builder lane (repin farm, staged patches, test suites).
Last updated: 2026-11-19 (Builder assist: Archivist Goal 2 citation_audit.py built+ran, 49 URLs checked, report with filtered analysis)

## Entries (keyword -> pointer | use case)
- citation audit / Archivist goal #2 assist: built+ran citation_audit.py, 49 external URLs live-checked, filtered accuracy ~86%, 5 genuinely dead links identified -> memory/builder/citation-audit-assist-archivist-goal2-2026-11-19.md | memory/archivist/citation_audit.py + memory/archivist/citation-audit-cycle5-report.md
- anti-phantom claim guard / verify_claims.py scans goal files, flags verified-markers whose cited artifact is missing; found 4 archivist PHANTOMs explaining the 2/10 stall -> memory/builder/evidence-verify-claims-guard-2026-11-19.md | memory/ops/verify_claims.py + memory/ops/claim-phantom-report.md
- Designer Goal#6 skeleton screens / .skel CSS + shimmer keyframe in app.css; skeleton HTML injected in fleetUpdate() core.js + goalsLoad() uploads.js with dataset.loaded guard; 4 host rows + 5 goal tiles pre-fetch; prefers-reduced-motion respected -> memory/builder/designer-goal6-skeleton-2026-11-19.md   2026-11-19 cross-assist (owner: Designer); option (d)
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
- -> memory/builder/agent-health-checks.jsonl   cycle-2 goal: agent capability health matrix data
- -> memory/builder/api_contract_test.py   cycle-2 goal 5: API contract pinning (--record/--check, fixtures in api-fixtures/)

- canary-goal1-first-real-deploy-2026-11-17.md � goal #1 first real canary deploy (BUILD_VERSION, all hosts green)
- scribe-g4-memhealth-dom-node-2026-11-18.md — 2026-11-18 Builder cross-assist: added #memHealthBody to index.html (Scribe goal #4)
- durable-check-scribe-goal6-2026-11-18.md — 2026-11-18 Builder cross-assist: durable_check.py built + CI-wired (Scribe goal #6)
- designer-goal5-components-2026-11-18.md — 2026-11-18 Builder cross-assist: wrote memory/portal/components.md (6 components + token table) for Designer goal #5
- designer-goal8-state-patterns-2026-11-18.md — 2026-11-18 Builder cross-assist: implemented .state-loading/.state-error/.state-empty/.state-conn-lost in ui/app.css (all tokens, 0 hex) + documented in components.md §7 (Designer goal #8)
- designer-goal2-fleet-states-2026-11-18.md — 2026-11-18 Builder cross-assist: loading/error/empty states + responsive SVG added to ui/fleet_topology.js (sha12=294aaca2ec20) + CSS in app.css (Designer goal #2, partial - screenshots still needed)
- assist-designer-goal1-tokens-2026-11-19.md — 2026-11-19 Builder cross-assist: replaced last 3 hard-coded hex (#3ddc84 x2, #4cd964) with var(--ok); post-fix scan = 0 truly hard-coded hex outside token definitions (Designer goal #1, near-closure; remaining hex only in var() fallbacks)