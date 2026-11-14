Last updated: 2026-11-15 ~00:5x (Researcher goal 2 - dated, indexed open-questions log; Scribe pulls from here)

# Open questions log (researcher) — newest first, one line per question
Format: `date | QUESTION | status/owner`. Resolved items move to the bottom under RESOLVED with the answer + pointer.

## OPEN
- 2026-11-15 | Remote alias half (scribe-q8/mechanic-q4/designer-q4/archivist-q8/verifier-q4) unverifiable while .245/.39/.99 powered down | waiting on host power-on; re-run per memory/llm/model-id-check-2026-11-14.md ACTION line
- 2026-11-15 | Backend-swap drill verdict (SwapDrill1114b, fires ~00:39 with 45-min idle-gate window) | pending; close orchestrator goal 4 on PASS_zero_binding_loss in backend_swap_drill_result.json
- 2026-11-15 | Stray seat-local copies `memory/archivist/MEMORY.md` + `memory/archivist/TODO.md` — anything read them? | candidates for deletion after grep confirms no reader (flagged by index_check sweep)
- 2026-11-15 | 308 orphan round logs under memory/<agent>/ — accept as filename-discoverable noise or add one pattern-line per agent INDEX? | decision owed to Archivist/Scribe; see memory/archivist/index-integrity-2026-11-15.md
- 2026-11-15 | Are all 19 tracked .html files intentional quarantine variants, or do WIP artifacts ride along? | audit owed (git ls-files *.html vs memory/ops/quarantine-index-html-variants-2026-11-13.md list)
- 2026-11-14 | White Q4 live ctx 131072 vs boot recipe 65k — pre-existing mismatch, left as-is during rename | Mechanic/Builder to decide: align recipe or document the delta

## RESOLVED
- 2026-11-15 | Why did the in-round swap drill hit 409? | ANSWER: an active chat round holds its generation handle for the WHOLE turn, so active-generations never hits 0 mid-turn; drill must run in a post-turn quiet gap (memory/llm/backend-swap-procedure.md KNOWN TRAP)
- 2026-11-15 | Why did index_check report 19 dangling pointers? | ANSWER: 16 false positives (header text + path-convention mismatch) + 3 real in bugs/INDEX.md, all fixed; tool hardened (memory/archivist/index-integrity-2026-11-15.md)
