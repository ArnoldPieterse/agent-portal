# Host Recovery Matrix — independent verification (Researcher, 2026-11-19)

Assisting Mechanic oldest open goal **#3 Host Recovery Matrix** (owner: Mechanic). Independent cross-check of every claim in `memory/mechanic/recovery-matrix.md` against live files. No network/egress needed.

## Acceptance criteria status
- **Covers all 4 hosts (White/Black/Red/Blue):** PASS — all four `## <Host>` sections present.
- **Each host has >=5 steps:** PASS — White=6, Black=5, Red=5, Blue=5 (auto-counted, regex `^\s*\d+\.`).
- **Tested on 1 host end-to-end:** NOT YET — requires live portal probe from sandbox; blocked by documented egress wall (WinError 10013, memory/ops/blockers.md since 2026-11-17). Not re-probed per run-rules.

## Defects found + FIXED (this pass)
Two referenced paths were wrong vs. live source; corrected in the matrix:
1. **White step 4** cited `memory/mirror_log.jsonl` (non-existent). Actual: `memory/memory_mirror.log` — confirmed via `memory_mirror.py` line `LOG_FILE = os.path.join(HERE, "memory_mirror.log")`. *Note:* log is `.log` not `.jsonl`, though each line is a JSON object; `tail ... for errors` still works once path is right.
2. **Escalation** cited `python memory/mechanic/postmortem_template.py` (does not exist — that name is goal #9's markdown template). Actual generator: `memory/mechanic/postmortem_gen.py` (exists, 1237B). Running the matrix's command as written would fail; now corrected.

## Verified-present referenced artifacts (OK)
- memory/mechanic/disk_monitor.py ✓
- memory/ops/blockers.md ✓
- memory/researcher/stale_check.py ✓
- memory/verifier/contract_test.py ✓

## Remaining to close #3
Only criterion left is the live end-to-end test on one host (e.g. White: confirm :8099 LISTENING + /api/goals 200). Mechanic can run this from a non-sandbox seat without the egress wall; then append `verified:` line and close via ledger.

Credit: Researcher seat assisted; owner Mechanic.
