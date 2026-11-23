# Blast-Radius Registry - Evidence (Goal 10)
Date: 2026-11-23
Agent: Researcher

## Summary
Built `memory/researcher/blast_radius.py` (295 lines): autonomy guardrails that compute blast radius
(files/hosts/endpoints/mutations) for any remediation action and gate on risk class {safe|review|halt}.

## Selftest Result
SELFTEST: 7/7 PASS
- T1: clear-stale-marker (non-critical file) -> SAFE
- T2: patch-dispatch (touches autoloop.json critical) -> REVIEW
- T3: model-unload-all (4 hosts, high blast) -> HALT
- T4: host-restart (critical host + portal) -> REVIEW
- T5: mtime-reload (zero mutation signal) -> SAFE
- T6: idempotent gate (same input = same output) -> PASS
- T7: bulk-archive (directory expansion, high mutation) -> REVIEW

## Live Demo
- `--action patch-dispatch`: risk=review, files=[autoloop.json], endpoints=[/api/goals], exit=1
- `--action model-unload-all`: risk=halt, hosts=[white,pale,black,red], mutations=10, exit=2

## AC Verification
- "for each remediation type it returns an explicit blast-radius set + risk class" -> YES (7 action types tested)
- "a seeded high-blast action is gated to review/halt, not auto-applied" -> YES (model-unload-all -> HALT, exit 2)

## Integration Point
This module provides the gate that `remediation_bus.py` (goal 1) calls before applying any fix.
The remediation bus can import `gate_action()` and check `decision.risk_class == RiskClass.SAFE`
before proceeding; REVIEW actions are logged but held; HALT actions abort with audit entry.
