# Mechanic auto-loop pass 2026-11-20c (~11:3x)

**Step taken (non-blocked, ledger upkeep):** reconciled an over-claimed evidence marker on Goal #7 Performance Profiling.

**What was wrong:** `memory/goals/mechanic.md` line 7 carried `(verified: ... selftest PASS ... live 1h run pending)`. goal_ledger.py's closure regex (line 50) counts ANY `(verified:` parenthetical as "reached" with no acceptance-test gate, so #7 was counted reached on selftest alone even though its acceptance test (live p50/p95/p99 with real samples) had NOT passed — perf-profile.json from the last 10s run = 0 samples.

**Fix:** rewrote the marker to `(PARTIAL 2026-11-20: selftest PASS only ... LIVE 1h run BLOCKED by sandbox :8099 egress wall, see memory/ops/blockers.md NEEDS-HUMAN; acceptance p50/p95/p99 with real samples NOT yet met)`. No `(verified:` / `— recorded` token, so the ledger no longer counts it as reached.

**Result (re-ran goal_ledger.py):** mechanic 9/10 open=1 -> **8/10 open=2** (#1 WinRM + #7 perf). Fleet 66/80 -> **65/80**. Now matches the auto-loop prompt's own "mechanic.md, 2 open" count.

**NOT re-probed:** both live legs already recorded NEEDS-HUMAN in memory/ops/blockers.md (WinRM #1 lines 6-12; perf #7 :8099 egress lines 137-141). elev.py absent at this sandbox seat (dir /s /b elev.py = none). Per anti-loop rule, no re-probe.

**Runbook note:** a `(verified:` marker must only be written when the goal's ACCEPTANCE test has actually run and passed — selftest-only work belongs in a PARTIAL/progress note, not a verified marker, or it silently inflates the fleet % via goal_ledger.py's regex.