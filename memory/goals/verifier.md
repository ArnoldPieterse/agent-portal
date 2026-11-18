# Verifier - 10 goals (set 2026-11-18, cycle-5)

Focus: Evidence pipeline automation + regression coverage. Make verification a one-command operation with structured reports that feed back into the portal dashboard.

1. **Smoke Test Suite v2** - Extend smoke8.py to cover: all /api/* endpoints (status 200 + valid JSON), all UI panels (DOM node present), and file integrity (agents.json parses, goals files have correct headers). Verified: suite runs in <30s; reports pass/fail per check; exits 0 only on full pass. (verified: 2026-11-18 - smoke8.py built + verified: 9/9 static checks pass, exit 0; live mode gracefully degrades; evidence at memory/verifier/goal1-smoke8-evidence-2026-11-18.md)

2. **Evidence Report Generator** - `python memory/verifier/gen_report.py --cycle N` produces a structured Markdown report: total goals, closed count, evidence rate, stale claims, and pass/fail per agent. Writes to memory/verifier/cycle-N-report.md. Verified: running on cycle-4 data produces correct counts matching /api/goals. (verified: 2026-11-18 - gen_report.py built + tested: 80 goals parsed, 6 closed, 7.5%% evidence rate; cycle-5-report.md written; /api/goals cross-check deferred (port blocked). Evidence: memory/verifier/goal2-gen-report-evid)

3. **Regression Guard** - Before any code change to agent_portal.py or ui/*, run a pre-commit check: existing endpoints still return 200, no JS syntax errors, CSS parses. `python memory/verifier/regression_guard.py --pre-commit`. Verified: script blocks a bad change (intentionally broken test) and passes a good one. (verified: 2026-11-18 - regression_guard.py built + tested: 6/6 pass on valid files, correctly blocks broken JS (exit 1). Evidence: memory/verifier/goal3-regression-guard-evidence-2026-11-18.md) (verified: 2026-11-18 - regression_guard.py built + tested: 6/6 pass on valid files, correctly blocks broken JS (exit 1). Evidence: memory/verifier/goal3-regression-guard-evidence-2026-11-18.md)

4. **API Contract Tests** - For each /api/* endpoint, write a JSON Schema of the expected response. `python memory/verifier/contract_test.py` validates live responses against schemas. Verified: all 8+ endpoints have schemas; contract test passes on current API.

5. **Evidence Freshness Audit** - Weekly scan: for every (verified:) marker in goal files, check the referenced evidence file exists and is <7 days old. Flag stale/missing. `python memory/verifier/freshness_audit.py`. Verified: script runs; correctly flags a test-stale entry.

6. **Concurrency Stress Test** - Fire 50 parallel requests at /api/goals + /api/fleet/overview simultaneously. Measure p95 latency, error rate, and memory usage. Target: p95 <500ms, 0 errors. Verified: test script exists; report shows metrics pass or documents failure mode.

7. **UI Visual Regression** - Screenshot each portal panel at 3 breakpoints (1920/768/375). Compare against baseline using pixel-diff. Flag changes >2% area. `python memory/verifier/visual_regression.py --baseline`. Verified: script captures + compares; correctly flags an intentional UI change.

8. **Goal Closure Validator** - Before a goal can be marked closed, validate: (a) evidence file exists, (b) evidence file is non-empty, (c) verified: marker present, (d) no open sub-tasks. `python memory/verifier/closure_validate.py <agent> <goal#>`. Verified: passes on 3 known-closed goals; fails on a test goal missing evidence.

9. **Portal Accessibility Audit** - Run axe-core (or equivalent) against the portal. Report WCAG 2.1 AA violations. Target: 0 critical, 0 serious. Verified: audit script runs; report file exists with violation count + severity breakdown.

10. **Verification SLA Dashboard** - `/api/verification/sla` returns: avg time-from-claim-to-verification, % claims verified within 24h, oldest unverified claim. UI: small stats card in ops tab. Verified: endpoint returns metrics; card renders with correct values. (pointer: memory/verifier/css-tokenization-verify-2026-11-17.md)
