# Studio API (:8888) & reload recipe
Last updated: 2026-11-11 (split from memory/llm-instances.md). :3008 is GONE - everything on http://127.0.0.1:8888.
## Studio API (MOVED 2026-11-10): :3008 is GONE - everything on http://127.0.0.1:8888
- POST /api/inference/load - body: {model_path (LOCAL PATH, not repo id), gguf_variant, gpu_ids:[n],
  max_seq_length, cache_type_kv:"q8_0", n_parallel:1, speculative_type ("mtp"|"auto"), spec_draft_n_max,
  alongside, force_reload}. gpu_ids WORKS in the load body; the override-store path IGNORES it.
- GET /api/inference/active-generations -> {"count":n}; POST /api/inference/cancel (never force_cancel_active)
- POST /v1/chat/completions with model = portal alias ("quinn-q4"/"atlas-q8"); GET /v1/models
  (alias artifact: Q8 instance shows loaded=true under bare id `Qwen3.8-27B-GGUF`)
- GET /api/settings/model-aliases; first multi-load: PUT /api/settings/multi-model {"enabled":true,"mode":"fit"}

## Reload recipe (proven 2026-11-10 via recover_all.py + schtask \RecoverAll)
1. Wait active-generations==0 (this Studio chat rides on Q4 - wait for its turn to end first).
2. POST /api/inference/load, Q8 FIRST (alongside; does not touch Q4):
   model_path ...\lmstudio-community\Qwen3.8-27B-GGUF, gguf_variant Q8_0, gpu_ids [1], ctx 32768, kv q8_0, n_parallel 1.
3. Then Q4 force_reload: ...\unsloth\Qwen3.8-27B-GGUF, UD-Q4_K_S, gpu_ids [0], ctx 65536 (32768 if GPU0 <22 GB free),
   kv q8_0, n_parallel 1, spec mtp n_max 4, llama_extra_args ["--split-mode","layer"]. Fresh engine clears any stuck queue.
4. Verify: nvidia-smi per-GPU (GPU0>18 GB, GPU1>25 GB) + llama-server cmdlines + /v1/models, then functional probes
   through quinn-q4/atlas-q8 -> recover_result.json verdict ALL_UP.
- dual_load.py + \DualLoadOnce are already migrated to :8888 and remain a valid alternative (Q4-first order, 409 retry).
- STALE (do not run): dual_load_once.py - targets dead :3008 API; orphaned (no bat/task references it); banner added.

