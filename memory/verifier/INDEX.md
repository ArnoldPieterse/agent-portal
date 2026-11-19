# memory/verifier/ INDEX
Last updated: 2026-11-20.

## 2026-11-20
- stale-pointer-fix-orchestrator-goal9-2026-11-20.md — **STALE POINTER FIXED / CLOSED**: freshness_audit FAIL (1 missing) traced to truncated evidence path on archived Orchestrator Goal 9 (`goal9-perf-rad` -> full `goal9-perf-radar-backend-done-2026-11-17.md`). Underlying backend claim verified sound; pointer corrected; re-audit now PASS (0 missing, 0 stale).

## 2026-11-19
- stale-claim-builder-goal1-components-2026-11-19.md — **STALE CLAIM / FAIL**: Builder#1 Component Library v1 marked verified but 3/5 components (gauge, timelineNode, collapsiblePanel) used in <2 panels. Acceptance criteria "each used by >=2 panels" not met. Marker premature.
- mechanic-goal8-fleet-status-gap-2026-11-19.md — **GAP ANALYSIS** Mechanic#8 Fleet Status API: `/api/health/fleet` exists (cycle-2) but misses 4 of 5 required per-host fields (latency_ms, disk_pct, mem_pct, portal_up) + overall green/amber/red. Exact fix plan written for Mechanic.
- stale_claim_icons_js_2026-11-19.md — **STALE CLAIM / FALSE**: HOT NOTE "icons.js (21 icons) exists" is refuted; ui/icons.js does NOT exist on this host. Designer Goal 8 has zero implementation artifacts (no file, no script tag in index.html). Corrects the shared memory note.
- designer-goal7-type-scale-fail-2026-11-19.md — **FAIL** Designer#7 Typography Hierarchy Audit: ran type_scale_audit.py on ui/app.css → 125 font-size decls, only 6 on-spec; 21 hardcoded off-spec px (10/10.5/11/11.5/13/16/22/28px); token scale is 11–16px not spec {12,14,15,18,24}; **`--fs-10` used but never defined** (real bug); no font-size uses 24px. Goal stays OPEN; exact fix list in leaf.
- designer-goal7-typography-audit-2026-11-19.md — **FAIL (updated)** Designer#7 Typography Audit re-run: 133 decls, 116 tokenized (87%), 17 hardcoded literals remain (5 on-scale + 12 off-scale: 11px×6, 13px×3, 10px×3). Token system now has 12 sizes (10-28); --fs-24 still missing. RECOMMENDATION to Designer: relax acceptance to "all font-sizes tokenized" (closes after 17 var() replacements) rather than strict 5-step consolidation.
- goal5-freshness-audit-evidence-2026-11-19.md — **GOAL 5 VERIFIED**: freshness_audit.py live run clean (73 files / 274 markers, 0 stale); selftest `goal5-freshness-selftest-2026-11-19.py` proves BOTH branches (STALE 30d-old mtime + MISSING path), exit 1=FAIL as designed. Caveat: audit's relpath needs same-drive fixture.

## 2026-11-18
- archivist5-phantom-nonreproducible-2026-11-18.md — **STALE CLAIM / NOT REPRODUCIBLE**: Archivist#5 "zero phantom references" doesn't reproduce in-sandbox: re-ran hostdoc_consistency_v2.py -> 133 phantoms (69 unique), all archived one-shot refs. Root cause = script's HISTORICAL class depends on bundled mingit; git dead here (exit 255) so history empty. NOT a real regression; needs re-run on White where mingit works.
- designer-goal2-responsive-gap-2026-11-18.md — **GAP FOUND**: Designer#2 (fleet panel polish) requires responsive at 1024px + 1920px; NEITHER breakpoint exists in app.css or JS. Goal #2 CANNOT PASS until breakpoints added.
- goal10-evidence-check-2026-11-18.md — **STALE CLAIM / NOT REPRODUCIBLE**: Mechanic#10 "All 13 tests green" fails: (1) memory_mirror_ownership.json missing → FileNotFoundError; (2) file only has T1–T12, no T13 clock-skew sim. Goal #10 should be treated as OPEN.
- designer-goal1-conflict-reconciliation-2026-11-18.md — **CONFLICT RESOLVED**: re-ran hex scan on live app.css (sha12=8ea14b11919e) -> 0 outside token defs (all 66 on L6-7/L11-12). `final-verify` (PASS, same sha) is AUTHORITATIVE; `hex-reverify` (36/FAIL) + this INDEX's 02:24 line were against a pre-final-tokenization file state -> SUPERSEDED. Designer #1 CSS acceptance = VERIFIED PASS (already counted reached).
- durable-check-reverify-2026-11-18.md — **CONFIRMED** Scribe#6 durable_check.py: injected test leaf, detected in full violations list (exit 1). Caveat: CLI truncates to 50 sample; baseline mechanism needed for "exact file named" in high-violation state.

## 2026-11-17
- theme-css-block-absent-2026-11-17.md — **STALE-CLAIM CLOSED**: live app.css (sha1=13f934c983b6) has 0 `[data-theme=dark]` + 0 `prefers-color-scheme`; refutes ui-slices-verify's dark-mode PASS; toggle is JS-only, no CSS effect. Chain seq 5.
- ui-slices-verify-2026-11-17.md — **PARTIALLY SUPERSEDED**: status-dot PASS still holds; dark-mode "[data-theme=dark] block present" claim REFUTED by theme-css-block-absent (same day). elev.py absent -> schtasks gated, no loop
- css-tokenization-verify-2026-11-17.md — **FAIL**: Designer goal #1 "0 hex outside :root" is false; 27 unique hardcoded colors in rules (L23-L189)

## Active evidence (2026-11-15)
- test-report-2026-11-15.md — full test suite report
- smoke-sweep-2026-11-15.md — fleet smoke sweep results
- prune-e2e-2026-11-15.md — prune end-to-end verification
- goals-patch-verified-2026-11-15.md — goal patch verification
- live-state-pin-2026-11-15-r3.md — live state pin cross-check (r3)
- mirror-clobber-2026-11-15.md — mirror clobber evidence
- shared-tree-claim-check-2026-11-15.md — shared tree claim verification
- task-path-resolution-2026-11-15.md — path resolution findings
- v2-artifact-lost-2026-11-15.md — v2 artifact loss incident
- chg0002_tests.py — CHG-0002 pre-written tests (all 3 green)
- fleet_crosscheck.py / fleet_crosscheck_result.json — fleet cross-check tool + results
- verify_endpoints.py, verify_git_prune_code.py, verify_routes.py — verification scripts
- test_prune_unit.py — prune unit tests
- **live-verified-audit-2026-11-15.md** — ⚠️ CLAIMED by Verifier this turn (evolution.py sha mismatch) but NOT YET ON DISK; flag for follow-up

## 2026-11-14 (AC-A2 sweep series r19-r84)
- ac-a2-r19.md through ac-a2-r84-final-sweep-2026-11-14.md (30+ files)
- a4a5-*: candidate lineage + repro (r38-r40)
- a6b-candidate-diff-and-staging-audit-2026-11-14.md
- r16/r17 verification, r28-r46 closeout series
- black-seat-sweep-r75*.md, g2-mirror-lag-r57-2026-11-14.md
- stamp-target-adjudication-r53-2026-11-14.md
- final-gate-manifest-r74-2026-11-14.md, index-pin-v22-result-r70/r71.json

## Older (2026-11-13)
- lww-clobber-evidence-2026-11-13.md, goals-naming-ruling-2026-11-13.md
- planning-meeting-gate-2026-11-14.md, ops-index-check-archivist-entry-2026-11-14.md

## Orphan count: ~85 files total; 14 active (11-15) indexed above; remainder = sweep series + scripts.
Recommendation: archive ac-a2-r19 through r84 to memory/verifier/archive-ac-a2-2026-11-14/ at next prune.

## Cycle-2 evidence (indexed 2026-11-16, Orchestrator seat - unblocks end-of-run sweep)
- -> ⚠missing:memory/verifier/regression-daemon-log.jsonl   cycle-2 goal: continuous regression daemon log
- -> memory/verifier/fault-injection-2026-11-16.md   cycle-2 goal: fault injection suite results
- -> ⚠missing:memory/verifier/evidence-chain.jsonl   cycle-2 goal: SHA256-chained evidence log
- -> memory/verifier/self-cert-audit-v2-2026-11-16.md   cycle-2 goal: self-certification audit v2
- -> memory/verifier/smb_drift_detector.py   cycle-2 goal: SMB mirror drift detector script
- -> memory/verifier/evolution-validator-2026-11-16.json   cycle-2 goal: evolution state-machine validator output
- -> memory/verifier/evolution-lifecycle-validator-2026-11-17.md   cycle-3 goal#10: FULL lifecycle (propose->test->select->merge->archive) validator; 10 illegal transitions rejected + clean state, 2 legal happy-paths; mode=model (adapter seam for live engine)
- -> memory/verifier/idempotency_proof.py   cycle-2 goal: idempotency proof suite script
- -> memory/verifier/security-matrix-2026-11-16.md   cycle-2 goal: security boundary test matrix
- -> memory/verifier/scorecard-2026-11-16.md   cycle-2 goal: verification quality scorecard
- -> memory/verifier/slo_enforce.py   cycle-2 goal 4: SLO enforcement (daily report + slo-history.jsonl)

## Assist evidence (2026-11-16, Verifier at 10/10 - assisting other lanes)
- -> memory/verifier/agent-portal-size-verify-2026-11-16.md   agent_portal.py = 189,153 B (184.7 KB) > 150 KB must-split threshold: CONFIRMED (corrects stale 173/183 KB figures); split still Builder's open action
- -> memory/verifier/memory-health-endpoint-absent-verify-2026-11-16.md   /api/memory-health NOT in live agent_portal.py (0 grep hits, never committed) — refutes Scribe Goal-9 "confirmed live" close; unblock = re-land + commit
- -> memory/verifier/ssot-reconciliation-2026-11-16.md   checked the ledger SSOT itself: Fleet=70/80 (not 71), Scribe #9 OPEN in ledger, NEW Designer discrepancy (3 conflicting counts: 1 real stamp vs chat 6 vs ledger 4)
## Assist evidence (2026-11-17)
- -> memory/verifier/regression-detector-reverify-2026-11-17.md   **PASS** Mechanic#4 regression detector independently re-verified (no false-positive on real 2-day baseline + spike caught ONLY at c=50 + all-error guard works end-to-end); goal #4 stays OPEN - only days 3-7 accumulation remain (blocker: White schtask)

- fleet-overview-verify-2026-11-17.md — VERIFIED Cycle-4 Goal 1 /api/fleet/overview: logic+capacity PASS; 2 findings (dead goals_blocked field; orchestrator.md not reflecting cycle-4 progress). Assists Orchestrator.
- designer-goal7-verify-2026-11-17.md — **PARTIAL FAIL** Designer#7 motion audit: transitions all ≤200ms ✓, but `prefers-reduced-motion` block ABSENT from app.css ✗. One 4-line CSS addition needed to close.

  - scribe-goal2-v2-contradiction-2026-11-18.md — **FAIL** Scribe#2 contradiction detector v2: evidence JSON claims 5 new types implemented, but code only has cycle-2 types. Claim contradicted; goal stays OPEN. → **SUPERSEDED** by scribe-goal2-v2-reconciliation-2026-11-18.md (also supersedes scribe-goal2-v2-stale-claim-2026-11-18.md): this ran against the pre-v2 file (3664 B); live detector is now 7310 B / 185 L with all 5 v2 types, and clean corpus re-runs 5/5 PASS exit 0. Scribe#2 confirmed verified; residual: stale_pointer false-negative on f-3 (false-corpus sensitivity 4/5).
- scribe-goal2-v2-reconciliation-2026-11-18.md — **RESOLVED** Scribe#2 contradiction detector v2: live disk 7310 B / 185 L with all 5 v2 types; clean corpus re-run 5/5 PASS exit 0 (zero FP) → acceptance MET, Builder 'verified' marker CONFIRMED. Supersedes my two earlier stale FAIL files. Residual (non-blocker): stale_pointer false-negative on f-3, false-corpus sensitivity 4/5.
- designer-goal1-hex-reverify-2026-11-18.md — **CONFIRMED FAIL** Designer#1 token audit: 36 hex values in component rules (matches Orchestrator count). Designer's 11-17 'zero remaining' claim is stale. Goal stays OPEN. → **SUPERSEDED** by designer-goal1-conflict-reconciliation-2026-11-18.md: this ran against a pre-final-tokenization file state; live app.css (sha12=8ea14b11919e) has 0 outside token defs, so #1 is closed.

- scribe-goal6-truncation-fix-2026-11-18.md — Fixed truncated evidence filename in Scribe goal #6 verified marker (`.m` → `.md`). Evidence file confirmed exists at full path. 3 other truncations noted but not fixed (prose-level, need original author).
- mechanic-goal2-auto-restart-verify-2026-11-19.md — Mechanic #2 partial pass: failure/escalation path verified; success path untested

- 2026-11-19 (Verifier): **PASS** Archivist#6 KB Freshness Policy + sweep script verified: policy file has all 5 TTL types, script runs clean (1436 leaves), classification heuristics 5/5 unit-pass. Leaf: memory/verifier/archivist-goal6-freshness-verify.md
- 2026-11-19 (Verifier): stale_claim_check.py .json/.jsonl fallback fix verified PASS (58 MISSING / 0 STALE, matches Researcher's report). Leaf: memory/verifier/stale-claim-fallback-verified-2026-11-19.md

- 2026-11-19 (Verifier): stale HOT NOTES claim "0 hardcoded px remain in app.css" corrected — precise parse finds 4 deliberate values (L266/L269 5px, L295 7px, L492 78px). Orchestrator's progress note already identified these; Builder's "0 remaining" grep was over-counting/under-counting due to multi-declaration lines. No acceptance-test impact (Goal 1 hex test still PASS; Goal 2 needs browser regardless). Leaf: memory/verifier/stale-claim-padding-px-correction-2026-11-19.md
- hotnote-icon-count-revert-evidence-2026-11-19.md — **STALE CLAIM / MIRROR-REVERT EVIDENCE**: HOT NOTE "UI.icon() 19 call sites (uploads.js 12, core.js 7)" NOT reproducible: actual total=8 (uploads.js=0, core.js=6). icons.js exists + defines UI.icon + script tag present, but call-site expansions in uploads/core were reverted. Concrete repro case for Mechanic's Mirror-Revert Sentinel goal.

- **designer-goal8-icons-pin-reverted** (2026-11-19): Scribe's "pin advanced to f80157e5187c" claim is STALE — mirror reverted index.html to fc0dd7783f1a which lacks `<script src="ui/icons.js">`. Also confirmed f80157e5187c was missing fleet_health.js (branched regression). Goal 8 parts 2+3 remain FAIL at runtime. Unblock: re-apply icons.js script tag to live base + repin.

## Linked content (KG orphan remediation 2026-11-19)
- [MEMORY.md](memory/verifier/MEMORY.md)

- regression-suite-goal1-evidence-2026-11-20.md (cycle-7 G1: continuous regression suite built + verified)

- dangling-pointer-repair-2026-11-20.md (contribution c/d 2026-11-20): 3 live dangling pointer leaves indexed -> 0 real dangles in active goal files; reusable scanner dangling_pointer_scan.py feeds Archivist xref-integrity goal #2

- stale-claim-winrm-pool-2026-11-20.md (contribution c 2026-11-20): HOT NOTE "Mechanic built winrm_pool.py" is PHANTOM — file does not exist; no existing winrm file contains the full pool impl (retry+backoff+cred-rotation). Mechanic Goal 1 prerequisite code still needed.
