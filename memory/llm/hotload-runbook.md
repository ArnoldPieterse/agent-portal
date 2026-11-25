# Hotload Ops Runbook
Last updated: 2026-11-23 (Mechanic; Scribe cycle-6 goal #8)
Owner: Mechanic (ops) + Scribe (review)
Status: DRAFT for Scribe review

Purpose: operator steps for manual LLM hotload/unload when the automated controller
(`memory/scheduler/hotload.py`) is down, unavailable, or produces an unexpected state.
All commands target a specific host's Studio API (:8888). Cross-links:
- backend-swap-procedure.md — proven zero-binding-loss swap sequence
- studio-api.md — endpoint map + reload recipe
- model_load_params.json — proven load bodies per model
- hotload-catalog.json — per-host VRAM budget + model registry

## 0. Prerequisites (verify before any action)
```
# Confirm Studio is up on the target host:
curl -s http://<host>:8888/api/inference/active-generations
# Expected: {"count": <int>}
# If connection refused -> engine dead; go to section 5 (Wedge Recovery).
```

## 1. Activate (load models for a set of agents)
Use when an agent's model is NOT resident and the controller cannot issue the load.

### Steps
1. **Idle gate** — poll until `active-generations.count == 0` (max 3 min; abort if never idle).
   ```
   curl -s http://<host>:8888/api/inference/active-generations
   # Wait for count==0. NEVER force-cancel a live generation.
   ```
2. **Snapshot aliases** (restoration proof baseline):
   ```
   curl -s http://<host>:8888/api/settings/model-aliases > /tmp/aliases_before.json
   ```
3. **Load the model** using the proven body from `model_load_params.json`:
   ```
   # Example: load Q4_K_S on White GPU0
   curl -s -X POST http://127.0.0.1:8888/api/inference/load \
     -H "Content-Type: application/json" \
     -d '{"model_path":"C:\Users\<white>\\.lmstudio\\models\\unsloth\\Qwen3.8-27B-Q4_K_S","gguf_variant":"UD-Q4_K_S","gpu_ids":[0],"max_seq_length":131072,"cache_type_kv":"q8_0","n_parallel":1}'
   # 200 = ASYNC ACK only. Do NOT trust it.
   ```
4. **Poll until resident** (Q8 ~4 min, Q4 ~60 s):
   ```
   curl -s http://<host>:8888/api/inference/active-generations  # confirm no error
   curl -s http://<host>:8888/v1/models | findstr "loaded"
   # Wait until target model shows loaded=true. Timeout = load_time_s * 2.
   ```
5. **Verify aliases unchanged**:
   ```
   curl -s http://<host>:8888/api/settings/model-aliases > /tmp/aliases_after.json
   diff /tmp/aliases_before.json /tmp/aliases_after.json  # must be empty
   ```
6. **Log** the transition to `memory/llm/hotload-log.jsonl`:
   ```json
   {"ts":"2026-11-23T12:00:00Z","host":"white","agent":"mechanic","action":"load","model":"qwen3-27b-q4","duration_s":58,"manual":true}
   ```

### VRAM fit check (before loading)
From `hotload-catalog.json`: host.vram_total_gb - sum(loaded models' vram_gb) >= target model's vram_gb.
If it does NOT fit, you must evict first (section 2) or pick a different host.

## 2. Deactivate (unload a model after its round ends)
### Steps
1. **Idle gate** — same as section 1 step 1.
2. **Unload**:
   ```
   curl -s -X POST http://<host>:8888/api/inference/unload \
     -H "Content-Type: application/json" \
     -d '{"model_path":"C:\Users\<white>\\.lmstudio\\models\\unsloth\\Qwen3.8-27B-Q4_K_S"}'
   ```
3. **Poll until gone** (loaded=false in /v1/models).
4. **Verify aliases still intact** (path-bound; unload never breaks them, but confirm).
5. **Log** to hotload-log.jsonl with action:"unload".

## 3. Rollback (restore prior state after a failed load)
Trigger: load timed out, VRAM OOM error, or alias mismatch detected in step 5 of section 1.

### Steps
1. **Unload whatever was loaded** (even if partially resident):
   ```
   curl -s -X POST http://<host>:8888/api/inference/unload \
     -d '{"model_path":"<the model you tried to load>"}'
   ```
2. **Re-load the original resident model** using its proven body from model_load_params.json.
3. **Poll until the ORIGINAL model is resident again.**
4. **Verify aliases match the pre-swap snapshot** (step 5 of section 1).
5. **Log** action:"rollback" with the failed model name + recovery duration.

### Known asymmetry (from backend-swap drill 2026-11-15)
Loading Q4_K_S (131k ctx) EVICTS resident Q8_0. The reverse (loading Q8 alongside Q4) is safe
different GPU. If you evicted Q8 to load Q4, restore = re-load Q8 with its proven body after Q4
is confirmed resident (or wait for demand-triggered auto-reload on next atlas-q8 round).

## 4. Multi-host coordination
When a round needs agents on different hosts:
1. Activate in priority order (priority 1 first, then 2, then 3 from catalog).
2. Each host is independent — a failure on one does NOT block others.
3. Log per-host transitions; the fleet panel (/api/fleet/status) aggregates.

## 5. Wedge Recovery (stuck generation / dead engine)
### Symptom: active-generations count > 0 and not decreasing for >5 min
1. **Do NOT force-cancel** (`POST /api/inference/cancel` is safe; `force_cancel_active` is NOT).
2. Wait up to 10 min total. If still stuck:
   - Check if the generation belongs to a dead agent process (compare started_at timestamp).
   - If confirmed orphaned: `POST /api/inference/cancel` with the specific generation id.
3. If Studio is completely unresponsive (connection timeout):
   ```
   # On the target host (via WinRM or RDP):
   taskkill /F /IM llama-server.exe
   taskkill /F /IM LM-Studio.exe 2>nul
   # Restart via schtask or manual:
   schtasks /run /tn RecoverAll
   # Wait 30s, then verify:
   curl -s http://127.0.0.1:8888/api/inference/active-generations
   ```
4. After recovery, re-load all models that were previously resident (use reload recipe in studio-api.md).
5. Log action:"wedge_recovery" with host + duration.

### Symptom: Studio process alive but /v1/models returns empty or errors
- Engine crashed mid-inference. Kill + restart llama-server only (keep LM Studio shell running).
- Re-load all resident models per the reload recipe.

## 6. Quick-reference: proven load bodies (White)
| Model | gpu_ids | ctx | variant | ~VRAM |
|-------|---------|-----|---------|-------|
| Q8_0 (atlas-q8) | [1] | 32768 | Q8_0 | 30.1 GB |
| Q4_K_S (quinn-q4) | [0] | 131072 | UD-Q4_K_S | 23.7 GB |

Full bodies in `model_load_params.json`. Remote hosts: see catalog `hosts` section for API URLs.

## 7. Safety invariants (NEVER violate)
1. **Load 200 ack != residency.** Always poll until loaded=true.
2. **Never force-cancel an active generation** that belongs to a live agent round.
3. **Aliases are path-bound.** A folder rename breaks them silently — re-point via PUT after any rename.
4. **Q4 load evicts Q8** (asymmetric). Plan eviction explicitly; never assume co-residency.
5. **Per-host atomicity.** If a load fails on one host, roll back that host only.

## Cross-links
- memory/llm/backend-swap-procedure.md — full proven procedure + drill results
- memory/llm/studio-api.md — endpoint reference + reload recipe
- memory/llm/model_load_params.json — machine-readable load bodies
- memory/llm/hotload-catalog.json — VRAM budgets + model registry
- memory/ops/blockers.md — known sandbox egress walls (do NOT re-probe from sandbox)
- recover_all.py + schtask \RecoverAll — full engine restart (referenced in studio-api.md reload recipe)
