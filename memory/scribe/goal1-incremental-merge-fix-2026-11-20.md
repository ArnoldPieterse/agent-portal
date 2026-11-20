# Goal 1 - Incremental Merge Fix (2026-11-20)

**Bug:** `extract_decisions.py --since YYYY-MM-DD` opened decisions.jsonl in write mode, clobbering all prior entries with only the new subset.

**Fix:** When `--since` is provided and OUT file exists, load existing entries, dedup on normalized decision text (lowercase + whitespace-collapsed), merge, sort by date+confidence, then write. Full-scan mode (no --since) still overwrites as before (idempotent).

**Verified:**
- Full scan: 11 entries, PASS
- Incremental (--since 2026-11-19): finds 1 new, merges to 11 total, PASS
- No data loss on repeated incremental runs

**Artifact:** memory/scribe/extract_decisions.py (fixed)
