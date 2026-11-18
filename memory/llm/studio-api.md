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

## Folder rename 2026-11-14 (fleet-convention ids) — DONE 01:45
White's local model folders were quant-less, so /v1/models deduped both resident variants under one bare id and the
fleet panel showed no quant tags. Renamed (white_realias_rename.py v2, verdict file white_realias_result.json):
  lmstudio-community\Qwen3.8-27B-Q8_0   (holds Qwen3.8-27B-Q8_0.gguf)
  unsloth\Qwen3.8-27B-Q4_K_S            (holds Qwen3.8-27B-UD-Q4_K_S.gguf + .part downloads for BF16/UD-Q8_K_XL)
Aliases bind folder PATHS (GET/PUT /api/settings/model-aliases), re-pointed in the same run:
atlas-q8 -> ...\Qwen3.8-27B-Q8_0, quinn-q4 -> ...\Qwen3.8-27B-Q4_K_S.
Contexts preserved: Q4 ctx 131072 GPU0 (~23.7 GB), Q8 ctx 32768 GPU1 (~30.1 GB). Fleet panel verified 01:45:
White row = 'Qwen3.8-27B-Q4_K_S (Q4_K_S), Qwen3.8-27B-Q8_0 (Q8_0)' (+ the same Q4 instance also lists under its
folder id unsloth/Qwen3.8-27B-Q4_K_S - cosmetic Studio dual-listing, same pattern as Red's row).
HISTORY: v1 run (01:13) ABORT_unload — unload body sent {'id':...}, endpoint requires model_path (422).
v2 (01:26) verdict PARTIAL = FALSE ALARM on Q8: POST /api/inference/load returns 200 as an ASYNC ACK before the
engine is resident; v2 probed atlas-q8 ~46 s after the ack -> 404 'downloaded but not loaded'. Q8 actually came up
~4 min after its load request (Q8_0 = 29 GB mmap + engine init). Lesson: after any load, POLL /api/inference/
loaded-models until the id is resident before probing aliases; never trust the 200 ack. Q8 was re-verified resident
+ atlas-q8 probe OK at 01:45 (manual load alongside running Q4 - safe, different GPU).
NOTE: hub repo id `unsloth/Qwen3.8-27B-GGUF` (UD-Q8_K_XL download) is separate from the local folder; if that
download resumes it may recreate a quant-less folder - rename again if so.

## Reload recipe (proven 2026-11-10 via recover_all.py + schtask \RecoverAll; paths updated 11-14)
1. Wait active-generations==0 (this Studio chat rides on Q4 - wait for its turn to end first).
2. POST /api/inference/load, Q8 FIRST (alongside; does not touch Q4):
   model_path ...\lmstudio-community\Qwen3.8-27B-Q8_0, gguf_variant Q8_0, gpu_ids [1], ctx 32768, kv q8_0, n_parallel 1.
3. Then Q4 force_reload: ...\unsloth\Qwen3.8-27B-Q4_K_S, UD-Q4_K_S, gpu_ids [0], ctx 131072 (was 65536; resident value preserved 11-14),
   kv q8_0, n_parallel 1, spec mtp n_max 4, llama_extra_args ["--split-mode","layer"]. Fresh engine clears any stuck queue.
4. Verify: nvidia-smi per-GPU (GPU0>18 GB, GPU1>25 GB) + llama-server cmdlines + /v1/models, then functional probes
   through quinn-q4/atlas-q8 -> recover_result.json verdict ALL_UP.
- dual_load.py + \DualLoadOnce are already migrated to :8888 and remain a valid alternative (Q4-first order, 409 retry).
- STALE (do not run): dual_load_once.py - targets dead :3008 API; orphaned (no bat/task references it); banner added.

