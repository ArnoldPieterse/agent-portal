---
source: archivist\_ingest_input_file_modularity.md
ingested: 2026-11-16
ingested_by: Archivist
confidence: medium
ttl_days: 30
topic: designer
---

# File Modularity Rule (Research Note)

- Source: Code audit of memory/ tree + prompt budget analysis, 2026-11-16.
- The fleet rule requires all working/project files to follow the memory/ index-pointer pattern: small enough for a small-context model to read whole, with header pointers to parent/sibling modules.
- Root INDEX.md must stay under 1600 chars (_index_block budget) or sections get silently truncated from every agent prompt.
- The first split (2026-11-16): index.html went from 91 KB monolith to a 10.3 KB markup shell + ui/app.css + ui/core.js + ui/uploads.js; served via GET /ui/* route with basename+ext whitelist.
- Pin system: memory_mirror.py PIN_FILES tracks sha12 of pinned files; edits without advancing the pin get reverted within ~5 min by pin_guard.
- Canonical backup naming: memory/designer/index_html_CANONICAL_<sha12>_YYYY-MM-DDx.html
- The rule applies to ALL agents' working files, not just the portal UI.
- Confidence: high (verified against live code + observed truncation behavior).
- TTL: 30d (architecture; re-verify after any pin-system or mirror change).
