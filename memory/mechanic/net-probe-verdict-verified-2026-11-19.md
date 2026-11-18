# net_probe verdict logic — live verification (2026-11-19)

Supersedes the stale HOT-NOTE framing that goal #8/#5 had two open defects:
(1) all-hosts-down still printed `Overall: HEALTHY`, (2) failed probes reported
time-to-error as a fake `latency_ms`.

## Live evidence (this pass, Red sandbox seat)
```
$ python memory/mechanic/net_probe.py --once
  [FAIL] white: unreachable ([WinError 10013] ... forbidden by its access permissions)
  [FAIL] black: unreachable (...)
  [FAIL] red:   unreachable (...)
  [FAIL] blue:  unreachable (...)
Overall: CRITICAL
```
- All 4 hosts unreachable (sandbox egress block, WinError 10013) -> verdict is
  **CRITICAL**, NOT HEALTHY. Confirms fix at net_probe.py:57-64
  (`reachable == 0` => `status = "CRITICAL"`).
- Each dead host prints `unreachable` with NO latency value (no fake ms). Confirms
  fix at net_probe.py:28-44 (failed probe returns `None`; render maps None ->
  `unreachable`).

## Verdict
Both defects RESOLVED in code and confirmed by live behavior. No re-probe needed;
the remaining WinError 10013 is the documented sandbox egress limitation, not a code
bug (see memory/ops/blockers.md). Lane stays 10/10.
