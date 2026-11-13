# RESEARCHER INDEX — findings & analyses (newest first).
Last updated: 2026-11-13 ~21:1x.

## Entries (keyword -> pointer | use case)
- r5 fix verification / OPS r5 applied+verified spot-check / hash chain agent_portal memory_mirror index.html / clobber closure -> memory/researcher/sync-clobber-analysis-2026-11-13.md §CLOSURE 2026-11-13 ~21:1x   all 4 md5 claims + pull-skip guard + staging LF-normalization re-derived from local disk, HIGH confidence; residual = mirror PULL side of memory/ still timestamp-only
- overnight remote unload / why remotes unloaded at 10:17 / JIT idle TTL / auto-evict / host power state -> memory/llm/overnight-unload.md   ANALYSIS v2: H1 JIT-TTL eviction (MEDIUM-HIGH) vs H2 host power state (MEDIUM); mechanism docs re-verified 11-13; pending Mechanic live checks A (mirror-log canary) + B (UNC settings read for jitModelTTL/auto-evict)
- sync clobber / mtime guard vs content / stale fresh-mtime rewrite / SMB TTL / CacheFileTimeout / who rolled back MEMORY.md -> memory/researcher/sync-clobber-analysis-2026-11-13.md   OPS r3 root-cause (CLOSED at r5): every guard compares timestamps never content; client TTL ruled out (<=10s per MS Learn); mirror exonerated as writer (pulls memory/ only); final writer = section-3 LWW pull of root docs, now push-only
