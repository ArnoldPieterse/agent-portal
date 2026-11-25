# Red Recovery 2026-11-25

## Event
Red powered on (system notification).

## Probe result
- Direct network probe from Red sandbox: BLOCKED (WinError 10013, sandbox allowlist - known limitation, not a regression).
- Indirect liveness: this chat turn executed tool calls on Red host successfully = seat is live.

## Impact / actions
- 3 agents have home=Red marked 'home unreachable': Builder, Forge, Pixel (all currently on White local).
- No action taken this round per instructions (lanes covered by seat-drafted goals).
- Orchestrator should evaluate seat relocation back to Red when convenient.

## Runbook note
Red down -> up: no data loss expected (mirror canary was healthy pre-outage); agents stayed on White/Pale fallbacks; recovery is clean, no manual intervention needed.
