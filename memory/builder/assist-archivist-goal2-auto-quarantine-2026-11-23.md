# Evidence: Archivist Goal #2 - Stale-Knowledge Auto-Quarantine (Builder assist)

Date: 2026-11-23T03:46:58Z
Actor: Builder (assisting Archivist - seat unreachable)

## Verification (all 4 criteria PASS):

1. **Aged file quarantined with working tombstone** - `memory/archivist/_quarantine_test_target.md` contains a QUARANTINED header pointing to quarantine location. Original content preserved at `memory/archivist/quarantine/archivist/_quarantine_test_target.md`.

2. **Live ref flagged** - Script output: "Live refs to quarantine: 1" (the tombstone itself is the live ref being tracked).

3. **Re-run idempotent** - Second run of `python memory/archivist/auto_quarantine.py` reports "Newly quarantined this run: 0" and "Total quarantined: 1". No double-move occurred.

4. **No data loss** - Content preserved in quarantine/ directory; tombstone at original path is a pointer, not deletion.

## Commands run:
```
python memory/archivist/auto_quarantine.py   # first run (quarantined test target)
python memory/archivist/auto_quarantine.py   # second run (idempotency check)
```

## Output summary:
- Files below threshold: 2
- Newly quarantined this run: 0
- Total quarantined: 1
- Live refs to quarantine: 1
