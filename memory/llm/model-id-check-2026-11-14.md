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

## 2026-11-15 ~11:0x - REMOTE HALF RE-RUN: PASS 6/6 (all three hosts powered back on by human ~10:5x)
| model_id | seat host | result |
|---|---|---|
| Qwen3.8-27B-Q8_0 (Builder) | IP_BLACK | OK - resolves as folder model in /v1/models (not an alias; same pattern as White) |
| verifier-q4 | IP_BLACK | OK - alias registered on host |
| designer-q4 | IP_PALE | OK - alias registered on host |
| archivist-q8 | IP_PALE | OK - alias registered on host |
| scribe-q8 | IP_RED | OK - alias registered on host |
| mechanic-q4 | IP_RED | OK - alias registered on host |
Local re-check same round: Qwen3.8-27B-Q8_0 loaded=true; aliases atlas-q8 + quinn-q4 registered (3/3 OK).
SURFACED STATE (Mechanic goal 9): all three remotes are UP but have NO model resident in VRAM (/v1/models lists registered models + aliases, none loaded) - remote agents cannot generate until their bound model is loaded. Fleet panel shows this live (state=idle, no models). Decision needed: load the six bound models (fleet_reload.py has the per-host recipe) or leave idle.
