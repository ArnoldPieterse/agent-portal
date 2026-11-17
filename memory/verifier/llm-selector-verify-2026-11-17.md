# VERIFIER — llm_selector.py hotload planner: verification pass (2026-11-17)

Parent: memory/verifier/INDEX.md | Sibling topic: memory/llm/auto-selector-2026-11-17.md
Artifact under test: `llm_selector.py` (Researcher dry-run planner) + `memory/llm/capability_registry.json`

## Verdict: NOT READY for live execution — 5/10 selftest assertions FAIL (exit code correctly = 1)
Repro: `python llm_selector.py selftest` → prints "5 failures", exit 1. (Note: a naive `cmd & echo %ERRORLEVEL%` read shows EXIT=0 because the module's startup warning goes to stderr — measure with subprocess; true code is 1.)

## Defects found (2 real planner bugs, 2 stale test assertions)

### B1 — `_placement` for-else discards valid evict-to-fit placements (BUG)
File: llm_selector.py:250-256. The eviction loop:
```
for rm in removable:
    if freed >= m["vram_gb"]: break
    freed += rm["vram_gb"]; evs.append(rm)
else:
    continue   # <-- runs when loop EXHAUSTS without break, even if need now met
if freed >= m["vram_gb"] and evs: options.append(...)
```
The `for...else` fires on natural exhaustion (no `break`), so when evicting ALL removable non-pinned residents exactly meets the VRAM need, the valid placement is thrown away.
Proven: `python llm_selector.py plan --task longctx-256k` → `no_fit`. But red/G0 resident `mechanic-q4` is NOT pinned; evicting it frees 32GB >= 30.7GB required by `qwen-longctx`. Correct behaviour = place with 1 eviction.
Fix: drop the `else: continue`; after the loop do `if not (freed >= m["vram_gb"] and evs): continue` then append.

### B2 — resident no_op routing impossible: model can't be placed on its own occupied GPU (GAP)
File: llm_selector.py:297 (action="no_op") + `_placement`. Placement requires the target's FULL vram_gb free, but a resident model already occupies that space, so `free[own_gpu] < vram_gb` always → no placement → `select(TASKS["text"])` returns no model. Causes 2 selftest FAILs: "text picks a model", "text has 0 evictions".
Fix: in `_placement`, if the target model is already resident on (host,gpu), treat cost as 0 / emit zero-eviction placement so `no_op` routing works.

### T1 — stale assertion "video requires >=1 eviction"
selftest.py line ~457. Registry's smallest video model `wan2.1-1.3b-gguf` (6GB) fits pale/G0 (11GB free) with ZERO evictions, so plan correctly returns `evictions=[]`. Assertion is out of date with the registry; make it conditional.

### T2 — stale assertion "video plan has safety+load+probe+restore"
selftest.py line ~463. The restore/deferred step only exists when there are evictions; with zero evictions nothing to restore, so the step is legitimately absent. Assertion should gate on `evictions != []`.

## What IS verified working (pass)
- `status` renders fleet VRAM + residency + activation correctly (matches capability_registry.json).
- Video hotload plan emits correct DRY-RUN steps: [safety] active-generations==0 → [weights] ensure+SHA256 → [launch] comfyui CUDA_VISIBLE_DEVICES → [probe]. No live calls made. ✓
- Pinned protection holds: video plan does NOT evict pinned (atlas-q8/quinn-q4) without --allow-critical. ✓
- Determinism: two identical `plan --task video` runs byte-identical. ✓
- no_match on impossible modality. ✓

## Scope note for Orchestrator/Builder
This is DRY-RUN only — live load hand-off to Builder/Mechanic is intentionally not wired (correct, per wedge/async-ack lessons). Do NOT trust any plan for real execution until B1+B2 fixed and selftest green. VRAM figures remain planning estimates; ground truth = nvidia-smi per-GPU.
