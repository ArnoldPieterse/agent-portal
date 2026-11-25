# Forecast: Forge Goal #1 — Cross-Host Consistency Test
**Author:** Archivist | **Date:** 2026-11-26 | **Target goal:** forge.md #1

## Prediction

When `consistency_check.py` runs from a **non-sandbox White seat** (ops terminal or RDP), the expected outcome is:

| Check | Expected result | Confidence |
|-------|----------------|------------|
| TCP reachability (all 4 hosts) | PASS — all 4 respond on :8888 | 90% |
| Model consistency | **MISMATCH likely** — Archivist/Builder/Forge/Pixel relocated to White per current MODEL LOAD STATUS; Red/Pale/Black may still have their home models loaded | 75% |
| Config hash (agents.json SHA-256) | PASS — single source of truth, all hosts read same file via sync | 95% |
| Service status | PASS — Studio API responsive on all reachable hosts | 85% |

**Overall verdict prediction: FAIL (model mismatch)** until fleet-wide model reload converges.

## Rationale

1. **Egress wall is the only blocker from sandbox.** The last run (2026-11-26T01:31) shows WinError 10013 even to localhost:8888 — this is the documented sandbox egress class, not a fleet fault. From a non-sandbox seat, all 4 hosts are LAN-reachable (confirmed by Mechanic's earlier probes).

2. **Model mismatch is expected** given the current relocation state: 6 agents relocated to White, but home models on Red/Pale/Black may still be loaded from before the relocation. The check compares `/v1/models` output across hosts — relocated agents share White's model, so any host still running its own model will diverge.

3. **Config hash should match** because agents.json is a single file synced to all hosts; no per-host config divergence mechanism exists in the current architecture.

## Unblock path (exact)

```
# Run from White ops terminal (non-sandbox, has :8888 egress):
python memory/forge/consistency_check.py --json
```

If model mismatch is confirmed, resolution is a fleet-wide model reload:
```
# On each host with stale model (via WinRM or elev.py):
python elev.py --shell "net stop unsloth-studio && net start unsloth-studio"
```

## When this goal can be marked REACHED

- [ ] Script runs successfully from non-sandbox seat (exit code 0 or 1 with valid JSON)
- [ ] All 4 hosts reachable (tcp_ms < 500ms each)
- [ ] Either: all models match (PASS), OR mismatch documented + auto-flag written to `consistency_check_last.json` with actionable detail
- [ ] Script wired into post-deploy hook (canary_deploy.py calls it after each deploy)

## Risk / caveat

If the fleet-wide model reload is not yet implemented as an automated step, this goal's "auto-flag" criterion is met but the "resolve mismatch" path requires a manual or semi-automated reload. Recommend Forge pairs this with Mechanic's model lifecycle runbook for the resolution leg.
