---
source: archivist\_ingest_test_input.md
ingested: 2026-11-16
ingested_by: Archivist
confidence: high
ttl_days: 90
topic: llm
---

# LM Studio Context Window Notes

## Routing

- The Black host runs the 70B model on :8888 with a 32k context window.
- When context exceeds the limit, the portal routes to the 8B fallback.

## Ops

- After a reboot, LM Studio must be restarted via the service probe before inference resumes.
