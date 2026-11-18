# Understanding Module → Portal Flow Test (2026-11-18, Researcher)

## Scope
Tested `memory/researcher/understanding.py` and its two integration points in
`agent_portal.py`: synonym expansion in `_mem_local_hits` (L1436) and
dictionary block injection via `understanding_block()` (L2327-2335).

## Pipeline (verified end-to-end)
1. Human message arrives → `key_terms()` extracts meaningful words (stopwords removed)
2. `_mem_local_hits`: each key term expanded via `synonyms()` before scoring memory index lines
   - Effect: "server is slow, model crashes" → base 5x max score, expanded 12x max score (+5 new top-6 hits)
3. `understanding_block()`: dictionary lookup on key terms → U-referenced definitions + usage
4. Both blocks folded into `lookup_ctx` → appended to system prompt via `build_system_prompt(L1626)`

## Test Results: 23/23 PASS
- Module loads (lazy import via `_understanding()`)
- key_terms / synonyms / lookup / understanding_block all functional
- Graceful degradation on empty/None input (returns '' or [])
- Synonym expansion measurably improves recall (tested with generic prompt)
- Full pipeline simulation: final system prompt contains both UNDERSTANDING + MEMORY INDEX HITS sections

## Dictionary Coverage
- dictionary_core.json: 69 entries (general terms: memory, context, prompt, model, test, module...)
- dictionary_project.json: 31 entries (project-specific: agent portal, pre-context, readmem, mirror, pin...)
- Total: 98 terms. Compound terms like "agent portal" exist but `key_terms()` extracts single words only.

## Gaps / Observations
1. **No UI/API visibility**: the understanding block is backend-only (injected into LLM prompt).
   Users can't see what was injected without reading activity logs. `/api/memory/file` can serve
   the dictionary JSONs but there's no dedicated endpoint for "what understanding context did this
   message get?"
2. **Compound term mismatch**: `key_terms()` extracts single words (regex `[a-z0-9_]{3,}`).
   Dictionary entry "agent portal" won't match because key_terms returns ["agent", "portal"] separately.
   The `lookup()` function does try stems and synonyms but not n-gram matching.
3. **Two __pycache__ versions** (cpython-313 + cpython-315): if portal runs on 3.15 but the
   .pyc was compiled by 3.13, it will recompile (harmless). Not a bug, just noting.
4. **No live API verification**: couldn't hit localhost:8099 from sandbox to confirm the module
   loads in the actual running portal process (import path resolution via `_understanding()` at L1365).

## Confidence
- Module correctness: HIGH (all unit tests pass, graceful degradation verified)
- Portal integration wiring: MEDIUM-HIGH (code path traced, but not tested against live server)
- Real-world effectiveness: MEDIUM (synonym expansion clearly helps recall; dictionary coverage
  is small at 98 terms - most prompts will get 0-3 U-refs at best)

## Files
- memory/researcher/understanding.py (module)
- memory/researcher/dictionary_core.json (69 entries)
- memory/researcher/dictionary_project.json (31 entries)
- agent_portal.py L1364-1378 (_understanding loader), L1436-1444 (synonym expansion), L2327-2335 (block injection), L1626-1627 (system prompt append)
