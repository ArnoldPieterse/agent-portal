---
source: archivist\_ingest_input_smb_mirror.md
ingested: 2026-11-16
ingested_by: Archivist
confidence: medium
ttl_days: 30
topic: mechanic
---

# SMB Mirror Sync Architecture (Research Note)

- Source: Code read of memory_mirror.py + ops runbooks, 2026-11-13.
- The mirror runs every 5 minutes via Windows Task Scheduler on White, pushing files to Red/Pale/Black over SMB shares.
- Conflict resolution uses mtime comparison: a file is pushed only if src_mtime > dst_mtime + 0.5s tolerance (MTOL constant).
- Known defect (fixed 2026-11-13): the original comparison used abs(src-dst) > MTOL, allowing a STALE source with an older mtime to overwrite a newer destination if the difference exceeded 0.5s in either direction.
- Fix: strict src > dst + 0.5s (one-way freshness check). Patch staged at memory/mechanic/memory_mirror_fixed.py.
- Files excluded from mirror: __pycache__, .git internals, and paths matching .gitignore denylist.
- The portal (agent_portal.py) also does per-chat-turn sync of MEMORY.md and TODO.md for immediate consistency within a session.
- Confidence: high (code-verified against source).
- TTL: 30d (architecture doc; re-verify after any mirror code change).
