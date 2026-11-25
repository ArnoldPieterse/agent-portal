# Black idle — root cause + fix (2026-11-25 ~18:10 local)

**Symptom:** Black sat at 0.6% VRAM for hours while White carried all inference.

**Root causes (both fixed):**
1. `C:\Users\<black>\.lmstudio\models` does not exist on Black — the backend's transformers-tier load of Q8_0 was pointed at a non-existent `.lmstudio/models/lmstudio-community/...` path (AutoConfig failures all day, e.g. 03:58/14:05/14:31 local).
2. The Q8 folder held TWO ggufs (main + `mmproj-Qwen3.8-27B-BF16.gguf`). Backend "Detected local GGUF model" only fires for a single-gguf folder, so the Q8 load fell back to the transformers tier and got path-mapped into the missing .lmstudio dir. (Q4_K_S folder had exactly one gguf and loaded fine in ~4s via llama-server.)

**Fix:** moved mmproj to `C:\Users\<black>\models\Qwen3.8-27B-Q8_0-mmproj\`; re-sent both loads as local GGUFs (Q8 gpu1 ctx 32k, Q4 gpu0; multi-model fit mode auto-sized Q4 ctx to 228608). Both resident & stable, chat probes OK: builder-q8 -> 'BUILDER-OK', verifier-q4 -> 'VERIFIER-OK'. Aliases set (revision f9138df288833037). black_dual_load_result.json verdict ALL_UP.

**Watch:** next fleet probe (~18:30 local) should show Black VRAM jump from 0.6%. If Black reboots, models do NOT auto-load — needs a reload hook (fleet_reload.py exists).
