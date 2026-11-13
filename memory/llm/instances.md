# LLM instances & routing (dual residency)
Last updated: 2026-11-14 (White-rename convention patch; split from memory/llm-instances.md). Ground truth = nvidia-smi per-GPU VRAM, never /v1/models alone.
STATUS 2026-11-10 18:38 - dual residency RESTORED (recover_all.py, verdict ALL_UP; wedge probe clean). Studio API on :8888 only.
## Current layout
- Q4_K_S on GPU0 (~20.6 GB, ctx 65536 → 131072 since 2026-11-14) — Researcher's (ex-Quinn, renamed 11-12) EXCLUSIVE instance (unsloth path).
- Q8_0 on GPU1 (~30.1 GB, ctx 32768) — Orchestrator (ex-Atlas, renamed 11-12) + the Studio chat thread share it (lmstudio-community path).
- MTP draft model (unsloth/Qwen3.5-4B-MTP-GGUF) currently UNLOADED; spec-decode ~104 tok/s when active.
- Studio /v1/chat/completions SERIALIZES generations globally across models (parallel_slots=1):
  probe_parallel raw concurrent quinn-q4+atlas-q8 never overlapped (-0.12s, 2026-11-10). Parallel
  group processing needs a Studio-side change, not portal/llama.cpp changes.

## Alias table (GET /api/settings/model-aliases on :8888) — how portal names resolve
- atlas-q8 -> C:\Users\White\.lmstudio\models\lmstudio-community\Qwen3.8-27B-Q8_0 (Q8_0, GPU1)
- quinn-q4 -> C:\Users\White\.lmstudio\models\unsloth\Qwen3.8-27B-Q4_K_S (UD-Q4_K_S, GPU0)
- 2026-11-14 convention patch: alias paths above updated to post-rename quant-bearing folders (fleet convention; see hosts.md "White model folders → fleet convention"). Live /v1/models still reports both variants under bare id `Qwen3.8-27B-GGUF` per the artifact note below.
- /v1/models alias artifact: Q8 instance shows loaded=true under bare id `Qwen3.8-27B-GGUF`, full id false. Route by local path + variant.
- /v1/models COUNT is a listing artifact, NOT resident instances: one 27B GGUF appears 3x (bare id,
  community path, unsloth path) plus qwen3-asr-1.7b (unloaded ASR). "4 models" = normal. Resident
  truth = nvidia-smi per-GPU VRAM + llama-server.exe process count (2 expected in dual residency).
  2026-11-10: GPU1 sat at 0 MiB with a single server while API still showed loaded=true -> the Q8
  instance had died; RecoverAll fired to restore.
- ENGINE UPDATE KILLS INSTANCES (2026-11-10): Arnold updated the llama engine -> all running
  llama-server processes die (GPU VRAM drops to 0, API may still show loaded=true). After ANY engine
  update: re-run schtask \RecoverAll. Recovery verified ALL_UP 23:23 with both servers on the new
  binary C:\Users\White\.unsloth\llama.cpp\build\bin\Release\llama-server.exe (Q8 PID 16616 port
  52233 ctx 32768; Q4 PID 24016 port 54521 ctx 65536 MTP n_max 4).

## Wedge incident (2026-11-10)
Client abort mid-stream left one model's request queue stuck (slot idle, requests time out; cancel reported cancelled:0).
Pre-reload probe on 2026-11-10 was CLEAN (quinn-q4 answered in 0.2 s) - not reproduced at probe time; force-reload of the
model's engine remains the proven remedy. If it recurs: run recover_all.py (RecoverAll task).

## Thread rebind (this Studio chat)
- PATCH /api/chat/threads/{id} on :8888 {modelId, modelGgufVariant}, no auth needed locally.
- Currently bound to Q4 (unsloth UD-Q4_K_S) - verified live 2026-11-10 (earlier note said Q8; that was wrong).

## Memory fit & fast-inference notes
- Q4_K_S at full native 256K ctx with q8_0 KV: weights 15.4 + KV 22.9 + projector 1.3 = 30.7 GB -> fits 2x5090 (64 GB). No limit needed.
- Fast-inference flags observed live on llama-server: --spec-type draft-mtp, q8_0 KV, --flash-attn, --jinja, --reasoning on, preserve_thinking, -ngl -1, --kv-unified.

## Core design requirement (Arnold)
Each portal agent = its OWN dedicated LLM instance (separate hosted model + state), not personas on one shared model.

