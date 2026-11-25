# MemFocus - LOD focus cursor over memory recall (2026-11-25)
User ask (Arnold): "our index regex memory and dna recall system can double up as a system focus or cursor with the same effect as Level Of Detail in rendering systems, as we recall new memories we can garbage collect memories that are not required for the moment, using only what the host can provide at the time and not causing overloading situations."

## How it works
- Every recall round (pre-context `_mem_local_hits` + post-prompt `_mem_recall_round`) now computes a FOCUS WINDOW: terms of the latest prompt + topic words of the TODO top section, hashed to an 8-char focus sig.
- Tiers per round, like LOD in rendering:
  - **T2 IN FOCUS** - full line text, only while within the host char budget
  - **T1 POINTER** - file:line + score only; agent fetches with tools if it matters
  - **T0 PARKED** - refs that were in the previous window but fell out of this round's top set are GC'd to `memfocus-parked.jsonl` (audit line: ts, ref, focus sig at eviction). Parking is never deletion - the index regex still finds them when focus returns.
- Host budget (`host_budget_chars`): reads newest `memory/ops/fleet-metrics.jsonl`; base 2400 chars scaled by seat-host vram_pct (1 - 0.6*vram%, floor 0.35), extra x0.7 if cpu>80; clamped [700, 2400]; unknown host -> conservative fleet-max; any failure -> 1500. So a loaded host gets less full-detail recall and more pointers - no overload.

## Files
- `memory/portal/memfocus.py` - pure functions (focus_terms / host_budget_chars / split_tiers / gc_round / park / state io). Importable standalone; never raises.
- `memory/portal/memfocus-state.json` - current window refs, focus sig, parked_total, last_gc_ts, rounds
- `memory/portal/memfocus-parked.jsonl` - GC audit log (append-only)
- Wiring: `_mem_local_hits()` in agent_portal.py (LOD path; degrades to old plain block if module missing); GET /api/memfocus returns state + live budget + last GC line.

## Verify
`python -c "import agent_portal as ap; print(ap._mem_local_hits([{'speaker':'you','content':'level counter goals memory focus'}])[:400])"` then `curl http://127.0.0.1:8099/api/memfocus`.