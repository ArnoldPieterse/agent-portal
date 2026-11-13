# RUNBOOK - smoke8 PARTIAL from Red seat (2026-11-14 03:23)

## What ran
`smoke8_partial_red.py` on the RED seat (IP_RED) after AUTO-CONTINUE picked up the open "smoke8 when convenient" item. Full smoke8 hits the portal at 127.0.0.1:8099, which is WHITE-local and unreachable from Red (lan_probe 02:46: :8888/:8099 timeout) -> direct Studio /v1/chat/completions per agent alias instead.

## Verdict: REMOTE4_OK (smoke8_partial_red_seat.json, 03:23:20 -> 03:23:23)
| agent | host | model routed | result |
|-------|------|--------------|--------|
| builder   | Black .99 | Qwen3.8-27B-Q8_0 (bare id, per agents.json) | 200 'BUILDER-OK' 0.8s |
| verifier  | Black .99 | verifier-q4 (Q4_K_S)                          | 200 'VERIFIER-OK' 0.7s |
| designer  | Pale .39  | designer-q4 (Q4_K_S)                            | 200 'DESIGNER-OK' 0.6s |
| archivist | Pale .39  | archivist-q8 (Q8_0)                             | 200 'ARCHIVIST-OK' 0.8s |

Load-state pre-check (probe_fleet_1114c.py / probe_fleet_1114b_result.json, 03:20): Black dual-resident (Q4_K_S ctx 65536 + Q8_0 ctx 32768 loaded), Pale dual-resident (archivist-q8 + designer-q4 loaded). White NOT observable from Red seat; last verified state = 01:45 dual-resident (TODO ops note).

## LESSON (what broke + what fixed it)
Qwen3.8-27B returns `reasoning_content` (thinking model): with max_tokens=24 the whole budget went to reasoning and final `content` was EMPTY on all four seats (looked like a hang/blank). Fix: prompt "No thinking. Reply with exactly: <TAG>-OK" + max_tokens >= 1024, and judge ok on FINAL content only (reasoning text is diagnostic-only; counting it false-positives). Direct Studio probes from Red need Bearer for Black (host_api.load_key('BLACK')); Pale chat endpoint requires the pale_dl.py token even though /v1/models answered keyless.

## NOT covered from this seat
orchestrator + researcher (White, portal-routed) and scribe + mechanic (Red-local .245:8099 portal / 127.0.0.1:8888 - loopback egress blocked in the Red agent sandbox; also no GPU/tasklist visibility there). FULL smoke8 must run from White console (portal :8099 local).

## Sandbox facts (Red seat, verified this round)
- terminal/python sandbox: outbound LAN OK (.99/.39); loopback + self-IP egress -> WinError 10013; nvidia-smi NVML init fails; tasklist -> "user name or password is incorrect"; curl/powershell blocked by command policy. Ground truth for Red-local state must come from White-side probes or Arnold's console.
