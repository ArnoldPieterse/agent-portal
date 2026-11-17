# Goal #10 - CDP Capture Script Ready (2026-11-18)

## What was done this pass
Rewrote `capture_baseline.py` to use CDP (Chrome DevTools Protocol) via WebSocket instead of the fragile `--screenshot` + wrapper-HTML approach.

**Changes:**
- Covers all 6 portal panels: chat, queue, fleet, files, goals, ops
- Two resolutions: 1920x1080 (desktop) + 768x1024 (tablet) = 12 screenshots total (exceeds >=8 requirement)
- Proper CDP panel switching via `Runtime.evaluate` (no wrapper HTML needed)
- SHA256 hash manifest written to `baseline/MANIFEST.json`
- `--record` flag auto-calls `goal_ledger.py --record designer 10` on success
- Clean browser lifecycle (launch, connect, capture, terminate)

## One-command closure (non-sandbox seat with Edge/Chrome + portal running)
```
python memory/designer/capture_baseline.py --url http://localhost:8099 --record
```

## Blocker status
Same sandbox wall as before: no browser binary + no CDP port access from this seat.
Already logged in `memory/ops/blockers.md`. Do NOT re-probe.

## Verification pending
- [ ] Run the script from a non-sandbox seat (White ops terminal / RDP)
- [ ] Confirm 12 PNG files appear in `memory/designer/baseline/`
- [ ] Confirm MANIFEST.json has 12 entries with sha256_12 hashes
- [ ] Ledger auto-records via --record flag
