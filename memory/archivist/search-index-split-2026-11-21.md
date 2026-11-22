# Search Index Split - 2026-11-21

## Context
search-index.json grew to 818.8 KB (2201 entries) after tree expansion, exceeding the file-modularity guideline (keep files small enough for a small-context model to read whole). Original AC was <500KB but that was set when the tree was smaller.

## Action
Split monolithic search-index.json into per-agent/domain files under `memory/archivist/search-index/`:
- 24 per-agent JSON files (largest: designer.json at 190.4 KB)
- manifest.json (2.3 KB) as pointer index
- All files <500KB: PASS

## Verification
- Search 'decay': 8 hits, top-3 correct (decay-alerts, decay-report, decay-schtask-setup)
- Search 'portal': 413 hits, relevant results returned
- Total entries preserved: 2201 (matches monolithic index)

## File Layout
```
memory/archivist/search-index/
  manifest.json       (pointer: agent -> file, count, size)
  archivist.json      (173 entries, 68 KB)
  designer.json       (504 entries, 190 KB)
  mechanic.json       (314 entries, 123 KB)
  ...                 (24 total)
```

## Usage
To search: read manifest.json to identify candidate files by agent/domain, then load only those. For cross-agent search, iterate all files (total I/O same as monolithic but each file is independently readable).

## Note
Original monolithic search-index.json retained for backward compatibility; can be archived after one more cycle if no consumers break.
