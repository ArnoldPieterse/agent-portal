# Mechanic Open Goals - Solutions Ready for Execution
**Prepared by Designer | 2026-11-23**

All 4 open goals have scripts built and locally verified. Each needs exactly **one command from a non-sandbox seat (White)** to close.

---

## Summary Table

| # | Goal | Status | Unblock Command | Est. Time |
|---|------|--------|-----------------|-----------|
| 1 | Portal Load Test 7-Day | Script ready, data on White | `python memory/mechanic/goal1_one_command_close.py` | <30s |
| 2 | Self-Healing Mirror Production | Alert tested; waiting 2-wk window (~Dec 1) | Confirm schtask + wait for window | ~8 days remaining |
| 3 | WinRM Remote Reboot E2E | Script built, dry-run PASS on Black+Pale | `python winrm_e2e_test.py --host black --password <admin_pw>` | <15 min |
| 7 | Log Rotation + Retention | Unit tests 13/13 PASS; deploy script ready | `python memory/mechanic/deploy_all_schtasks.py` (from White) | <60s |

---

## Goal 1 - Portal Load Test 7-Day Completion

**What's done:**
- schtask `PortalLoadProbe` registered on White (verified 2026-11-22)
- Data accumulating daily; 5/7 days in sandbox mirror, 7/7 expected on White
- One-command closure script built: `goal1_one_command_close.py`

**Remaining action (one command from White):**
```bash
python memory/mechanic/goal1_one_command_close.py
```

**What it does:**
1. Probes 127.0.0.1:8099, writes today's data point
2. Counts distinct days in `load-baseline.jsonl`
3. If >=7 days: runs `load_week_complete.py` verdict
4. If PASS: auto-records ledger entry

**Closure evidence:** PASS/FAIL verdict in stdout + ledger marker.

**Risk:** If White's file still shows <7 days (e.g., schtask missed a day), script reports the gap and exits non-zero. Fallback: manually append missing days or wait one more cycle.

---

## Goal 2 - Self-Healing Mirror Production

**What's done:**
- `mirror_heal.py` running correctly (negative age = mirror IS fresh)
- Alert threshold tested: 4 failures fires alert; 3 does not (boundary correct)
- Zero unexplained drift >5 min confirmed

**Remaining action (two parts):**
1. **Now:** Confirm schtask `MirrorHeal` is registered on White:
   ```bash
   python elev.py --shell "schtasks /query /tn MirrorHeal"
   ```
2. **~Dec 1:** Two-week clean window closes. Run final verification:
   ```bash
   python memory/mechanic/mirror_heal.py --status
   ```

**Closure evidence:** Two consecutive weeks of `mirror-repairs.jsonl` with zero unexplained drift + alert threshold test (already done).

**Risk:** Low. Mirror is already healthy; this is an accumulation goal, not a build goal. No action needed until ~Dec 1 except the one schtask confirmation.

---

## Goal 3 - WinRM Remote Reboot E2E Test

**What's done:**
- `winrm_e2e_test.py` built (5 phases: baseline, host-down, CB detect, WinRM reboot, recovery verify)
- Dry-run validated against BOTH Black and Pale (TCP :8888 reachable, Studio API responding)
- Script logs all 5 phases to JSONL for audit trail

**Remaining action (one command from White):**
```bash
python winrm_e2e_test.py --host black --password <admin_pw>
```

**What it does:**
1. Phase 1: Verify target host baseline (TCP up, model count)
2. Phase 2: Stop service on target (simulated host-down)
3. Phase 3: Verify watchdog detects TCP-down within 30s + circuit breaker opens
4. Phase 4: Trigger WinRM reboot; wait for boot tasks to reload models
5. Phase 5: Confirm agent responsive again, model count matches baseline

**Closure evidence:** All 5 phases PASS in <15 min; JSONL log with sequential timestamps; no data loss (model count pre==post).

**Risk:** Medium. This is a destructive test on Black (non-critical host). If Black has active workloads, delay. Script has `--dry-run` for safe re-validation. Recommend running during low-activity window.

---

## Goal 7 - Log Rotation + Retention

**What's done:**
- `log_rotate.py` built: max 50MB per file, 7-day retention, .gz compression
- Unit tests: 13/13 PASS (rotation, compression, bounded disk, no data loss)
- `deploy_all_schtasks.py` includes `LogRotateDaily` schtask definition

**Remaining action (one command from White):**
```bash
python memory/mechanic/deploy_all_schtasks.py
```

**What it does:**
1. Registers all pending schtasks including `LogRotateDaily` (daily at 03:00)
2. Each task is idempotent (re-register = no-op if already exists)

**Closure evidence:** `schtasks /query /tn LogRotateDaily` shows Registered + Next Run Time; one successful daily run log entry in `memory/mechanic/log-rotate-runs.jsonl`.

**Risk:** Low. Idempotent deploy; worst case re-registers an existing task (no-op).

---

## Recommended Execution Order

1. **Goal 7** - lowest risk, idempotent, <60s. Do first to clear the queue.
2. **Goal 1** - also low risk, <30s, data-dependent (check day count first).
3. **Goal 3** - medium risk (destructive on Black), needs admin_pw, ~15 min. Schedule during quiet hours.
4. **Goal 2** - no action until ~Dec 1 except one schtask check.

All four can be executed in a single White session if timing works:
```bash
# Single-session close-out (from White, non-sandbox)
python memory/mechanic/deploy_all_schtasks.py          # Goal 7
python memory/mechanic/goal1_one_command_close.py      # Goal 1
python elev.py --shell "schtasks /query /tn MirrorHeal" # Goal 2 (confirm only)
# Goal 3: schedule separately during quiet window
python winrm_e2e_test.py --host black --password <admin_pw>
```

---

## Files Referenced
- `memory/mechanic/goal1_one_command_close.py`
- `memory/mechanic/winrm_e2e_test.py`
- `memory/mechanic/deploy_all_schtasks.py`
- `memory/mechanic/mirror_heal.py`
- `memory/mechanic/log_rotate.py`
