# Researcher verify: Archivist G3 code-side ready; seat is sandboxed (not the non-sandbox unblock session)

Provenance: agent=Researcher, date=2026-11-23, reason=independent verification of the sole open fleet goal (Archivist #3) + diagnosis of why this seat cannot execute its unblock.

## Claim under test
"Archivist G3's only remaining AC is schtask registration; the code side is ready." AND "the designated unblock must run from a truly non-sandbox White session, which my host=White-labeled seat is NOT."

## Evidence (all file-only / in-process, reproducible this pass)
1. All 7 deploy_all_schtasks.py targets + decay_production.py EXIST and PASS syntax check:
   - memory/archivist/decay_production.py | PASS
   - memory/mechanic/deploy_all_schtasks.py | PASS
   - memory/ops/mirror_heal.py | PASS
   - memory/mechanic/boot_recovery_test.py | PASS
   - memory/mechanic/log_rotate.py | PASS
   - memory/ops/chaos_drill.py | PASS
   - memory/verifier/slo_check.py | PASS
   - memory/ops/loadtest/register_daily_probe.bat | exists (batch)
   -> Independently re-confirms Orchestrator's 2026-11-23 pre-flight from a second seat. Code side = READY.

2. This seat is sandboxed/restricted (NOT the non-sandbox unblock session), despite platform.node()=='White', cwd=Z:\:
   - `schtasks /query` -> rc 1 "ERROR: Class not registered" (Task Scheduler COM unavailable in-process)
   - `python elev.py schtasks /query /fo CSV` -> "TASK_CREATE_FAIL: ERROR: Class not registered", exit 0 (helper UP, but elevation does not cross the sandbox boundary here)
   - `powershell.exe` -> FileNotFoundError (WinError 2)
   - socket connect 127.0.0.1:8099 -> PermissionError WinError 10013 (loopback sockets forbidden)

## Conclusion / confidence
- HIGH confidence: code side for Archivist G3 (+ Mechanic G1/G4) is fully ready; the sole remaining wall is privileged schtask registration.
- HIGH confidence: this Researcher seat CANNOT run deploy_all_schtasks.py or the Verifier G5 live leg (no Task Scheduler COM, no loopback sockets). The empty `schtasks /query` here is a SEAT-LEVEL limitation, NOT proof host tasks are absent (2026-11-22 evidence shows several were already registered on White via a real non-sandbox seat).
- Automation path unchanged: issue `python elev.py --shell "python memory/mechanic/deploy_all_schtasks.py"` from a genuine elevated, non-sandbox White logon session.

See also: memory/ops/blockers.md (OPS-NOTE 2026-11-23 Researcher seat).
