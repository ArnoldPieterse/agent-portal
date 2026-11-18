# Ops — Windows runbook: portal lifecycle, reboot recovery, ground truth
Last updated: 2026-11-12 (agent rename Atlas->Orchestrator, Quinn->Researcher; aliases quinn-q4/atlas-q8 unchanged).
## Reboot recovery runbook (verified after the 2026-11-10 reboot)
What AUTO-STARTS on boot:
- Studio :8888 + the Q4 instance (quinn-q4, GPU0) — loads itself; this Studio chat rides on it.
- Portal :8099 via `PortalRun` task (earlier assumption that it did NOT auto-start was WRONG).
What does NOT auto-start:
- Orchestrator's Q8 instance (ex-Atlas; GPU1 sits empty). Fix: `schtasks /run /tn RecoverAll` (recover_all.bat ->
  recover_all.py) -> verdict in recover_result.json (expect ALL_UP). Q4-first order is safe there;
  the chat slot must be idle (no active Studio turn).
- `LlamaRPCWorker` task is Disabled — the White RPC worker is legacy/optional; the current
  dual-residency architecture does not depend on either RPC worker.
Post-reboot verification order:
1. nvidia-smi per-GPU VRAM (expect Q4 ~20.5 GB GPU0; GPU1 empty until RecoverAll).
2. GET :8888/api/inference/status + /api/inference/active-generations.
3. Portal: GET :8099/api/memory -> 200.
4. Functional probe ATLAS first (quinn-q4's single slot is held by any active Studio chat turn —
   probing it from inside a turn deadlocks behind itself; see memory/llm/instances.md (Wedge incident)).

## Portal lifecycle
- Portal :8099 = agent_portal.py, started detached via scheduled task `PortalRun` -> **portal_hidden.vbs** (2026-11-15) -> hidden cmd -> portal_start.bat -> **pythonw.exe**.
  WINDOWLESS: wscript + WshShell.Run style 0 + pythonw = zero console popups (user-critical complaint 2026-11-15; old direct-.bat task left a visible cmd for the portal's whole life, and MemoryMirrorRun's `cmd /c` wrapper popped a visible window every 5 min with the title flipping to `net.` while it ran `net use` against dead hosts). The periodic tasks (MemoryMirrorRun 5-min, PortalFleetProbe 10-min, PortalDailyGitCommit daily) now run pythonw DIRECTLY as the task action - no cmd wrapper, and their scripts use absolute log paths because schtask has no WorkingDirectory.
  The task's Status stays "Running" for the portal's WHOLE lifetime (the waiting vbs keeps it alive).
- Restart TRAP: `schtasks /run /tn PortalRun` reports SUCCESS but NO-OPS while Status is Running — the old
  PID keeps :8099 and serves STALE code (the duplicate pythonw dies on bind-fail 10048, visible only in
  portal_run_err.log). Correct restart: `taskkill /pid <PID from _portal_pid.txt> /f`,
  THEN `schtasks /run /tn PortalRun`, then confirm a NEW PID listens on :8099 (Get-NetTCPConnection
  -LocalPort 8099) and PROVE it postdates the edit: process CreationDate > agent_portal.py LastWriteTime.
  Write the new PID to _portal_pid.txt. The hidden cmd hosting the portal exits automatically when the
  pythonw child dies; if a stale HIDDEN cmd ever lingers, `tasklist` shows it but no window does -
  kill by PID. (2026-11-11 MIME incident: fix on disk ~20 min while the live server still served
  text/plain for .html.)
- Logs: portal_run.log / portal_run_err.log.
- After editing index.html: user must HARD-REFRESH (Ctrl+Shift+R) — stale tabs keep old JS.
- After editing agent_portal.py: restart as above, then verify with GET /api/memory + a probe script.

## Ground-truth checks
- GPU state: nvidia-smi per-GPU VRAM (dual-resident = Q4 ~20.6 GB on GPU0, Q8 ~30.1 GB on GPU1).
- Studio API :8888: GET /v1/models, /api/inference/status, /api/settings/model-aliases.
- Detached workers: verify via API + nvidia-smi + result files; a raw detached python worker can die before
  writing its result — prefer the .bat + schtasks chain.

## Windows quirks
- Piped stdin makes `powershell -Command` refuse to run ("Input redirection is not supported") -> launch detached things via .bat + schtasks.
- Launching a detached runner with `powershell -Command Start-Process ...` chained in ONE tool call can spawn the child TWICE (observed 2026-11-11 ~22:4x: two serial_e2e_wait.py, different pythons). After any such launch, verify a SINGLE instance: `Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object CommandLine -like '*<script>*'` and kill extras before the run starts (two concurrent group-e2e runs = parallel local streams = wedge risk).
- Detached runners that touch LOCAL models must self-wait for Studio idle (`/api/health` inference_active=False) because the active chat turn holds quinn-q4's slot (see Recovery section).
- NTFS is case-insensitive: memory.md == MEMORY.md (ONE file; portal and Studio chat share it).
- Long-lived detached waiters: register them as a REAL scheduled task (`schtasks /create` interactive, user White) - an ad-hoc Start-Process child of an ephemeral tool session dies when that session ends (observed 11-12 ~5:0x: first RedQ8Wait instance logged only 'start' at 5:01 then vanished). After launch, verify the PID is alive (Win32_Process CommandLine filter) before trusting it.


## Auto-start after reboot (set 2026-11-12 pre-reboot audit)
No host auto-logons (AutoAdminLogon=0 everywhere) -> "auto start" = at user logon (console or RDP).
| Host | Studio :8888 | Models | Portal |
|---|---|---|---|
| White | HKCU Run `Unsloth --hidden` (added 11-12; also auto-restores Q4 ~4min post-boot) | `_boot_recover.vbs` in Startup: +3min -> `schtasks /run /tn RecoverAll` (recover_all.py: reloads Q8 GPU1 + Q4 GPU0, probes, and STARTS PORTAL IF DOWN via PortalRun). 11-15: task action now `wscript recover_hidden.vbs` (style-0 hidden cmd) - it was the one boot-time launcher still showing a visible window | started by recover_all.py step 6; manual fallback `schtasks /run /tn PortalRun` (RESTART TRAP still applies for code changes) |
| Red .245 | HKCU Run `Unsloth --hidden` (pre-existing, verified via WinRM) | `_boot_fleet.vbs` in White Startup: +6min -> fleet_reload.bat (waits up to 20min on /api/health, loads Q8_0 GPU1 ctx32768->16384 + XL GPU0 ctx65536, skips if both resident) | n/a |
| Black .99 | HKCU Run `Unsloth --hidden` (verified) | same fleet_reload.py (JWT login auth, Q4_K_S GPU0 65536 + Q8_0 GPU1 32768 alongside) | n/a |
| Pale .39 | presumed same Run entry (no WinRM to verify - it survived the 11-11 reboot) | same fleet_reload.py (Bearer key from pale_dl.py, Q8_0 GPU1 16384 first then Q4_K_S GPU0 65536->32768 alongside) | n/a |
Notes: root-level schtasks /create and Set-ScheduledTask on existing tasks need ADMIN (White is not admin; the 11-12 trigger attempts failed with 0x80070005 - hence Startup-folder VBS instead). Stale \RedQ8Wait DISABLED 11-12 (was armed 23:59). fleet_reload.py = idempotent (skips loaded hosts); results in recover_result.json + fleet_reload_result.json.
**11-15 popup rule (user-critical):** a task action that is a .bat under an interactive token ALWAYS shows a window - wrap it in a style-0 vbs (portal_hidden.vbs / recover_hidden.vbs pattern). Any pythonw-hosted script must pass `creationflags=0x08000000` (CREATE_NO_WINDOW) to every console child (GUI parent + console child = fresh visible console even with capture_output) - memory_mirror.py + agent_portal.py fixed 11-15. Verify popup fixes by FORCING the trigger path while polling EnumWindows for ConsoleWindowClass, never post-hoc. Detail: memory/portal/bugs/popup-pythonw-children-recoverall-2026-11-15.md.

11-12 post-reboot: fleet_reload.py had 2 bugs (wait_up returned None -> white()/red() exited early; RED missing from thread tuple) - FIXED + verified. Pale Studio was already down at fleet start 19:23 (machine alive, :8888 refused) - needs manual logon/startup; load its dual via API after (Q8_0 GPU1 ctx16384 then Q4_K_S GPU0 ctx65536 alongside, key in pale_dl.py).
