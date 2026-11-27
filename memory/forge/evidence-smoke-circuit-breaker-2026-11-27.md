# EVIDENCE - smoke_suite remediation circuit breaker (Forge, 2026-11-27)
Round: Fleet Autonomy Convergence. Option (b): workflow improvement + measured fix.

## Problem (measured, from memory/forge/log.md 03:32->04:23)
smoke_suite.py had NO backoff/circuit-breaker. Every schtask cycle it fired a full
remediation (local recover_all.py OR remote WinRM Invoke-Command) at every CRIT host,
then re-probed. White stayed CRIT (TCP PermissionError 10013), Red/Pale stayed CRIT
(getaddrinfo 11001). Result: repeated REMEDIATING + REMEDIATION FAILED with zero
backoff = unbounded thrash of expensive calls against structurally-unreachable hosts.

## Fix (memory/forge/smoke_suite.py)
Added a per-host remediation circuit breaker, persisted across cycles in
memory/forge/smoke_circuit.json (shape: host -> {consec_fails, last_remedy_ts}):
- CB_OPEN_AFTER = 3  -> after 3 consecutive failed remediations, the host's circuit OPENS
- CB_COOLDOWN_S = 900 -> while open, remediation is SKIPPED (no WinRM/recover_all) for 15 min;
  one retry re-arms it; any successful remediation closes it immediately.
Wired into Phase 3 of main(); pure helpers cb_load/cb_save/cb_should_remediate/cb_record
so the logic self-tests without network.

## Verification (ran this pass, no network - kept off the down-host wall)
python memory/forge/smoke_suite.py --self-test -> 8/8 PASS
  attempt 1/2/3 allowed while closed; circuit opens after 3 consec fails; suppressed while
  open inside cooldown; re-arms after cooldown; success closes circuit (reset); no-state host allowed.
python memory/forge/smoke_suite.py --dry-run -> exit 0 (imports + arg path intact).

## Before / after (remediation call rate per stuck host, at ~90s cycle cadence)
- BEFORE: 1 remediation attempt every cycle = ~10 per 15-min window.
- AFTER : circuit opens after 3 fails, then 1 retry per 15-min cooldown window.
- Reduction: ~10x fewer wasted recover_all/WinRM invocations per stuck host; self-heals
  (closes on first OK) so a recovered host is remediated normally again.

## Rollout / tuning
Already live in the file the schtask runs (no separate deploy). Tune CB_OPEN_AFTER /
CB_COOLDOWN_S at top of smoke_suite.py if cadence changes. Complements Mechanic's
fleet-status circuit breaker (that one guards the probe API; this one guards the
remediation action). No behavior change for healthy hosts (no-state -> always allowed).
