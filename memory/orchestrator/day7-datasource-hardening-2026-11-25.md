# Orchestrator — Day-7 checkpoint: data-source hardening (2026-11-25)

## Action taken
Upgraded `stealth_checkpoint.py` to use Scribe's structured JSONL as primary data source,
with markdown parsing as fallback. This eliminates a class of parse failures that could
produce incorrect revenue numbers on day-7 if the markdown format drifts.

Changes:
1. Added `parse_ledger_jsonl(path)` — reads structured entries from stealth-ledger.jsonl
2. Renamed old parser to `parse_ledger_md(text)` (fallback only)
3. Updated `build_report` to accept parsed dict directly (no re-parsing)
4. Updated `main()` to prefer JSONL, fall back to MD
5. Selftest updated: 2/2 cases use structured dicts

## Verification
- `python memory/orchestrator/stealth_checkpoint.py --selftest` -> SELFTEST PASS
- Live run: reads stealth-ledger.jsonl (1 entry), produces correct day-0 report
  - outreach=3 (matches JSONL), revenue=$0, all HOLD decisions
- Output: memory/orchestrator/stealth-checkpoint-latest.{md,json}

## Status
Goal #8 (Day-7 checkpoint) remains date-gated to 2026-12-02. This pass de-risks the
day-7 run by ensuring the data pipeline is robust. No further action needed until 12-02.
Blocker recorded in memory/ops/blockers.md (date-gate, not a technical blocker).
