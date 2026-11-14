Last updated: 2026-11-14 ~01:5x (daily model_id alias check, Orchestrator goal)

# Daily model_id alias check — 2026-11-14
Source of truth: agents.json `model_id` values vs Studio :8888 (GET /models + GET /api/settings/model-aliases) + portal /api/fleet.

## Local host (White, 127.0.0.1:8888)
| model_id | result | evidence |
|---|---|---|
| Qwen3.8-27B-Q8_0 | OK | /models lists it, loaded=true (Q8_0, ctx 262144) |
| atlas-q8 | OK | alias registered -> lmstudio-community\Qwen3.8-27B-Q8_0 (folder exists on disk) |
| quinn-q4 | OK | alias registered -> unsloth\Qwen3.8-27B-Q4_K_S (folder exists on disk) |

## Remote seats — UNVERIFIED this round (hosts unreachable at check time)
| model_id | seat host | result |
|---|---|---|
| scribe-q8, mechanic-q4 | IP_RED | host unreachable via /api/fleet |
| designer-q4, archivist-q8 | IP_PALE | host unreachable via /api/fleet |
| verifier-q4 (Builder seat also .99) | IP_BLACK | host unreachable via /api/fleet |

Fleet snapshot: White busy (Q8_0 resident, generations=1); all three LAN hosts state=unknown reason=unreachable.
ACTION: re-run remote half when any of .245/.39/.99 is up; log result here (append, do not delete).
