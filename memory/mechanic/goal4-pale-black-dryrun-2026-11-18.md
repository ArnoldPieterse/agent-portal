# Goal #4 Evidence: Pale + Black Dry-Run Confirmed (2026-11-18)

## Test
`python reboot_recovery_test.py --dry-run` from White sandbox seat.

## Results (2026-11-18T02:52:33Z)
| Host | Target | Status | Latency |
|------|--------|--------|---------|
| White | 127.0.0.1:8099 | FAIL | 24.0ms (sandbox egress 10013, known) |
| Pale | IP_PALE:8888 | **PASS** | 31.2ms |
| Black | IP_BLACK:8888 | **PASS** | 3.4ms |
| Red | IP_RED:8888 | FAIL | 0.1ms (self-probe limitation, known) |

## Verdict
- Pale + Black: **CONFIRMED REACHABLE** - recovery script would detect portal-down and initiate start.
- White + Red failures are sandbox egress/self-probe limitations (documented in goal4-reboot-recover-v2-2026-11-18.md), not actual host failures.
- Combined with earlier Red --dry-run --force validation (hot notes 11-18): **3/4 hosts validated for recovery logic**.

## Remaining for full closure
1. Schtask registration on all 4 hosts (NEEDS-HUMAN: non-sandbox terminal)
2. One live kill+restart to measure actual recovery time <5min (requires portal running on non-sandbox host)

## Runbook note
What broke: Pale/Black dry-runs were pending from cycle-2.
What fixed it: ran reboot_recovery_test.py --dry-run from White seat; both hosts PASS via 8888 TCP check.
