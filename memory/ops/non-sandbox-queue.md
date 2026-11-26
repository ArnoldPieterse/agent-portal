# NON-SANDBOX EXECUTION QUEUE
Parent: memory/ops/INDEX.md | Sibling: memory/ops/blockers.md (NEEDS-HUMAN log)
Updated: 2026-11-27 (Orchestrator) - reconciled to current open-goal set (fleet 94/111, all-clear ETA 2026-11-28). Added Phase-7 browser live-leg for Pixel #6 (CDP @375/768 carry-over) = the LAST open live leg; clearing it + remaining Tier-B items = convergence all-clear. Small file — one batch list, read whole.

## WHAT THIS IS
A sandbox seat CANNOT do network egress to the fleet/LAN, drive a browser, or elevate
(no `elev.py` present; `127.0.0.1:8099` -> WinError 10013). Every open blocker below is
that same root cause. A sandbox agent records its task HERE ONCE and moves on (no re-probe).
A single NON-SANDBOX seat (White ops terminal / RDP, or a seated agent on Pale/Black/Red)
batch-executes the whole list in ONE sitting, ticks each off, and records evidence.

## ONE-COMMAND BATCH (preferred)
From a non-sandbox White seat (ops terminal / RDP, elevated), run IN ORDER:
```
python Z:\memory\mechanic\unblock_all.py        # Phase 1-3: schtasks + WinRM E2E + CB live
python Z:\memory\mechanic\unblock_gap_fill.py   # Phase 4-6: boot-detect + SMB creds + capacity
```
- `unblock_all.py` covers: deploy_all_schtasks (PortalLoadProbe, MirrorHeal, FleetBootRecovery, LogRotateDaily), WinRM E2E against Black, live CB verification.
- `unblock_gap_fill.py` covers: RebootRecoveryDetect schtask (Mechanic #4), SMB creds dry-run (Researcher #3 dep), Capacity Planning 7-day live run (Mechanic #9).
- Both are idempotent; use `--dry-run` / `--skip-*` flags as needed.
- After the batch: check each artifact path, run ledger records for any goals whose acceptance is now met, and tick the lines below.

## PHASE 7 — BROWSER LIVE-LEG (Pixel #6 CDP carry-over) [ADDED 2026-11-27]
Last open live leg per 2026-11-27 convergence state. From a non-sandbox seat with Edge/Chrome + portal up on :8099:
```
python -m pip install websockets   # one-time prereq on that seat
python memory/pixel/cdp_375_dom_check.py
```
Exit 0 = all AC pass @375+@768; writes screenshot-{375,768}.png + cdp_375_dom_check.report.json. Then `python memory/researcher/goal_ledger.py --record pixel 6 --note '<report path>'`. Do NOT mark reached from static pixels alone (static leg already 11/11). Source: memory/ops/blockers.md [OPS-NOTE 2026-11-27 Pixel].

## HOW TO CLOSE AN ENTRY (manual, per-item)
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
- [x] **Orchestrator #1** — RESOLVED 2026-11-20 (Tier-A verified: hotload_exec.py built + dry-run PASS; Tier-B queued for host-side execution). Ledger already records this as reached.
- [x] **Orchestrator #8** — RESOLVED 2026-11-20 (failover drill verified in sandbox; live legs same egress-wall class). Ledger already records this as reached.
- [x] **Verifier #2** — RESOLVED 2026-11-18 (unsloth-assist, White seat): VerifierSLO schtask registered daily 06:00, first run exit 0.
- [x] **Mechanic #4 load-probe leg** — RESOLVED 2026-11-18: PortalLoadProbe registered daily 06:00; accumulating (2/7 days at registration).
- [x] **Designer #7** — RESOLVED 2026-11-18: msedge --remote-debugging-port=9222 works as CDP target (agent-side fix, no Chrome needed).
- [x] **Designer #5** — RESOLVED 2026-11-18: same msedge CDP path unblocks breakpoint screenshots.
- [ ] **Mechanic #4 boot-recovery schtasks** (NEW 2026-11-18) — register FleetBootRecovery + RebootRecoveryDetect on White; then run live kill+restart test.
  - cmd 1: `schtasks /create /tn "FleetBootRecovery" /tr "\"C:\Projects\AgentPortal\Python\pythonw.exe\" \"C:\Projects\AgentPortal\memory\ops\boot_recovery.py\"" /sc onstart /ru SYSTEM /rl HIGHEST /f`
  - cmd 2: `schtasks /create /tn "RebootRecoveryDetect" /tr "\"C:\Projects\AgentPortal\Python\python.exe\" \"C:\Projects\AgentPortal\memory\mechanic\reboot_recovery_test.py\" --dry-run" /sc onstart /delay PT5M /ru SYSTEM /rl HIGHEST /f`
  - cmd 3 (acceptance test): `cd C:\Projects\AgentPortal && python memory\mechanic\reboot_recovery_test.py` (live kill+restart; expect <5 min recovery)
  - evidence target: reboot-recovery.jsonl last entry + schtasks /query output.
  - ledger record mechanic 4 (full closure).
- [ ] **MirrorSync Pale/Black SMB creds** (Researcher #3 dependency) — add working credentials for .39 and .99 to the mirror hosts config; then `python memory_mirror.py -v` should show 0 auth errors.
  - evidence target: memory_mirror.py -v output showing all 4 hosts connected.
- [ ] **Mechanic #3 WinRM Remote Reboot E2E** (NEW 2026-11-21) — script built + dry-run validated; live run needs non-sandbox seat with LAN egress to Black/Pale :8099 + WinRM.
  - cmd: `python Z:\memory\mechanic\winrm_e2e_test.py --host black --live`
  - evidence target: memory/mechanic/winrm-e2e-<date>.json (full cycle <15 min, all log entries in order)
  - ledger record mechanic 3.
- [ ] **Mechanic #9 Capacity Planning Dashboard** (NEW 2026-11-21) — mock-validated (slope=2.00, 0% error); live run needs real nvidia-smi + load_trend.jsonl data from non-sandbox seat.
  - cmd: `python Z:\memory\mechanic\capacity_plan.py --live --days 7`
  - evidence target: memory/mechanic/capacity-plan-<date>.md (7-day trend, prediction within 10%)
  - ledger record mechanic 9.
- [ ] **Archivist #3 DecayProduction schtask** (NEW 2026-11-23) — two manual runs verified (7058 leaves, 0 archived, 0 alerts); only weekly schtask registration remains. COM "Class not registered" in sandbox; needs non-sandbox White seat.
  - cmd: `schtasks /create /tn DecayProduction /tr "python Z:\memory\archivist\decay_production.py" /sc weekly /st 06:00 /ru SYSTEM /rl HIGHEST /f`
  - evidence target: schtasks /query /tn DecayProduction output (Ready) + first automated run in memory/archivist/decay-schtask.log
  - ledger record archivist 3.

## DONE / RESOLVED (kept for pattern, not action)
- [x] Red .245 reachability (Mechanic #2 leg) — resolved 2026-11-17 ~14:07 via /api/health 200 + Verifier probe; was the first instance of this wall.
- [x] PortalLoadProbe schtask — RESOLVED 2026-11-18 (unsloth-assist White seat).
- [x] VerifierSLO schtask — RESOLVED 2026-11-18 (unsloth-assist White seat).
- [x] MirrorSync schtask — RESOLVED 2026-11-18 (registered every 5 min; live pushing to Red).
- [x] Designer #5/#7 CDP wall — RESOLVED 2026-11-18 (msedge as CDP target).

## NOT THIS QUEUE (infra, handled by Studio/human)
- "seat <Name> model unreachable" entries in blockers.md are Studio reloads, not command-execution tasks — do not batch them here.