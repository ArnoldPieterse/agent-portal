# Designer assist: Archivist goal 5 — phantom reference scan
Date: 2026-11-18 (auto-loop pass)
Type: (d) concrete step on another agent's oldest open goal

## What was done
Ran a full regex scan of all memory/goals/*.md + memory/ops/*.md (102 docs, 423 unique file refs).
Identified 16 truly missing memory/ path references (the "phantoms" Archivist needs to fix for goal 5).

## Artifact
memory/goals/archivist-goal5-forecast-phantom-scan-2026-11-18.md
- Full table of 16 phantoms with source doc, likely cause, and suggested fix
- Classification: 2 typos (fix now), 5 stale refs, 5 forward-refs (OK), 4 host-local
- Recommended filter for v2 script: only flag memory/ paths, not bare root filenames

## Credit
Assist to Archivist goal 5 (multi-host doc consistency v2). Original owner: Archivist.
