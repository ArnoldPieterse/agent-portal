# Lv 3 stuck >1h + residual popups — root cause & fix (2026-11-23)

## Symptom
Dashboard: 74/82 (90.2%), Lv 3 chip, no progress for >1h. User also reported scheduled-task
popups still happening.

## Root cause 1 — wedged engine on Pale (IP_PALE), no auto-fix path
- Archivist (archivist-q8 alias -> Qwen3.8-27B-Q8_0, gpu 1) unreachable: /v1/chat/completions
  hung for minutes; active-generations stayed count=0 (requests never reached the worker).
- Full unload+load of the model did NOT clear it (engine dispatch layer deadlocked, not model state).
- Watchdog gap: streak>=8 on a LIVE host passes reason='reload', but _studio_recover only
  UNLOADs when reason=='wedged' -> every 'reload' was a no-op re-load of the resident model.
  The 'wedged' path requires 120 consecutive BUSY ticks (2h), which a timeout never produces.
  Net: portal burned its 3 reload attempts, re-armed, repeated - forever. No reboot path
  because the host TCP was alive.

## Fix 1 (code) — agent_portal.py _studio_recover
'reload' now really unloads+loads (unload failure tolerated; load decides). The existing
streak>=8 branch on a live host therefore clears wedged engines within ~13 min + one cycle.
Portal restarted by portal_host (respawn, CREATE_NO_WINDOW) to pick up the fix.
Immediate: manual unload+load then WinRM reboot of Pale (approved 11-15); boot tasks reload
both Pale models (Q8_0 archivist, Q4_K_S designer).

## Root cause 2 — zombie guardian = the popups
portal_guardian.py (old chain) no longer existed on disk but a zombie pythonw instance
(PID 19648, spawned 15:48 via cmd /c, parent gone) kept running and spawned
memory\mechanic\oom_recovery.py watch every 20s = visible console + focus steal.
Nothing references it anymore (all hits are comments); no schtask for it; killed. Its .vbs
archived to archive/orphaned_20261123/. All remaining spawns run inside portal_host.py
with CREATE_NO_WINDOW; zero periodic schtasks left (verified: only MS/NVIDIA tasks).

## Verify
- Pale back + /v1/chat/completions answers on both alias and raw id.
- Portal log shows Archivist recover OK; goals 82/82 -> Lv 4 report written.
- No console windows appear over the next hour (guardian gone, host windowless).
