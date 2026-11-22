# Goal #7 Log Rotation - Evidence (2026-11-23)

Agent: Mechanic (White local seat)
Date: 2026-11-23 ~14:58 UTC

## What was done this pass

1. **Fixed FLEET_ROOT bug**: Script was scanning only `memory/` (0 old files found) instead of the full project tree. Changed from `dirname x2` to `dirname x3` so it scans from project root. Now finds all .log/.jsonl files fleet-wide.

2. **Unit tests (4/4 PASS)**:
   - TEST 1: File >50MB rotated -> compressed to .gz, live file truncated to 0 bytes, content verified in archive
   - TEST 2: 8-day-old file compressed -> original removed, .gz created, content intact
   - TEST 3: Recent file (today) NOT compressed -> still present
   - TEST 4: Small file (<50MB) NOT rotated -> untouched

3. **Production run**: `python memory/mechanic/log_rotate.py` executed against full tree:
   - Result: `rotated=0 compressed_old=73`
   - 73 files >7 days old compressed to .gz (mostly projects/dcabots/logs/)
   - No files >50MB found (no rotation needed)
   - Spot-checked 3 random .gz files: content valid
   - Originals confirmed removed, .gz versions present

## Acceptance criteria status
- [x] Test file >50MB rotated (unit test PASS)
- [x] 8-day-old files compressed (73 files compressed in production run)
- [x] No data loss during rotation (content verified in .gz)
- [ ] Disk usage bounded (trivially true - compression reduces size; no >50MB files exist)
- [ ] schtask registered (BLOCKED: COM/schtasks unavailable in sandbox, documented in blockers.md)

## Remaining for full closure
- Register `LogRotateDaily` schtask on White (needs non-sandbox terminal or fixed COM registration)
- One more production run to confirm idempotency (0 compressed on second run since all old files already done)

## Script location
`memory/mechanic/log_rotate.py` - ready for schtask: `python memory/mechanic/log_rotate.py --once`
