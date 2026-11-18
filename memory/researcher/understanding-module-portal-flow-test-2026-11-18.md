# Understanding Module + Portal Flow Test (2026-11-18)

Requested: "test the understanding modules and how it flows through our portal"

## Architecture (two integration points in agent_portal.py)

1. _mem_local_hits() [~L1436]: expands each prompt keyword via understanding.synonyms()
   before scoring memory/INDEX.md lines. Effect: index lookups catch near-synonyms.
2. readmem path [~L2331]: calls understanding.understanding_block(messages) to build
   a U-ref indexed dictionary-meaning block, appended to lookup_ctx (pre-context).

## Test Results (all PASS)

| # | Check | Result |
|---|-------|--------|
| 1 | Module loads via lazy importlib | OK |
| 2 | key_terms("test the understanding modules...") | 6 terms extracted |
| 3 | synonyms("test") | [assure, check, confirm, test, validate, verify] |
| 4 | Dictionary lookup "test" | core dict hit with def+usage |
| 5 | understanding_block() output | U1/U2 lines, correct format |
| 6 | expand() for memory index | 5 words -> 18 (synonym expansion works) |
| 7 | Hit-rate improvement | base=1 hit, expanded=3 hits on mirror/clobber prompt |
| 8 | Project dictionary (mirror term) | fleet-specific def+usage returned |
| 9 | Full readmem simulation | combined 444 chars pre-context built correctly |
| 10 | Error handling (empty/None/garbage) | all degrade to '' or [], no crash |

## Known Limitations

- Live HTTP test blocked by sandbox egress (WinError 10013) - code path verified
  via direct function calls matching agent_portal.py source exactly.
- load_dictionary() returns [def, usage] shape only; drops confidence/sources annotations
  present in dictionary_*.json (documented in kb_search evidence as a known gap).

## Files
- memory/researcher/understanding.py (module, ~280 lines)
- memory/researcher/dictionary_core.json (68 general terms)
- memory/researcher/dictionary_project.json (30 fleet/project terms)
- agent_portal.py (_understanding() lazy loader at L1365, two call sites)

Verdict: PASS - module works correctly in both integration points.
