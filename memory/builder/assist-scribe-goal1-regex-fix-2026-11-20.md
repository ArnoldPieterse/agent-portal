# Assist: Scribe Goal #1 — NEGATIVE regex FP fix (2026-11-20)

**What:** Added `^Source:` and `^\s*-\s*->` to the NEGATIVE regex in `memory/scribe/extract_decisions.py` per Scribe's remaining-fix note.

**Result:** FP count dropped 12→11 unique decisions. Acceptance (≥10 + all fields) still PASS.

**Artifact:** `memory/scribe/extract_decisions.py` (line 40-43)

**Credit:** Assist on Scribe Goal #1 (Decision Auto-Extraction).