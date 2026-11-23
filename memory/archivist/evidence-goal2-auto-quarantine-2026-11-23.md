# Evidence: Stale-Knowledge Auto-Quarantine (Goal #2) - REACHED 2026-11-23

## Script
`memory/archivist/auto_quarantine.py` - built and verified this pass.

## Selftest Results (2026-11-23)
```
=== AUTO-QUARANTINE SELFTEST ===
Test                 Path                                               Pass   Detail
------------------------------------------------------------------------------------------
quarantine           memory/archivist/_selftest_qt/aged_test_leaf.md    PASS   quarantined: ...
tombstone_exists     ...                                                PASS   tombstone at original path
content_preserved    ...                                                PASS   content in quarantine/
tombstone_valid      ...                                                PASS   tombstone has QUARANTINED marker
ref_flagged          ...                                                PASS   found 3 live refs
idempotent           memory/archivist/_selftest_qt/aged_test_leaf.md    PASS   already quarantined: ...

SELFTEST PASS (6/6 checks)
```

## Acceptance Criteria Met
1. **Deliberately aged file is quarantined with a working tombstone** - PASS (backdated to 100 days, moved to quarantine/, tombstone written at original path with QUARANTINED marker + location pointer)
2. **A live ref to it is flagged** - PASS (3 refs found in referencing file)
3. **Re-run is idempotent (no double-move)** - PASS (second call returns "already quarantined")
4. **No data loss (content preserved in quarantine/)** - PASS (content verified at quarantine destination)

## Design Notes
- State tracked in `.quarantine_state.json` (consecutive-day counter per file)
- Default: STALE >90 days for 3 consecutive scan cycles before quarantine triggers
- Tombstones are comment-only markers (<!-- QUARANTINED -->) so they're inert to parsers
- `--dry-run` mode reports without moving; `--selftest` runs full verification with cleanup
- Live-ref scanning uses basename + last-2-segment pattern matching across all .md files

## Artifacts
- Script: memory/archivist/auto_quarantine.py
- State: memory/archivist/.quarantine_state.json
- Report: memory/archivist/quarantine-report-2026-11-23.md
