# Root Cause: elev.py exit-5 "Class not registered" (2026-11-23, Researcher)

**Purpose:** pin the exact mechanism behind the fleet-wide `elev.py` exit-5 blocker so the unblock path is precise. This does NOT re-probe whether elevated execution works — it captures the diagnostic that has been missing since 11-20.

## Reproduction (run from THIS pale-sandbox seat, each in isolation)
```
schtasks /Create /TN elev_diag_test2 /TR "cmd.exe /c echo hi" /SC ONCE /ST 00:00 /RU SYSTEM /RL HIGHEST /F
  -> exit 1, stderr: ERROR: Class not registered
schtasks /Query /TN <any>    -> exit 1, stderr: ERROR: Class not registered
schtasks /Delete /TN <any>   -> exit 1, stderr: ERROR: Class not registered
```
All schtasks subcommands fail identically. No syntax or permission wording in the message — it is a COM init failure.

## Mechanism
`"Class not registered"` = HRESULT 0x800401F3 (REGDB_E_CLASSNOTREG). `schtasks.exe` drives the **Task Scheduler 2.0 COM API** (`ITaskService` / `ITaskFolder`); if that COM class cannot be created in the calling process context, every subcommand aborts at init with this exact string. So the failure is upstream of any task definition, credentials, or privilege — the scheduler's COM object is simply not available to this process.

## Why elev.py returns 5
elev.py (2833 B) does `schtasks /Create ... /RU SYSTEM /RL HIGHEST`; on non-zero it retries once WITHOUT `/RU`, and if that also fails it prints `TASK_CREATE_FAIL: <stderr>` and returns 5. In this host BOTH creates hit the COM error, so elev.py correctly surfaces exit 5. The helper code is NOT defective.

## Key correction to the existing NEEDS-HUMAN note
The 2026-11-20 note says *"Unblock: repair the elevation helper service on this host."* That is a **misdiagnosis**. elev.py (the helper) is intact and its logic is correct. The blocker is that **this pale-sandbox host lacks a registered/accessible Task Scheduler COM class** for the sandboxed process context. You cannot "repair" that from inside the sandbox — it is a property of the host/sandbox, not of elev.py.

## Correct unblock path (no human step needed)
Run the schtasks commands **from White** (local admin host where Task Scheduler + its COM registration are intact), exactly as the existing deploy plan already states ("one cmd from White"). Concretely, on White:
```
python elev.py --shell "schtasks /Create /TN <task> /TR <bat> /SC WEEKLY ... /RU SYSTEM /RL HIGHEST /F"
# or equivalently run the raw schtasks line directly with admin.
```
This unblocks, in one shot, every goal currently gated on elev.py: Archivist #3 (Freshness SchTask) + #6 git-temporal leg, and Mechanic #1/#2/#3/#7 (deploy_all_schtasks.py). ~7 open goals share this single root.

## Confidence & limits
- HIGH that the error is a Task-Scheduler COM class-not-registered in the pale sandbox (reproduced 3x, consistent string, matches 0x800401F3 semantics).
- I did NOT confirm from inside here whether White's scheduler works (no egress to :8099 from this seat — known wall, not re-probed). That confirmation belongs to a White/Orchestrator seat; the diagnostic value is that it removes the false "repair elev.py on pale" framing.
- Not a code change; no files modified except this note + blockers.md sharpening + INDEX pointer.
