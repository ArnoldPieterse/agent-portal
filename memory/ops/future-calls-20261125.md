# Future-calls feature - 2026-11-25

Built + deployed in agent_portal.py (portal restarted via schtask PortalRun, live on :8099).

API:
- POST /api/future-calls  {caller, calls:[{id?, agent|self, prompt, chain_from?, delay_s?}], create_agents?:[{name, capabilities[], reports_to?, persona?, memory_seed?, studio?, api_key?, model_id?}]}
- GET  /api/future-calls  (states + outputs)

Semantics: N chained/unchained future LLM calls to self or mixed agents. {prev} = chain_from output; {out.<id>} = any completed call's output. New agents materialised first from capability spec + canned memory seed (memory/<Name>/MEMORY.md), seat inherited from reports_to parent. Audit: memory/ops/future-calls.jsonl.

Verified end-to-end: unchained (Builder) OK; chained {prev} (Verifier) OK; create_agents probe agent created on Black seat, answered, then cleaned up. t3 took ~7 min (thinking model, 4096 budget) - expected for async calls.

Queue for next continue:
1. DNA -> outlet art pipeline (Outlet orchestrates artistic expression of each DNA-code part)
2. HF survey -> best-fit model mapping per agent -> one-at-a-time downloads
3. Optional: UI panel for future-calls status; fix stale tunnel hostnames for unreachable seats (Designer/Archivist/etc - same failure mode as Black's tunnel, direct IP works)
