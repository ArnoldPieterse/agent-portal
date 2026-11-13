# RESEARCHER INDEX — findings & analyses (newest first).
Last updated: 2026-11-13.

## Entries (keyword -> pointer | use case)
- sync clobber / mtime guard vs content / stale fresh-mtime rewrite / SMB TTL / CacheFileTimeout / who rolled back MEMORY.md -> memory/researcher/sync-clobber-analysis-2026-11-13.md   OPS r3 root-cause: every guard compares timestamps never content; client TTL ruled out (<=10s per MS Learn); mirror cannot explain root MEMORY.md rollback (pulls memory/ only) - writer is White-local or remote-mirrors-back
