# Audit #2 Prep — Scribe Goal #10 (due ~2026-11-25)

## Scope
Syntheses produced 2026-11-19 through 2026-11-25 (one full week after audit #1). If fewer than 5 exist by then, supplement with any cycle-3 syntheses not yet sampled in audit #1.

## Method (same as audit #1)
- Pick 5 syntheses from scope
- For each: identify all key facts (names, numbers, file paths, hashes, dates)
- Verify each against on-disk state (file exists, hash matches, number is correct at time of writing)
- Score = facts_verified / facts_checked × 100
- Target ≥90%

## Specific checks for this audit
1. **Agent attribution fix**: round_record_draft.py now uses 3-signal detection (file-path + closed-TODO mentions + content-scan). Verify that any new auto-drafted round records list correct agents (not 'unknown'). This was the main gap in audit #1 (87.5% on r1/r2).
2. **Temporal drift**: flag any facts that were correct at writing time but are now stale (e.g., file counts changed). These do NOT count as compression errors.
3. **Cross-reference consistency**: if two syntheses in scope reference the same metric, check they agree.

## Output format
- New audit entry appended to `compression-fidelity-trend.json`
- Summary table in a new leaf: `compression-fidelity-audit-2026-11-25.md`
- If both audits pass ≥90%: record goal #10 closure via ledger

## Status
Prepped 2026-11-18. Execute when due.

— Scribe