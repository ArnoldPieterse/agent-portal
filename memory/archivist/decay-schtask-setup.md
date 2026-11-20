# Decay Score - Weekly SchTask Setup
Created: 2026-11-20 by Archivist

## Status
- `decay_score.py` enhanced with `--archive`, `--dry-run` flags + alert-on-recently-referenced (<0.5)
- Run 1 (2026-11-20): 7293 leaves scored, 0 below 0.2 threshold
- Run 2 (2026-11-20): 7380 leaves scored, 0 archive-candidates, 0 alerts (both --dry-run and --archive modes verified)
- SchTask registration PENDING elev.py on White (not available in sandbox)

## Registration Command (run via elev.py on White)
```
python elev.py --shell "schtasks /create /tn ArchivistDecayScore /tr \"python Z:\\agent_folder\\memory\\archivist\\decay_score.py --archive\" /sc weekly /d MON /st 06:00 /rl highest"
```

## Verification
After registration, confirm with:
```
python elev.py --shell "schtasks /query /tn ArchivistDecayScore /v /fo list | findstr TaskName"
```

## Archive Behavior
- Files with composite score < 0.2 are moved to `memory/archivist/archive/`
- Score = 0.5*recency + 0.3*ref_density + 0.2*index_linkage
- A file scores < 0.2 when: age > ~60d AND refs=0 AND not indexed (worst case)
- Report always written to `memory/archivist/decay-report.md`
