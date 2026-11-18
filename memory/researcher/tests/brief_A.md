# BRIEF: Test brief A - mirror revert root cause
Date: 2026-11-18
Researcher: Researcher
Status: CLOSED

## Claim
The index.html pin revert is caused by memory_mirror.py restoring the pinned canonical file during each sync cycle.

## Evidence
[1] kb: memory/researcher/mirror-revert-fix1-epoch-landed-2026-11-18.md
[2] kb: memory/researcher/mirror-revert-pin-churn-2026-11-18.md
[3] web_search: https://example.com/fleet-mirror-notes

## Confidence
High — three independent leaves agree on the pin-restore mechanism.

## Open Questions
- none

## Follow-up Actions
- none
