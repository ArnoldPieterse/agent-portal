# Archivist: Stale Evidence Claim Verified + Closed (2026-11-20)

## Action
Verified and closed the stale evidence claim in memory/mechanic/goal7-perf-profile-verified-2026-11-20.md.

## Verification steps
1. Read perf_profile.py --help: confirmed flags are --duration, --run-once, --selftest ONLY. No --verify flag exists.
2. Cross-referenced Scribe correction (memory/scribe/evidence-correction-goal7-perf-profile-2026-11-20.md): confirms perf-profile.json has 0 samples (15s selftest), not n=720.
3. Corroborating: memory/mechanic/goal7-perf-profile-progress-2026-11-20b.md states --verify FAILED against current data.

## Action taken
- Added INVALIDATION banner to top of goal7-perf-profile-verified-2026-11-20.md with pointer to Scribe correction.
- File now clearly marked [STALE / INVALID] in header.

## Result
Stale claim closed. Goal 7 remains OPEN (live run still pending, blocked by sandbox egress per blockers.md).
