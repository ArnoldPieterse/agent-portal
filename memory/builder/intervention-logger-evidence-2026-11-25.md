# Intervention Logger Hook - Evidence
Date: 2026-11-24 21:19 UTC

## What was built
`memory/builder/intervention_logger.py` - detects human intervention patterns in chat messages.

## Detection patterns
- **unblock**: unblock, clear block, go ahead, proceed, treat as normal, relocated, failover
- **redirect**: redirect, reprioritize, change priority, stop doing, focus on, change course, pivot
- **approve**: approved, lgtm, ship it, green light, sign off, accepted

## Verification (selftest: 9/9 PASS)
- 5 matching messages correctly classified (type + agent)
- 3 non-matching messages correctly ignored (no false positives)
- Log file structure verified: ts, agent, type, context fields present
- Live --check mode works standalone

## Integration point
Import check_message + log_intervention in agent_portal.py message handler.
Module is standalone-testable without portal dependency.
