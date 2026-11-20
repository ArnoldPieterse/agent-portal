# Scribe Goal 9 (Institutional Memory Search) - PARTIAL progress 2026-11-20

Status: **PARTIAL** - backend complete + unit-verified; UI (header search box + results panel) still pending.
Goal line kept OPEN (no false `verified:` marker).

## What was built this pass
- `memory/scribe/memory_search.py` - standalone full-text search over `memory/` + top-level
  `TODO.md`/`MEMORY.md`. Ranking = relevance (per-term frequency + exact-substring bonus)
  + recency (mtime within 30d, exponential decay) + agent-role match (+15 when query names an
  agent and the hit is in that agent's dir / mentions it). Returns top-N `{path, score, snippet, mtime}`.
- `agent_portal.py` - new route `GET /api/memory/search?q=<text>&top=<n>&agent_role=<name>`
  (inserted after `/api/memory/file`). Thin wrapper: parses query, delegates to
  `memory_search.search_memory`, returns `{query, count, results}`. 400 on empty q; top clamped 1..25.

## Verification (ran this pass)
- `python memory/scribe/test_memory_search.py` -> **PASS: all checks green**
  - (A) 12 queries each returned >=1 relevant result (acceptance needs >=10).
  - (B) No false negatives on exact-match terms: for every query, at least one ground-truth file
    containing the exact lowercase term appeared in top-5.
  - Sample top-1s: hotload->cards/hotload.md; anti-stall->TODO.md; cycle_narrative->cycle_narrative.py;
    winrm reboot->mechanic/runbook.md.
- `python -c "import ast; ast.parse(open('agent_portal.py').read())"` -> portal parses OK.
- Import path proven: self-test imports memory_search the same way the endpoint does (sys.path insert).

## Known fix this pass
- Sandbox maps repo to `Z:` while realpath resolves to `C:`; `os.path.relpath` raised
  "path is on mount 'C:', start on mount 'Z:'". Replaced with string-based `_rel_under()` helper.

## Remaining (next step, NOT done)
1. UI: search box in portal header + results panel with clickable links -> belongs in `ui/` modules
   (index.html is markup-only + pinned; do not edit it directly). 
2. Live HTTP end-to-end check of `/api/memory/search` requires a portal reload (running PID 6660 has
   pre-edit code) - hand to Mechanic for the next safe reload, then curl the route.

## Acceptance mapping
- [x] >=10 test queries return relevant results (12 passed)
- [x] ranking puts most-relevant first (top-1 spot-checks correct)
- [x] no false negatives on exact-match terms (self-test check B)
- [ ] UI renders without errors (pending - ui/ module work)
