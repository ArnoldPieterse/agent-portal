# Researcher cross-check — Arnold White-console pass, bundle v2 0809fd6a (r69, 2026-11-14)

First-party on my seat (sandbox _default root). Purpose: confirm PRE-CONDITIONS for the sole human gate + verify what I can without White console access.

## VERIFIED first-party (evidence, this seat)
- **Bundle v2 apply-list byte-exact:** `memory/orchestrator/white-apply-bundle-v2-r45.md` = `0809fd6ac7ea / 4,529 B`; all 8 items present. Item 7 (dcabots re-prompt, atlas-q8 pre-check SATISFIED since 01:45, count=2 recipe) + item 8 (smoke8) confirmed in text.
- **Stamp target byte-exact:** `memory/designer/index_html_stamp_final_107cbd93.html` = `107cbd9357c8 / 69,888 B` — matches bundle item-1 pin exactly.
- **recover_all.py dual-path logic VERIFIED against source (not just keywords):**
  - `_resolve(base_dir,*names)` L8-15: returns first existing dir, else falls back to `names[0]` (new name). Q4P=`_resolve(unsloth,"Qwen3.8-27B-Q4_K_S","Qwen3.8-27B-GGUF")`; Q8P=`_resolve(lmstudio-community,"Qwen3.8-27B-Q8_0","Qwen3.8-27B-GGUF")`. => works pre- AND post-rename, as claimed.
  - `dual_ok()` L146-152: `q4_in = new OR old`, `q8_in = new OR old` in llama-server cmdline + VRAM gates (>=2 servers, vram0>18GB, vram1>25GB). => accepts either cmdline form, as claimed.
  - **Design nuance confirmed (not a defect):** both variants can resolve to bare folder `Qwen3.8-27B-GGUF`, so name check is ambiguous; the code therefore relies on count-based guard — consistent with item 7's `GET :8888/v1/models` count=2 requirement and OPS-NOTE diagnosis.

## ABSENT from this seat (=> pass NOT yet landed here)
- `white_realias_result.json` — absent tree-wide (the rename/unload/load result artifact).
- `ac_a2_live_leg_r20/r21_result.json` — absent; only the `.py` scripts exist at `memory/mechanic/`. Console-produced, structurally unreachable from agent seats (r19–r45).
- `probe_fleet_1114b_result.json` — absent tree-wide.

## Conclusion / confidence
- **High confidence** in the pre-condition state: bundle + stamp target byte-exact, recover_all.py dual-path guard matches intent. No defect found; name-ambiguity is handled correctly by design.
- **Cannot confirm from this seat** that Arnold's pass actually EXECUTED (rename+unload/load+live-leg r21+smoke8): those artifacts are console-produced and absent here. Remains structurally human-gated — nothing agent-executable. Confidence in "pass executed" = LOW until a result JSON lands + Orchestrator first-party adjudicates.

