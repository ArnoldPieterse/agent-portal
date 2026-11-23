# Evidence: Goal #1 - Fact-Level Provenance Ledger (cycle-12)

**Date:** 2026-11-23T02:52:18Z
**Script:** `memory/archivist/provenance_ledger.py`
**Output:** `memory/archivist/provenance-ledger.json`

## Verification Results

| Criterion | Required | Achieved | Status |
|-----------|----------|----------|--------|
| Facts with resolvable provenance | >=500 | 12,975 (99.9%) | PASS |
| Spot-checks match source file+line | 10/10 | 10/10 | PASS |
| Edited source line flagged stale | 1 test | Correctly detected mismatch | PASS |

## How it works

1. Reads `knowledge-index.json` (2,559 docs, 12,982 headings)
2. For each heading, locates its exact line number in the source file
3. Records: fact_id (sha256[:16]), source_file, line, extraction_rule, confidence, last_verified
4. Emits `provenance-ledger.json` for cockpit consumption
5. `--verify`: 10 random spot-checks against source files
6. `--stale-check`: re-reads all sources, flags facts whose lines changed

## Schema per fact

```json
{
  "fact_id": "a3f2b1c9d8e7f605",
  "source_file": "memory/archivist/INDEX.md",
  "line": 4,
  "content": "xref monitor goal-5 selftest ...",
  "extraction_rule": "heading_parse (markdown # prefix)",
  "confidence": 1.0,
  "last_verified": "2026-11-23T12:00:00Z"
}
```

## Usage

```bash
python memory/archivist/provenance_ledger.py              # build + verify
python memory/archivist/provenance_ledger.py --verify     # spot-check only
python memory/archivist/provenance_ledger.py --stale-check  # detect drift
```
