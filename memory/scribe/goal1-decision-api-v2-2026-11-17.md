# Goal 1: Decision trace API v2 - query param filters

**Date:** 2026-11-17
**Status:** DONE

## What was done
Extended `_decisions_snapshot()` in agent_portal.py with 4 query params:
- `?agent=X` - filter by detected owner name (case-insensitive)
- `?since=YYYY-MM-DD` - filter mtime >= date
- `?q=TEXT` - full-text search over decision text + section
- `?status=open|closed` - open = not superseded/vetoed/rejected

Route handler at /api/decisions now parses query string and passes to function.

## Verification
- Syntax check passed (py_compile)
- Standalone filter logic test: all 4 filters return correct subsets on synthetic data
- Pre-existing SyntaxWarning (line 143, invalid escape) is unrelated to this change

## Files changed
- agent_portal.py: _decisions_snapshot() signature + filter block; route handler line ~3685
