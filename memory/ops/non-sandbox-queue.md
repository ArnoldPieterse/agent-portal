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

## OPEN (batch in one sitting)
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
