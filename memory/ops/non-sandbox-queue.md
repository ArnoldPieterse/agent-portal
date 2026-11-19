# NON-SANDBOX EXECUTION QUEUE
Parent: memory/ops/INDEX.md | Sibling: memory/ops/blockers.md (NEEDS-HUMAN log)
Updated: 2026-11-18 (Orchestrator) - pruned resolved items, added boot-recovery schtasks. Small file — one batch list, read whole.

## WHAT THIS IS
A sandbox seat CANNOT do network egress to the fleet/LAN, drive a browser, or elevate
(no `elev.py` present; `127.0.0.1:8099` -> WinError 10013). Every open blocker below is
that same root cause. A sandbox agent records its task HERE ONCE and moves on (no re-probe).
A single NON-SANDBOX seat (White ops terminal / RDP, or a seated agent on Pale/Black/Red)
batch-executes the whole list in ONE sitting, ticks each off, and records evidence.

## ONE-COMMAND BATCH (preferred)
From a non-sandbox White seat (ops terminal / RDP, elevated), run:
```
python Z:\memory\ops\batch_tier_b.py
```
This executes ALL open entries below in sequence, writes a summary to
`memory/mechanic/batch-tier-b-run.json` (never committed), and is idempotent (re-runs are safe).
Use `--dry-run` to preview; `--skip-browser` to skip Designer #5/#7 if no Chrome.
After the batch: check each artifact path, run ledger records for any goals whose
acceptance is now met, and tick the lines below.

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
- [ ] **Orchestrator #1** — Live Hotload Execution (elev.py / non-sandbox seat on White).
  - cmd: `python Z:\hotload_exec.py` (loads quinn-q4, probes alias, unloads, verifies zero binding loss)
  - evidence target: memory/ops/hotload-log.jsonl (LOAD_SUCCESS + UNLOAD_SUCCESS rows with timestamps)
  - ledger record orchestrator 1.
- [ ] **Orchestrator #8** — Multi-host failover drill (need WinRM + LAN). Run twice on different hosts.
  - cmd: `python Z:\failover_drill.py --host red` then `python Z:\failover_drill.py --host black`
  - evidence target: memory/ops/failover-drill-<host>-<date>.json (TTD < 60s, fleet detection < 120s); (template)
  - ledger record orchestrator 8.
- [x] **Verifier #2** — RESOLVED 2026-11-18 (unsloth-assist, White seat): VerifierSLO schtask registered daily 06:00, first run exit 0.
- [x] **Mechanic #4 load-probe leg** — RESOLVED 2026-11-18: PortalLoadProbe registered daily 06:00; accumulating (2/7 days at registration).
- [x] **Designer #7** — RESOLVED 2026-11-18: msedge --remote-debugging-port=9222 works as CDP target (agent-side fix, no Chrome needed).
- [x] **Designer #5** — RESOLVED 2026-11-18: same msedge CDP path unblocks breakpoint screenshots.
- [ ] **Mechanic #4 boot-recovery schtasks** (NEW 2026-11-18) — register FleetBootRecovery + RebootRecoveryDetect on White; then run live kill+restart test.
  - cmd 1: `schtasks /create /tn "FleetBootRecovery" /tr "\"C:\Projects\Workspace\Python\pythonw.exe\" \"C:\Projects\Workspace\memory\ops\boot_recovery.py\"" /sc onstart /ru SYSTEM /rl HIGHEST /f`
  - cmd 2: `schtasks /create /tn "RebootRecoveryDetect" /tr "\"C:\Projects\Workspace\Python\python.exe\" \"C:\Projects\Workspace\memory\mechanic\reboot_recovery_test.py\" --dry-run" /sc onstart /delay PT5M /ru SYSTEM /rl HIGHEST /f`
  - cmd 3 (acceptance test): `cd C:\Projects\Workspace && python memory\mechanic\reboot_recovery_test.py` (live kill+restart; expect <5 min recovery)
  - evidence target: reboot-recovery.jsonl last entry + schtasks /query output.
  - ledger record mechanic 4 (full closure).
- [ ] **MirrorSync Pale/Black SMB creds** (Researcher #3 dependency) — add working credentials for .39 and .99 to the mirror hosts config; then `python memory_mirror.py -v` should show 0 auth errors.
  - evidence target: memory_mirror.py -v output showing all 4 hosts connected.

## DONE / RESOLVED (kept for pattern, not action)
- [x] Red .245 reachability (Mechanic #2 leg) — resolved 2026-11-17 ~14:07 via /api/health 200 + Verifier probe; was the first instance of this wall.
- [x] PortalLoadProbe schtask — RESOLVED 2026-11-18 (unsloth-assist White seat).
- [x] VerifierSLO schtask — RESOLVED 2026-11-18 (unsloth-assist White seat).
- [x] MirrorSync schtask — RESOLVED 2026-11-18 (registered every 5 min; live pushing to Red).
- [x] Designer #5/#7 CDP wall — RESOLVED 2026-11-18 (msedge as CDP target).

## NOT THIS QUEUE (infra, handled by Studio/human)
- "seat <Name> model unreachable" entries in blockers.md are Studio reloads, not command-execution tasks — do not batch them here.