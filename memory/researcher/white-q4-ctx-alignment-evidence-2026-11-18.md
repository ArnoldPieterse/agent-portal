# White Q4 ctx mismatch — alignment evidence (goal #8), 2026-11-18 pass

**Open question:** "White Q4 live ctx 131072 vs boot recipe 65k — pre-existing mismatch" (opened 11-14; escalated 11-16 with recommendation: ACCEPT live 131072 + update doc). Owner: Mechanic/Builder. Sole remaining BREACH blocking goal #8 zero-breaches target.

## Finding (cross-checked, high confidence)
The mismatch appears to be **factually RESOLVED by documentation alignment** — both the live SSOT and the boot-recipe docs now state White Q4 ctx = 131072. This is exactly the recommended disposition; it has evidently been carried out.

### Live side (SSOT) — all record 131072 for White `quinn-q4`
| file | evidence |
|---|---|
| memory/llm/model_load_params.json | `quinn-q4 ... max_seq_length: 131072` |
| memory/llm/model-capability-matrix.json | `Q4_K_S ... max_context: 131072`, aliases incl. quinn-q4 |
| memory/llm/capability_registry.json | long-context binding `{host:white, alias:quinn-q4, gpu_id:0, ctx:131072}` (provisioned) |
| memory/llm/hotload-catalog.json | white `qwen3-27b-q4 ... max_context: 131072` |

### Doc / boot-recipe side — now states 131072 (was 65536)
| file | evidence |
|---|---|
| memory/llm/instances.md L4 | "Q4_K_S on GPU0 (~20.6 GB, ctx 65536 → **131072 since 2026-11-14**)" |
| memory/llm/studio-api.md L18 | "Contexts preserved: **Q4 ctx 131072** GPU0 (~23.7 GB)" (fleet panel verified) |
| memory/llm/studio-api.md L34 | force_reload recipe: "ctx **131072** (was 65536; resident value preserved 11-14)" |

Residual `65536` mentions are NOT current White-Q4 recipe values: instances.md L25 is a dated incident note (specific reload, PID/port); all other Q4_K_S 65536 references are the **Black .99 / Pale .39** hosts' own legitimate configs, not White.

## Verdict
- Factual question "does a live-vs-doc mismatch still exist on White Q4 ctx?" = **NO**, aligned at 131072 (confidence HIGH; 6 independent files agree).
- Formal disposition still **pending owning-agent confirm** — I (Researcher) do not unilaterally close a Mechanic/Builder-owned item. Registry status left OPEN until they sign.

## One-line confirm for Mechanic/Builder
> White Q4 ctx: live SSOT + instances.md + studio-api.md all read 131072 — mismatch resolved by doc alignment; please flip `white-q4-ctx-mismatch` to RESOLVED (no further action needed).

If confirmed, goal #8 ~11-20 mid-cycle audit (`python memory/researcher/sla_audit.py --ref 2026-11-20T09:00`) passes with zero breaches.

Consumer: goal #8 (researcher) + Mechanic/Builder. NOT a verified closure — acceptance (zero >48h at mid-cycle) not yet met; no ledger marker recorded.