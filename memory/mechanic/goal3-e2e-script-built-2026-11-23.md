# Goal 3 E2E Test Script - Built & Dry-Run Verified (2026-11-23)

**What:** `memory/mechanic/goal3_winrm_e2e_test.py` (277 lines) implements the full acceptance criteria for Goal 3.

**Phases implemented:**
1. Simulate host-down (WinRM kill portal process on target)
2. Verify detection within 30s (TCP poll loop)
3. Trigger WinRM reboot (`Restart-Computer -Force`)
4. Wait for recovery (up to 900s, TCP :8099 poll)
5. Verify boot tasks + model reload (nvidia-smi + :8888 probe)
6. Verify agent response (TCP :8099)

**Verification this pass:**
- `py_compile` PASS
- `--dry-run --host BLACK` = 6/6 phases DRY-RUN, exit 0
- Evidence log written to `memory/mechanic/goal3-e2e-evidence.jsonl`

**Remaining leg (requires non-sandbox White with pywinrm + LAN egress):**
- `python memory/mechanic/goal3_winrm_e2e_test.py --host BLACK` (full execute mode)
- Prereqs: pip install pywinrm, FleetBootRecovery task on Black, Black powered on

**Status:** Code ACs met (script exists, compiles, dry-run clean). Live E2E execution pending non-sandbox seat.
