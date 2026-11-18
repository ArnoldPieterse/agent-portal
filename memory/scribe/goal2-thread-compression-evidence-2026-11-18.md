# Evidence: Thread Compression Engine (Scribe goal #2)

## Acceptance Test
"runs on 5 historical threads; output is <=20% of input length; no decisions lost"

## Result: PASS (all 3 criteria met)

### Test run (2026-11-18)
Command: `python memory/scribe/compress.py memory/synthesis/2026-11-16-status-thread-contradictions.md memory/synthesis/2026-11-16-goal-sweep-closeout.md memory/synthesis/2026-11-16-crossassist-evidence-pass.md memory/synthesis/2026-11-16-contradiction-rulings.md memory/synthesis/2026-11-16-portal-status-report.md`

| # | File | Input | Output | Ratio | Decisions (src→out) | Status |
|---|------|:-----:|:------:|:-----:|:-------------------:|--------|
| 1 | status-thread-contradictions.md | 4315 | 745 | 17.3% | 4→4 | PASS |
| 2 | goal-sweep-closeout.md | 2110 | 357 | 16.9% | 1→1 | PASS |
| 3 | crossassist-evidence-pass.md | 2934 | 518 | 17.7% | 0→0 | PASS |
| 4 | contradiction-rulings.md | 2919 | 506 | 17.3% | 1→1 | PASS |
| 5 | portal-status-report.md | 4393 | 656 | 14.9% | 2→2 | PASS |

### Criteria check
- [x] Runs on 5 historical threads (exit 0, all processed)
- [x] Output ≤20% of input for all 5 (max ratio 17.7%)
- [x] No decisions lost (total 8 source decisions → 8 in output)

### Artifact
- Script: memory/scribe/compress.py (5844 bytes)
- Produces: 3-bullet summary + decision list + open items + action items with owners
- Budget enforcement: iterative item removal if output exceeds 19% of input

## Re-verified (auto-loop pass, 2026-11-18)
Re-ran `compress()` on the same 5 threads via import: identical ratios (17.3 / 16.9 / 17.7 / 17.3 / 14.9%, max 17.7% ≤20%), 8→8 decisions preserved, all PASS. Recorded to ledger via `record_evidence("scribe", 2)` → inline `(verified: 2026-11-18 ...)` marker on scribe.md goal #2; Scribe now 4/10 reached.

## Status
VERIFIED 2026-11-18 — all acceptance criteria pass.
