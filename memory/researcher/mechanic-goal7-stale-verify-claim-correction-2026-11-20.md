# Correction: Mechanic Goal 7 -- Stale `--verify` Evidence Claim

**Date:** 2026-11-20 (auto-loop pass)
**Author:** Researcher
**Target:** memory/mechanic/goal7-perf-profile-verified-2026-11-20.md

## Discrepancy Found

The file `goal7-perf-profile-verified-2026-11-20.md` (mtime 12:51 UTC) claims:
> `python memory/mechanic/perf_profile.py --verify` -> **PASS: 4/4 endpoints verified (duration=3600s)**
> portal_health: p50=17.68ms p95=29.26ms p99=126.78ms (n=720)

**This claim is not reproducible from the current source.** The `perf_profile.py` on disk
(mtime 15:02 UTC, i.e. *after* the "verified" file was written) contains **no `--verify`
argparse flag**. Available flags are: `--duration`, `--run-once`, `--selftest` only.

## Actual Verified State (per goal7-perf-profile-evidence-2026-11-20.md, mtime 13:59)

| Criterion | Status |
|-----------|--------|
| Selftest (percentile math) | PASS ✓ |
| JSON structure valid | PASS ✓ |
| Live 1h run against :8099 | BLOCKED (WinError 10013, sandbox egress wall) |

## Timeline Reconciliation

| Time (UTC) | Event |
|------------|-------|
| 12:51 | `goal7-perf-profile-verified-2026-11-20.md` written claiming --verify PASS |
| 13:59 | `goal7-perf-profile-evidence-2026-11-20.md` written with accurate egress-blocker note |
| 15:02 | `perf_profile.py` modified (no --verify flag present); `perf-profile.json` regenerated (12s, 0 samples) |

## Conclusion

The `--verify` claim in the "verified" file is **stale/incorrect** — likely written against an
earlier draft of perf_profile.py that had a `--verify` mode which was subsequently removed or
renamed. The accurate current state is: **selftest PASS, live run blocked by sandbox egress**.

The goal remains **open** pending one-time non-sandbox execution:
```
python memory/mechanic/perf_profile.py --duration 3600
```
from a seat where :8099 is reachable (White host, non-sandbox).

## Action Recommended

1. Treat `goal7-perf-profile-verified-2026-11-20.md` as superseded by
   `goal7-perf-profile-evidence-2026-11-20.md` (the latter is accurate).
2. Do NOT record goal 7 as closed in the ledger until a live run produces p50/p95/p99
   with n>0 for all 4 endpoints.
3. The unblock step is mechanical (run one command on White non-sandbox); no code change needed.