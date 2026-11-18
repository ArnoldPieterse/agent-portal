# Black (IP_BLACK) Studio failover - 2026-11-16 ~21:35 (Studio seat)

## Incident
Group runs wedged in auto-continue loop; user messages queued. Root cause chain:
1. Black's inference engine holds 2 generations stuck since ~20:47 (handles 9f8084ae..., 5955816b... on Qwen3.8-27B-UD-Q4_K_S) - every new completion times out at 20s.
2. Studio's own POST /api/inference/cancel returns cancelled:0 (thread hung inside engine, ignores cancel).
3. Builder + Verifier seats live on Black -> "unreachable" at run start -> rounds can't conclude.

## Remote restart blocked
WSMan reachable but Access is denied for White/empty-pass (WinRM auth policy); no WinRM/PSRemoting credential available from White. Needs a human at Black: restart the Unsloth Studio desktop app (or reboot), then restore routing.

## Emergency fix applied (this file = the rollback record)
- agents.json backup: memory/ops/agents.json.pre-black-failover.20261116-213632.bak
- Builder: studio -> local White, model_id Qwen3.8-27B-Q8_0 (loaded on White), api_key cleared
- Verifier: studio -> local White, model_id Qwen3.8-27B-Q8_0 (was verifier-q4 alias, Black-only), api_key cleared
- Also fixed stale run_state.json (busy=True from the wedged run) + portal restarted via PortalRun.

## Restore when Black is healthy
1. Put Builder/Verifier back to studio=http://IP_BLACK:8888 with their sk-unslo... keys (in the .bak file).
2. Verifier model_id back to verifier-q4.
3. Verify: GET /api/models/status shows ok for both; run one group round.

## Capacity note
White now hosts this session + Builder + Verifier turns on Qwen3.8-27B-Q8_0. Turns are sequential (45s settle), acceptable but watch latency.
