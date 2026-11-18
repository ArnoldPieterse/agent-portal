---
source: archivist\_ingest_input_lmstudio_ctx.md
ingested: 2026-11-16
ingested_by: Archivist
confidence: medium
ttl_days: 30
topic: portal
---

# LM Studio Context Window Behavior (Research Note)

- Source: Direct observation + LM Studio docs, 2026-11-14.
- LM Studio on this fleet uses a 32768-token context window by default for all loaded models.
- When reasoning_effort is set to 'high' or 'default', the model can consume the entire window on internal reasoning, leaving zero tokens for output - producing empty HTTP responses (observed as HTTP 400 with empty body).
- Setting reasoning_effort to 'low' in agents.json constrains the thinking budget, preserving room for actual output tokens.
- The portal maps reasoning_effort from agents.json to the LM Studio API parameter at agent_portal.py line ~1040.
- Affected models observed: Qwen3.8-27B-Q8_0 (Black), and any model with extended thinking enabled.
- Recovery: reduce reasoning_effort in agents.json, respawn the agent (effective at next spawn, not mid-session).
- Confidence: high (reproduced 3x across different agents on 2026-11-13/14).
- TTL: 90d (stable platform behavior unless LM Studio updates change defaults).
