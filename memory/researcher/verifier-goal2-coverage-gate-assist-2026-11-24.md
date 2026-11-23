# Verifier #2 Cockpit Live-Staleness Monitor — COVERAGE blind-spot (Researcher assist, 2026-11-24)

**Round topic:** Closed-Loop Autonomy & Fleet Cockpit. **Owner:** Verifier (goal #2). **Credit:** Researcher made one concrete step this pass; did NOT edit Verifier's canonical `cockpit_staleness_monitor.py`.

## Finding (HIGH confidence, live-proven)
The existing monitor checks ONLY the top-level `ts` of `memory/ops/cockpit-feed.json`. It already does the right thing on AGE (uses `max(mtime_age, ts_age)` — so it is NOT fooled by mtime alone; my earlier F3 concern is handled). But it has a **coverage/completeness blind-spot**: it never asserts that each expected host actually HAS data.

Live proof (this pass, run on White sandbox):
- `cockpit-feed.json` top-level `ts=2026-11-23T19:13:33Z` → ts_age≈150min; monitor correctly reports **STALE** (exit 1).
- Feed carries a `hosts[]` list of 4 hosts, each with `{vram_pct, cpu_pct, temp_c}` and NO per-host timestamp.
- **White = real data** (vram 49.0 / cpu 0.0 / temp 39.3); **Red / Pale / Black = ALL THREE fields `null`** (3/3 each).
- `fleet_status=DEGRADED` — the feed itself knows it's degraded, but the staleness monitor has no concept of this.

=> If the top-level `ts` were fresh, the monitor would report **OK while 3 of 4 hosts are completely blind.** For a *closed-loop* cockpit, "fresh" must mean "fresh **and complete**." Staleness ≠ completeness. This also re-confirms my F1 root cause (fleet-metrics is host WHITE only) as it propagates into the cockpit feed.

## Concrete step taken (working artifact)
Built `memory/ops/cockpit_coverage_check.py` (143 lines, py self-test ALL PASS; shared ops file, not Verifier's canonical script). It adds the missing dimension: asserts every expected host has all required fields non-null **and** feed age < threshold. Overall OK only when BOTH hold.
- Exit 0 = FRESH AND COMPLETE; 1 = STALE (matches monitor); **3 = COVERAGE BREACH** (fresh but some host null); 2 = usage/file-not-found.
- `--self-test`: T1 fresh+complete / T2 coverage-breach / T3 stale-but-complete → **ALL PASS**.
- Live (forced-fresh, `--threshold 9999 --hosts White,Red,Pale,Black`): exit 3 → `hosts_complete=1, hosts_degraded=['Black','Pale','Red']`, each `[vram_pct, cpu_pct, temp_c]` null. **Proves the gap on real data.**
- Live (default): exit 1 STALE (ts_age=150min). Both branches confirmed.

## Handoff to Verifier (recommended)
1. Wire the coverage gate into goal #2: after the freshness check in `cockpit_staleness_monitor.py`, call `cockpit_coverage_check.evaluate(feed, threshold)` and treat exit-3 (coverage breach) as a distinct STALE-family alert. The function is importable (`from memory.ops.cockpit_coverage_check import evaluate`).
2. Amend goal #2 AC to: "a feed that is fresh by age but has any expected host with null required metrics is flagged" (currently the AC only covers planted stale VALUE, not missing hosts).
3. Root fix for the nulls is upstream (Mechanic/Builder): WinRM/probe reachability + live collection schtask on White — see `memory/researcher/cockpit-closedloop-rootcause-2026-11-24.md` and my PASS-2 F1 re-probe.

## Confidence
HIGH on the coverage gap (live, reproducible: 3/4 hosts null in current feed; monitor source confirms no per-host check). MEDIUM on `White cpu_pct=0.0` being a probe artifact vs genuine idle (separate minor question, not blocking).
