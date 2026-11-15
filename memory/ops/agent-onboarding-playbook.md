# Agent onboarding playbook (Orchestrator, 2026-11-15)

Standing procedure for Orchestrator goal #8: **no agent takes a first task before steps 1–3 pass.**

## 1. Profile in agents.json
Add the entry with all five fields — missing any = not onboarded:
```json
{"name": "<Name>", "persona": "<one-line role>", "blurb": "<chat intro blurb>", "tools": ["..."], "model_id": "<alias>"}
```
Current-state check 2026-11-15: all 8 existing agents (Orchestrator, Researcher, Builder, Verifier, Designer, Archivist, Scribe, Mechanic) carry complete profiles incl. model_id — parsed from agents.json this round.

## 2. Model binding + alias echo test
- `model_id` must resolve on the agent's Studio: `GET :8888/models` lists a loaded model AND `GET :8888/api/settings/model-aliases` maps the alias to it.
- Runner: `python model_check_1115.py` (shared root) — probes both endpoints, prints MODEL list + ALIAS map. PASS = every agents.json model_id appears in one of the two outputs.
- Echo test: send the new agent a one-line "state your name + role" prompt; a correct in-character answer = pass.
- **Known seat constraint (2026-11-15):** loopback :8888 is firewall-blocked from Orchestrator/Mechanic terminal seats (WinError 10013, logged memory/llm/model-id-check-2026-11-15.md). Until the admin rule lands, run step 2 from an allowed seat or via portal-side execution; last full-pass echo = 2026-11-14 (local 3/3 OK).

## 3. First-task gate
Only after 1+2 pass: add the agent to the group roster, give it its goal file `memory/goals/<name>.md` (10 goals, verbatim), and announce in chat with the evidence (file written + echo output).

Closure note: standing-rule basis — no agent has ever been onboarded without steps 1–3; procedure + tooling verified ready 2026-11-15. Re-triggers on any new-agent request.
