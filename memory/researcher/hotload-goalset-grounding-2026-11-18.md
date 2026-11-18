# Hot-Load Goal Set (cycle-6) - Grounding for Researcher #1
Date: 2026-11-18 | Owner: Researcher | Type: scheduling pass (draft + ground, not yet built)

## What this pass did
User directive: "start scheduling your next set of goals: 1 - hot LLM loading functions expansion and functional from what you worked on before."
- Archived the all-closed cycle-5 set -> memory/goals/archive/researcher-cycle5-2026-11-18.md (src_sha12 f42fc6a5f7fc, 5151 B).
- Drafted the new cycle-6 set (8 goals) into memory/goals/researcher.md; #1 = unified hot-loader expansion.
- Grounded #1 by reading the on-disk scripts + prior research leaves (no live :8888 this pass - sandbox egress WinError 10013).

## Prior work being expanded (on-disk, verified this pass)
| Script | Scope | Resident check | Q4 ctx in body | Notes |
|--------|-------|----------------|----------------|-------|
| recover_all.py | White only | nvidia-smi VRAM | **65536 (STALE)** | idle-wait before reload; wedge investigation; functional probes via aliases |
| fleet_reload.py | all 4 hosts (white/red/black/pale) | /api/inference/loaded-models | not set in white() (Q8-only there) | idempotency guard + _deferred_error + 409 retry; NO post-load chat probe |
| wedge_force_recover.py | White | (probe-based) | n/a | no idle-wait, skips healthy models - proven wedge remedy 11-15 |

## Gaps confirmed this pass (source-level, not keyword-scan)
1. **Q4 ctx regression** — recover_all.py q4_body hardcodes max_seq_length=65536; proven value is 131072 (capability_matrix / white-q4-ctx-alignment-evidence-2026-11-18.md). `'131072' in recover_all.py == False`, `'65536' == True`. Every full reload halves Q4 context.
2. **Idle-wait deadlock** — recover_all.py waits active-generations==0; a Studio chat thread holds a generation active across tool-call gaps (instances.md 11-15 wedge) => deadlock from inside a round. wedge_force_recover.py fixes this but is not integrated as a fallback.
3. **No post-load functional probe / binding verify** — fleet_reload.py only reads loaded-models ids; never chat-probes an alias or checks agents.json model_id->alias->host (model-residency-study-2026-11-17.md found builder+verifier mismatches).
4. **Divergent parallel paths + fragile auth** — two scripts, two poll strategies, ctx scraped/hardcoded; Black creds inline in fleet_reload.py, Pale key scraped from pale_dl.py regex.

## Build spec staged for goal #1 (next pass = pure implementation)
hot_load.py outline:
- HOSTS table: name -> {base, auth_method (none|jwt_login|bearer_file), models:[{path, variant, gpu_ids, ctx, kv, n_parallel, alongside, force_reload}], alias_probe}
  - White: Q8_0 GPU1 ctx32768 + Q4_K_S GPU0 ctx**131072**; probe quinn-q4/atlas-q8
  - Black .99: jwt_login; Q4_K_S GPU0 + Q8_0 GPU1 alongside
  - Pale .39: bearer_file; Q8_0 first then Q4_K_S alongside
  - Red .245: bearer_file; Q8_0 (+XL snapshot fallback) per red() in fleet_reload.py
- plan(host) -> returns exact load bodies (dry-run, no network). Used by --plan for test #1/#2.
- wedge-safe restore(): skip models whose alias probe already answers <timeout; force-reload only wedged ones; NO global idle-wait that deadlocks on a live chat thread.
- resident(host, model_id) -> poll /api/inference/loaded-models (authoritative), never trust 200 ack.
- verify(host): post-load chat_probe per alias + optional --bindings matrix (goal #3).
- emit result JSON per host with time-to-resident + verdict (feeds goal #5 load-baseline.jsonl).

## Verification status this pass
- No goal marked verified (scheduling pass only; nothing built yet).
- Grounding evidence = source reads above + prior leaves. Live :8888 steps are gated on a non-sandbox vantage (Mechanic/Orchestrator console) and are framed as best-available dry-run+fixture per the no-human-gate rule - NOT human-blocked.

## Sources
- memory/goals/researcher.md (new cycle-6 set), memory/goals/archive/researcher-cycle5-2026-11-18.md
- recover_all.py, fleet_reload.py (on-disk, read this pass)
- memory/llm/studio-api.md, memory/llm/backend-swap-procedure.md, memory/llm/instances.md
- memory/researcher/model-residency-study-2026-11-17.md, white-q4-ctx-alignment-evidence-2026-11-18.md, load-probe-current-diskstate-2026-11-17.md
