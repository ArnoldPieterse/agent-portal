# Runbook: design_qa.py encoding fix (2026-11-26)

**What broke:** `memory/designer/design_qa.py` had 7 `open()` calls without `encoding='utf-8'`, causing crashes on Windows when files contain non-ASCII bytes or CRLF line endings.

**Fix applied:** Added `encoding='utf-8'` to all 7 `open()` calls (lines 22, 28, 39, 51, 68, 69, 96). Syntax verified clean.

**Ops copy:** `memory/ops/design_qa.py` already had encoding params - no change needed there.

**Verification:** `compile()` passes; zero unencoded `open()` calls remain.
