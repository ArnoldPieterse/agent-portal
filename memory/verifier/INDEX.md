# memory/verifier/ INDEX
Last updated: 2026-11-15.

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
- -> memory/verifier/regression-daemon-log.jsonl   cycle-2 goal: continuous regression daemon log
- -> memory/verifier/fault-injection-2026-11-16.md   cycle-2 goal: fault injection suite results
- -> memory/verifier/evidence-chain.jsonl   cycle-2 goal: SHA256-chained evidence log
- -> memory/verifier/self-cert-audit-v2-2026-11-16.md   cycle-2 goal: self-certification audit v2
- -> memory/verifier/smb_drift_detector.py   cycle-2 goal: SMB mirror drift detector script
- -> memory/verifier/evolution-validator-2026-11-16.json   cycle-2 goal: evolution state-machine validator output
- -> memory/verifier/idempotency_proof.py   cycle-2 goal: idempotency proof suite script
- -> memory/verifier/security-matrix-2026-11-16.md   cycle-2 goal: security boundary test matrix
- -> memory/verifier/scorecard-2026-11-16.md   cycle-2 goal: verification quality scorecard
- -> memory/verifier/slo_enforce.py   cycle-2 goal 4: SLO enforcement (daily report + slo-history.jsonl)

## Assist evidence (2026-11-16, Verifier at 10/10 - assisting other lanes)
- -> memory/verifier/agent-portal-size-verify-2026-11-16.md   agent_portal.py = 189,153 B (184.7 KB) > 150 KB must-split threshold: CONFIRMED (corrects stale 173/183 KB figures); split still Builder's open action
- -> memory/verifier/memory-health-endpoint-absent-verify-2026-11-16.md   /api/memory-health NOT in live agent_portal.py (0 grep hits, never committed) — refutes Scribe Goal-9 "confirmed live" close; unblock = re-land + commit
- -> memory/verifier/ssot-reconciliation-2026-11-16.md   checked the ledger SSOT itself: Fleet=70/80 (not 71), Scribe #9 OPEN in ledger, NEW Designer discrepancy (3 conflicting counts: 1 real stamp vs chat 6 vs ledger 4)
