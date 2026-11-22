# Fleet Model Residency Study v2 — 2026-11-17

Source: agents.json (on-disk) cross-referenced with memory/llm/hosts.md (dual-resident layout, last confirmed 11-14) + MEMORY.md hot note (White models unloaded 11-16). Live probe BLOCKED by sandbox network restriction (WinError 10013 on all outbound sockets); matrix built from documented state only.

## Matrix: 8 agents × expected × actual

| Agent | agents.json model_id | Routed to (per config) | Intended host | Alias registered on host | Loaded? | Match |
|-------|---------------------|----------------------|---------------|--------------------------|---------|-------|
| orchestrator | atlas-q8 | White (local) | White | atlas-q8 (Q8_0 GPU1) | NO (unloaded 11-16) | OK (binding correct, model idle) |
| researcher | quinn-q4 | White (local) | White | quinn-q4 (Q4_K_S GPU0) | NO (unloaded 11-16) | OK (binding correct, model idle) |
| builder | Qwen3.8-27B-Q8_0 | White (local) ← WRONG | Black .99 | builder-q8 (Q8_0 GPU1) | YES | **MISMATCH** |
| verifier | Qwen3.8-27B-Q8_0 | White (local) ← WRONG | Black .99 | verifier-q4 (Q4_K_S GPU0) | YES | **MISMATCH** |
| designer | designer-q4 | Pale | Pale .39 | designer-q4 (Q4_K_S GPU0) | YES | OK |
| archivist | archivist-q8 | Pale | Pale .39 | archivist-q8 (Q8_0 GPU1) | YES | OK |
| scribe | scribe-q8 | Red | Red .245 | scribe-q8 (Q8_0 GPU1) | YES | OK |
| mechanic | mechanic-q4 | Red | Red .245 | mechanic-q4 (UD-Q4_K_XL GPU0) | YES | OK |

## Match rate: 6/8 = 75% (below 90% threshold)

## Mismatch detail

### Builder (CRITICAL — wrong host + wrong alias)
- agents.json: `model_id: "Qwen3.8-27B-Q8_0"`, no `studio` field → portal routes to LOCAL White :8888
- Intended: Black .99, alias `builder-q8` (Q8_0 on GPU1, ctx 32768)
- Impact: Builder requests hit White's Q8_0 (currently unloaded) instead of Black's instance. If both Orchestrator and Builder resolve to White's Q8_0, they'd queue against the same model.
- Fix: add `"studio": "http://Black:8888"` + `"api_key": "<BLACK_KEY>"` + change `model_id` to `"builder-q8"`

### Verifier (CRITICAL — wrong host + wrong alias + wrong quantization)
- agents.json: `model_id: "Qwen3.8-27B-Q8_0"`, no `studio` field → portal routes to LOCAL White :8888
- Intended: Black .99, alias `verifier-q4` (Q4_K_S on GPU0, ctx 65536)
- Impact: same wrong-host problem as Builder. Additionally, the benchmark (model-benchmark-2026-11-16.md) recommends Q4_K_S for Verifier (latency-bound, short-output role) — agents.json has Q8_0 which is ~55% slower.
- Fix: add `"studio": "http://Black:8888"` + `"api_key": "<BLACK_KEY>"` + change `model_id` to `"verifier-q4"`

## Recommendations (for Orchestrator / agents.json edit)

1. **Builder binding**: set `model_id: "builder-q8"`, `studio: "http://Black:8888"`, `api_key: <from host_api.py load_key('BLACK')>`
2. **Verifier binding**: set `model_id: "verifier-q4"`, `studio: "http://Black:8888"`, `api_key: <from host_api.py load_key('BLACK')>`
3. After fix, re-run this probe with live network access to confirm 8/8 match.
4. White's two models (atlas-q8 + quinn-q4) are unloaded per user directive 11-16 — binding is correct but they cannot serve until reloaded (Orchestrator model-load governance goal covers this).

## Confidence & limitations
- HIGH confidence in the mismatch identification: agents.json is read directly from disk; hosts.md layout was verified live on 11-14 (model-id-check-2026-11-14.md PASS 6/6 for remotes). Both sources agree.
- MEDIUM confidence that Black's instances are still loaded NOW (11-17): last confirmed 11-14; overnight-unload risk exists (memory/llm/overnight-unload.md). Live probe needed to confirm.
- Sandbox blocked all outbound network (WinError 10013) — cannot run live /v1/models this pass. Mechanic or Orchestrator can re-run model_check_1115.py + remote probes when sandbox allows, or via elev.py if available.

## Sources
- agents.json (on disk, read this pass)
- memory/llm/hosts.md (dual-resident layout table, last updated 11-14)
- memory/llm/model-id-check-2026-11-14.md (remote PASS 6/6 on 11-15)
- memory/researcher/model-benchmark-2026-11-16.md (Q4 vs Q8 speed comparison)
- MEMORY.md hot note: "models unloaded on White" 11-16

## Consumer
Feeds Orchestrator agents.json correction goal + Mechanic load-probe verification. Handoff: Orchestrator to apply the two binding fixes; Verifier to smoke-test post-fix.