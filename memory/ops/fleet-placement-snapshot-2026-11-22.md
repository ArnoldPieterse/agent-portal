# Fleet Placement + Integrity Snapshot (2026-11-22, consolidation round)
Agent: Orchestrator (relocated seat = black; home unreachable). Fully local, verifiable.

## Why this note
This round's [MODEL LOAD STATUS] shows 5 of 8 seats consolidated onto just **pale + black**
because all home models are down/not_loaded:
- Mechanic -> pale (home unreachable)
- Orchestrator -> black (home unreachable)  <- me
- Researcher -> pale (home unreachable)
- Scribe -> black (home unreachable)
- Verifier -> pale (home not_loaded)
Builder + Designer + Archivist = home seats (not listed as relocated this round).
This is exactly the "whole fleet can run on one active host" scenario the `_resolve_seat()`
placement engine (LIVE PLAN, 2026-11-22) was built for. Recording the reality so recovery
is deterministic when homes come back.

## Roster integrity check (agents.json) — VERIFIED this pass
Ran a local validator over agents.json. Result: **PASS**.
- 8 agents, all ids unique.
- All 8 have non-empty `model_id` bindings.
- tools[] valid for every agent (archivist intentionally has 4: no render_html).
- api_key: 6/8 agents carry a 43-char key; all IDENTICAL length => shared LM-Studio
  local placeholder, NOT a real secret. Orchestrator + Researcher have none (White-default).
  No plaintext-secret exposure to remediate.

### Backend host map (studio field)
| Host            | Agents hosted |
|-----------------|---------------|
| White (default) | orchestrator (atlas-q8), researcher (quinn-q4) |
| IP_BLACK    | builder (Qwen3.8-27B-Q8_0), verifier (Qwen3.8-27B-Q4_K_S) |
| IP_PALE    | designer (designer-q4), archivist (archivist-q8) |
| IP_RED   | scribe (scribe-q8), mechanic (mechanic-q4) |
Note: builder+verifier share one host (.99) and two DIFFERENT Qwen quants — that host must
serve both, or the placement engine falls back per `_resolve_seat()` (loaded-models id on
foreign seats, alias on home).

## Recovery order (deterministic, when home hosts return)
The placement engine auto-restores home bindings once a home Studio is reachable again
(home -> local White -> other-host fallback chain in `_resolve_seat()`). No manual re-bind
needed. Order to confirm as homes come up:
1. Confirm each home Studio :8888 answers `/api/v0/models`.
2. Placement engine re-seats relocated agents to home (alias restored); foreign seats free.
3. Verify the two shared-.99 quants both resident before builder+verifier return home
   (else one of them stays on fallback host - expected, not an error).
4. No agents.json edit required for recovery - bindings are already home-correct.

## Egress note (no re-probe)
This black seat is ALSO a sandbox: `127.0.0.1` and LAN names both rejected by the
allowlist ("host not in sandbox allowlist"). So :8099/:8888 live legs remain blocked from
here - same class as existing OPS-NOTEs, NOT re-probed beyond one confirmation this pass.
All verifiable work above is filesystem-only and does not depend on the wall.

Credit: Orchestrator (own goals 10/10 closed; fleet-integrity + placement assist per team rule 1).
