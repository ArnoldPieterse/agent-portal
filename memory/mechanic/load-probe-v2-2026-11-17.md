# load_probe.py v2 upgrade + gap-marker (2026-11-17)

**Goal:** #4 Portal load test & capacity baseline
**Step:** Upgraded probe script for cross-host use; recorded day-2 gap entry.

## Changes to memory/ops/load_probe.py
- Added `--host` flag (default 127.0.0.1:8099) - no longer hardcoded localhost
- Added `--timeout` flag (default 15s)
- Added `target_unreachable` status marker when all requests fail at every level
- Error messages now captured up to 80 chars (was 40) for better diagnosis

## Baseline state (memory/ops/load-baseline.jsonl)
| ts | target | status |
|---|---|---|
| 2026-11-16 18:37:54 | localhost | ok (p50=127ms @10, p50=373ms @50, p50=1666ms @200) |
| 2026-11-17 13:33:28 | [redacted-LAN-IP]:8099 | target_unreachable (egress guard on Red sandbox blocks :8099 egress to White) |

## Next step
Run `python memory/ops/load_probe.py --host 127.0.0.1:8099` from **White** seat daily.
The v2 script will produce valid data when run on the same host as the portal.
Week-long tail needs ~5 more good days (currently day 1 of 7).

## Runbook note
load_probe.py was hardcoded to localhost; now takes --host flag. When running from a different seat than the portal, use `--host <portal-ip>:8099` and expect a gap-marker if egress is blocked.
