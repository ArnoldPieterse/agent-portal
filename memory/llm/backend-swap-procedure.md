Last updated: 2026-11-14 ~00:0x (Orchestrator goal 4 - procedure written + drill scheduled)

# Backend-swap procedure (unload idle → load required → restore binding)
Purpose: free VRAM for a required model on a host, then restore the original state, with ZERO lost bindings. All endpoints verified against White :8888 on 2026-11-14.

## Endpoints (verified)
- GET /models -> data[]: {id, loaded, quant, context_length...} (loaded flag = resident)
- GET /api/settings/model-aliases -> {aliases:[{name, model(folder PATH)}]} — aliases bind folder paths, not ids
- GET /api/inference/active-generations -> {count, active:[...]}
- POST /api/inference/load body: {model_path (LOCAL FOLDER PATH), gguf_variant, gpu_ids:[n], max_seq_length, cache_type_kv:"q8_0", n_parallel:1, [force_reload, speculative_type:"mtp", spec_draft_n_max:4]}
  - 200 = ASYNC ACK only — poll GET /models until loaded=true (Q8 took ~4 min once)
  - 409 Conflict while a generation is active -> idle-gate first (see below)
- POST /api/inference/unload body: {model_path} (full path; reported id also accepted per 11-14 v2 run)

## Procedure (proven bodies from white_realias_rename.py v2, 2026-11-14 01:26)
1. IDLE GATE: poll /api/inference/active-generations until count==0 (up to ~3 min; abort if never idle - NEVER force-cancel a live generation).
   KNOWN TRAP: an active chat round keeps its generation handle for the WHOLE turn (observed started_at persisting across tool calls) - a drill cannot pass the gate from inside the round it would disturb. Schedule it as a one-shot schtask AFTER the round ends.
2. SNAPSHOT: GET /api/settings/model-aliases + GET /models -> save to result file (restoration proof baseline).
3. LOAD required model alongside (multi-model fit mode; PUT /api/settings/multi-model {"enabled":true,"mode":"fit"} if not set). White proven bodies:
   - Q8_0: {model_path: C:\Users\White\.lmstudio\models\lmstudio-community\Qwen3.8-27B-Q8_0, gguf_variant: "Q8_0", gpu_ids:[1], max_seq_length:32768, cache_type_kv:"q8_0", n_parallel:1}
   - Q4_K_S: {model_path: C:\Users\White\.lmstudio\models\unsloth\Qwen3.8-27B-Q4_K_S, gguf_variant: "UD-Q4_K_S", gpu_ids:[0], max_seq_length:131072, cache_type_kv:"q8_0", n_parallel:1, force_reload:true, speculative_type:"mtp", spec_draft_n_max:4}
4. POLL until resident (loaded=true); on failure UNLOAD whatever was loaded and restore - full rollback.
5. VERIFY bindings mid-swap: GET /api/settings/model-aliases must equal the snapshot (aliases are path-bound; a folder rename breaks them silently - re-point via PUT /api/settings/model-aliases).
6. When done, UNLOAD the temporary model (POST /api/inference/unload {model_path}); poll until loaded=false.
7. FINAL VERIFY: aliases identical to snapshot + original resident model(s) still loaded=true. Log every step with timestamps to a result JSON (pattern: backend_swap_drill_result.json).

## Drill status 2026-11-14
- First in-round attempt: 409 on load POST (own round was the active generation) -> gate added, run aborted cleanly, zero side effects.
- Safe drill (idle Q4_K_S alongside resident Q8_0; aliases before/mid/after; unload; Q8 untouched) SCHEDULED as one-shot task SwapDrill1114 @ 15/11/2026 00:05 (runs after the Orchestrator round ends). Verdict file: backend_swap_drill_result.json; log: backend_swap_drill_scheduled.log. PASS criterion: verdict = PASS_zero_binding_loss.
