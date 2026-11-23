# cockpit-staleness-monitor-cwd-fix-2026-11-24

**STATUS: VERIFIED PASS (genuine)** — Cockpit Live-Staleness Monitor, cycle-14 goal #2.
Supersedes `cockpit-staleness-monitor-verified-2026-11-23.md`, which was a **false closure**:
it claimed "Self-test ALL PASS" but the self-test was CWD-fragile and actually FAILED when run
from any directory other than the repo root.

## Defect caught (reproduced)
The prior leaf's reproduction command `python memory/verifier/cockpit_staleness_monitor.py`
worked only from the repo root because `FEED_FILE`/`ALERT_DIR` were **CWD-relative** strings.
Running the self-test from `memory/verifier/` (a plausible CWD for a scheduled task) made T1 and
T2 fail with `FEED FILE NOT FOUND: memory/ops/cockpit-feed.json` (it resolved to
`memory/verifier/memory/ops/...`). A *continuous* monitor launched with an arbitrary CWD would
therefore silently report false-stale. Reproduced 2026-11-24:
```
cd memory\verifier && python cockpit_staleness_monitor.py --self-test
[TEST 1] fresh=False  Evidence: FEED FILE NOT FOUND ...
=== SELF-TEST RESULT: FAIL ===   (T1 FAIL, T2 FAIL, T3 PASS)
```

## Fix
Anchored all paths to the repo root via `__file__` so the monitor is CWD-independent:
```
REPO_ROOT = Path(__file__).resolve().parent.parent.parent   # .../memory/verifier/file.py -> root
FEED_FILE = REPO_ROOT / "memory" / "ops" / "cockpit-feed.json"
ALERT_DIR = REPO_ROOT / "memory" / "verifier"
```
Note: first attempt used `.parent.parent` (off-by-one -> `<root>/memory`, still broken); corrected
to three parents. Verified `FEED_FILE.exists() == True` before re-testing.

## Reproduction (2026-11-24, after fix)
| Check | Command | Result |
|-------|---------|--------|
| Self-test from repo root | `python memory/verifier/cockpit_staleness_monitor.py --self-test` | **ALL PASS** (T1 fresh, T2 stale+alert, T3 missing-file path) |
| Self-test from memory/verifier | `cd memory\verifier && python cockpit_staleness_monitor.py --self-test` | **ALL PASS** (proves CWD-independence) |
| Live STALE run | `python ... --threshold 5` | `STALE age=591.5min >= 5min`, alert leaf written, exit **>=1** (via runtime `if errorlevel 1`) |
| Fresh run | `python ... --threshold 99999` | `FRESH age=591.5min < 99999min`, exit **0** |

## Acceptance criteria
- Continuous check that /api/fleet/cockpit data is <5min fresh: YES — checks both file mtime and
  internal `ts` (most conservative = max), threshold configurable via `--threshold`.
- Alert leaf on breach: YES — writes `memory/verifier/cockpit-stale-alert-YYYY-MM-DD.md` with a
diagnosis path (collector liveness, portal log, restart command).
- Self-test proves pass AND fail branches + missing-file path: YES — T1/T2/T3, now CWD-independent.
- Exit codes 0=fresh / 1=stale: YES — confirmed via runtime `if errorlevel` check (parse-time
  `%errorlevel%` expansion in cmd is unreliable; do not trust it for exit-code evidence).

## Live operational finding (not a monitor bug)
The feed the monitor watches, `memory/ops/cockpit-feed.json`, is **genuinely stale**: internal ts
= 2026-11-23T05:07Z (~591 min old at check time). The fleet collector that writes it has stopped.
This is the correct STALE verdict, not a false positive. Hand off to Mechanic (collector liveness).

## Artifacts
- Script: `memory/verifier/cockpit_staleness_monitor.py` (paths now anchored to repo root)
- This leaf: `memory/verifier/cockpit-staleness-monitor-cwd-fix-2026-11-24.md`
