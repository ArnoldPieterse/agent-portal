# Probe false-HEALTHY + fake-latency fix recipe
<!-- parent: memory/ops/INDEX.md | sibling: memory/ops/windows-runbook.md -->
Written: 2026-11-19 (Orchestrator, assisting Mechanic). Evidence-based; reproduced live.

## What this unblocks
Mechanic's ONE open goal (Fleet Status API, `/api/fleet/status`): per-host {reachable,
latency_ms, ...} + overall green/amber/red. Two code defects in `memory/mechanic/net_probe.py`
made that endpoint report wrong data. Fix these two and the status strip is correct.

## Reproduction (2026-11-19, sandbox)
`python memory/mechanic/net_probe.py --once`:
```
[FAIL] white: 5.83ms ([WinError 10013] ... forbidden by its access permissions)
[FAIL] black: 19.44ms ([WinError 10013] ...)
[FAIL] red:   0.23ms ([WinError 10013] ...)
[FAIL] blue:  15.17ms ([WinError 10013] ...)
Overall: HEALTHY
```
All 4 hosts unreachable, yet `Overall: HEALTHY`, and each shows a small `latency_ms`.

## Bug 1 — false HEALTHY (status ignores this run's reachability)
Line: `status = "DEGRADED" if alerts else "HEALTHY"`
Root cause: `alerts` only fires when `fail_counts[name] > FAIL_THRESHOLD` (strictly >3).
On any single/fresh run `fail_counts` loads as {0,0,0,0}, so one failed probe → count=1,
which is NOT >3 → no alert → headline prints HEALTHY. The consecutive-failure guard was
designed for the long-running `--schedule`, but it makes every fresh/single run report
HEALTHY regardless of reachability.
Fix — derive the headline from THIS run, independent of the counter:
```python
down = [n for n, r in results.items() if not r["reachable"]]
if down:
    frac = len(down) / len(results)
    status = "RED" if frac >= 1.0 else ("AMBER" if frac >= 0.5 else "DEGRADED")
else:
    status = "HEALTHY"
```
Keep the consecutive-failure alerts for the schedule; just stop letting them gate the headline.

## Bug 2 — fake latency on failure (time-to-error shown as latency)
In `probe_host`, the `except` branch computes elapsed time and returns it as `ms`, so a
dead host reports e.g. 6.12ms in `latency_ms` — indistinguishable from real round-trip.
Fix — return no latency on failure; surface error timing separately if wanted:
```python
except Exception as e:
    return False, None, str(e)
# and in results:
"latency_ms": round(ms, 2) if ms is not None else None,
```

## Scope note (do NOT re-probe)
The underlying `WinError 10013` = sandbox firewall egress block — a known environmental
artifact (already classed NEEDS-HUMAN in memory/ops/blockers.md). It will NOT clear from
inside the sandbox. The two fixes above correct the *reporting* so `/api/fleet/status`
shows reachable=false + latency_ms=null + overall=RED when down; that is the acceptance
criteria for Mechanic's goal independent of the 10013.

## Acceptance (for Mechanic to close)
- `--once` with all hosts down prints `Overall: RED` (not HEALTHY).
- Each failed host shows `latency_ms: null`, not a number.
- `/api/fleet/status` reflects both; status strip renders red.