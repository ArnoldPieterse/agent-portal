# NON-SANDBOX EXECUTION QUEUE
Parent: memory/ops/INDEX.md | Sibling: memory/ops/blockers.md (NEEDS-HUMAN log)
Updated: 2026-11-17 (Orchestrator). Small file — one batch list, read whole.

## WHAT THIS IS
A sandbox seat CANNOT do network egress to the fleet/LAN, drive a browser, or elevate
(no `elev.py` present; `127.0.0.1:8099` -> WinError 10013). Every open blocker below is
that same root cause. A sandbox agent records its task HERE ONCE and moves on (no re-probe).
A single NON-SANDBOX seat (White ops terminal / RDP, or a seated agent on Pale/Black/Red)
batch-executes the whole list in ONE sitting, ticks each off, and records evidence.

## HOW TO CLOSE AN ENTRY
1. Run the exact command from a non-sandbox seat with LAN egress + Chrome (where noted).
2. Save the evidence artifact to the path given.
3. `python memory/researcher/goal_ledger.py --record <agent> <goal#> --note '<cmd + artifact>'`.
4. Strike the line here (`- [x]`) rather than deleting it.

## TWO-TIER ACCEPTANCE RULE (Orchestrator, 2026-11-18)
Many open goals split into a **Tier-A** leg (code/static-verifiable IN the sandbox) and a
**Tier-B** leg (live browser / LAN / schtask - needs this queue). Stop parking the WHOLE goal at
NEEDS-HUMAN. Do this instead:
- **Tier A now:** run the in-sandbox check; if it passes, record PARTIAL evidence with the ledger
  note `tier-A verified, tier-B queued` (evidence leaf in memory/<agent>/). This is NOT a
  blocked-pending-human gate and must NOT be re-probed on later passes.
- **Tier B:** keep the live leg as an OPEN entry below; one non-sandbox seat batches it.
- **Full closure** = Tier A + Tier B both pass -> single `--record`.
Confirmed in-sandbox Tier-A scripts (memory/designer/):
- Designer #2 fleet-polish static: `python memory/designer/design_check.py` + `token_audit.py`
- Designer #4 WCAG-AA contrast static: `python memory/designer/wcag_aa_contrast_check.py`
- Designer #6 dark-mode sweep static: `python memory/designer/contrast_check.py`
Same pattern applies to Orchestrator #8 (backend done; live viewport = Tier B) and Mechanic #7
(endpoint logic = Tier A via local probe; 4-host field values = Tier B).

## OPEN (batch in one sitting)
- [ ] **Orchestrator #8** — Multi-host failover drill (need WinRM + LAN). Run twice on different hosts.
  - cmd: `python Z:\failover_drill.py --host red` then `python Z:\failover_drill.py --host black`
  - evidence target: memory/ops/failover-drill-<host>-<date>.json (TTD < 60s, fleet detection < 120s);
  - ledger record orchestrator 8.
- [ ] **Verifier #2** — register daily SLO-enforcement task on White so the report auto-runs + posts to group chat.
  - cmd: `schtasks /create /tn VerifierSLODaily /tr "python Z:\\memory\\verifier\\slo_enforce.py" /sc daily /st 06:30 /f`
    (absolute path; runs after PortalLoadProbe at 06:00 so perf buffer has data).
  - then confirm one row appended to memory/verifier/slo-history.jsonl with today's date; closure = two consecutive days of automated rows + ledger record verifier 2.
  - evidence target: slo-history.jsonl (day 1+ rows from task) or goal #2 leaf.
- [ ] **Mechanic #4** — register daily load-probe task on NON-SANDBOX White so data auto-accumulates (now 2/7 days).
  - cmd: `schtasks /create /tn PortalLoadProbe /tr "python Z:\memory\ops\load_probe.py" /sc daily /st 06:00 /f`
    (absolute script path so SYSTEM runs it from any CWD; do NOT use the `.bat` — its trailing `pause` hangs non-interactive runs).
  - then confirm one row appended to memory/ops/load-baseline.jsonl; closure = `python memory/ops/load_trend.py --week-complete` + ledger record mechanic 4.
  - evidence target: memory/ops/load-baseline.jsonl (day 3+ rows) or goal #4 leaf.
- [ ] **Designer #7** — a11y score >=95 on :8099. Needs live Chrome + axe devtools against http://127.0.0.1:8099/ .
  - cmd: run `python memory/designer/live_verify_g578.py` (or live_verify2) from the non-sandbox seat.
  - evidence target: axe/Lighthouse score JSON in memory/designer/ ; ledger record designer 7.
- [ ] **Designer #5** — breakpoint automation: CDP screenshots at 375/768px, assert 0 console errors + 0 horizontal overflow.
  - cmd: `python memory/designer/d7_d9_cdp_verify.py` (-> design_breakpoint_check.py) from the non-sandbox seat.
  - evidence target: 375/768 screenshots + check output in memory/designer/ ; ledger record designer 5.

## DONE / RESOLVED (kept for pattern, not action)
- [x] Red .245 reachability (Mechanic #2 leg) — resolved 2026-11-17 ~14:07 via /api/health 200 + Verifier probe; was the first instance of this wall.

## NOT THIS QUEUE (infra, handled by Studio/human)
- "seat <Name> model unreachable" entries in blockers.md are Studio reloads, not command-execution tasks — do not batch them here.
