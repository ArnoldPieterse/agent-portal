# net_probe.py verdict fix (2026-11-19, Mechanic)

**What broke:** `run_check()` set `status = "DEGRADED" if alerts else "HEALTHY"` — the overall
verdict only reflected *sustained* failure alerts (`fail_counts > 3`). On a single fresh run where
ALL hosts are unreachable, `fail_counts` is still 1 each → no alert → it printed `Overall: HEALTHY`
while every host line said `[FAIL]`. Also `probe_host()` returned time-to-error as `latency_ms`, so a
dead host displayed a fake RTT (e.g. `6.12ms`).

**What fixed it:**
1. `probe_host()` now returns `ms=None` on the exception path (no real RTT for a failed probe).
2. Verdict derived from current reachability: `CRITICAL` if 0/4 reachable, `DEGRADED` if any host
   down OR sustained/p95 alerts, else `HEALTHY`. Failed lines print `unreachable`, not a fake ms.

**Evidence (this seat = Red sandbox, egress blocked → WinError 10013 on all hosts):**
- Before: `[FAIL] white: 6.12ms (...)` ... `Overall: HEALTHY`
- After:  `[FAIL] white: unreachable (...)` x4 ... `Overall: CRITICAL`

Note: the per-host FAILs here are the *known* sandbox egress block (see memory/ops/blockers.md,
WinError 10013 class) — NOT a real fleet outage. On White (where the portal + LAN live) the same
fix yields `HEALTHY` when hosts answer and correctly escalates to DEGRADED/CRITICAL on real loss.

Runbook one-liner: net_probe overall verdict ignored current reachability → all-down read as
HEALTHY; now verdict = f(reachable_count, alerts): 0→CRITICAL, partial/alerts→DEGRADED, else HEALTHY.