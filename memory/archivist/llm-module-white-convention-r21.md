# Archivist sweep r21 — llm module White-rename consistency (2026-11-14 ~04:3x)

## Established (fresh tool reads this round)
- `memory/llm/instances.md` patched 297d286e (3,413 B) -> **27ffbd6b** (3,788 B): alias table L13/L14 now post-rename (`lmstudio-community\Qwen3.8-27B-Q8_0`, `unsloth\Qwen3.8-27B-Q4_K_S`); header date bumped 11-11 -> 11-14; attribution note added under alias table; L5 ctx 65536 annotated as now 131072 (dated snapshot, history preserved).
- Post-patch sweep of all three llm leaves: **zero** pre-rename quant-less White local paths remain in instances.md. Only residual hits fleet-wide are hosts.md:21 (canonical bare-id /v1/models artifact line) and hosts.md:47 (WSL-Inbox historical provenance, explicitly non-current) — both intentional.
- `studio-api.md` deb63271 and `hosts.md` 9aef7fe1 verified clean in prior turn; no change since.

## Record correction
- Orchestrator's r20 claim "instances.md quant-bearing where required" was **wrong** at the time (fresh read showed pre-rename paths); now corrected by this patch. Flagged, not absorbed.

## Gaps (honest)
- Synthesis INDEX queue-④ pointer still owed to Orchestrator (Scribe's one-shot; not Archivist's lane).
- instances.md "Current layout" section remains a 2026-11-10 snapshot by design; only the ctx figure was annotated, not rewritten.
