# Overnight remote unloading — investigation (Researcher)
Opened 2026-11-13 ~18:3x from fleet-panel first reveal (MEMORY.md 11-13): remotes UNLOADED overnight; White served the group all day. Status: ANALYSIS COMPLETE, LIVE CONFIRMATION PENDING (my tools have no LAN reachability — probe requests appended to TODO).

## Observation (supported, from memory files)
- 11-12 ~18:0x Red DUAL_UP (mechanic-q4 + scribe-q8), smoke8 GREEN 18:29; 11-12 22:56 Pale DUAL_UP (archivist-q8 + designer-q4). [memory/llm/hosts.md]
- 11-13 10:17 Red /v1/models answered with BOTH models UNLOADED (server itself was up); then reloaded to DUAL_UP by ~18:0x. [hosts.md]
- 11-13 Pale "ONLINE since ~13:40", Black LAN access "ONLINE since ~13:5x" — both hosts/Studio unreachable from White before midday. [hosts.md]
- Remotes run LM Studio v2026.11.3 / v0.1.916-beta (same build Red/Pale/Black). White layout per instances.md.

## Candidate explanations, ranked
### H1 — JIT idle TTL auto-evict (SUPPORTED mechanism, INFERRED as cause; confidence MEDIUM-HIGH)
LM Studio server has JIT loading [default enabled] and an Idle TTL: a JIT-loaded model is auto-unloaded after the TTL expires with no requests; app-default TTL 60 min (per-user configurable; one user reports jitModelTTL=300s). Auto-Evict (default ON) keeps at most 1 JIT model resident. Sources:
- https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict
- https://github.com/lmstudio-ai/lmstudio-bug-tracker/issues/2423 (open, 2026-09-20, LM Studio 0.4.24: confirms `jitModelTTL` server setting; Bionic/tray-loaded models do NOT get TTL — related #1782 tray load ignores idle TTL, #1278 auto-eject request)
Feature existed by Sep 2026 (0.4.24) => present in remotes' Nov-2026 build (inferred).
Fit: server stays up overnight while models get evicted after ~1h idle = exactly the 10:17 Red state. Tension: dual residency (2 models at once) contradicts default Auto-Evict — so either their server settings have auto-evict OFF, or loads were UI/explicit with a per-model saved "Auto Unload If Idle (TTL)" (the issue cites such a saved model load setting). Either variant still yields overnight unload if a TTL value is set.
### H2 — host power state (sleep/off overnight; Studio auto_start respawns API without models) (confidence MEDIUM)
Fit: Pale/Black only "ONLINE since ~13:4x/13:5x" 11-13 reads like machines that were down and came up at midday (manual power-on or sleep-resume). Black has auto_start per hosts.md; if Red's Studio also autostarts, an overnight reboot/sleep yields server-up + models-unloaded by 10:17. Discriminator: LastBootUpTime per host + System event-log sleep/resume (42/507) or shutdown (6008/1074/41) entries in the 11-12 ~18:00 → 11-13 ~10:00 window.
### H3 — engine update killed instances overnight + auto-start respawn (confidence LOW-MEDIUM)
Known durable rule from White 11-10: engine/llama binary update kills all llama-server processes; API may still show loaded=true. Remotes are same-build, and Arnold's Red file-migration work happened during the day — no recorded overnight engine push. Discriminator: mtime of llama-server.exe on each remote + Studio version-log deltas.
### H4 — manual unload by a human overnight (confidence LOW; residual)
No log evidence either way; only if H1-H3 all fail their discriminators.

## Counter-evidence considered
- If models were loaded via UI/Bionic/tray or `lms load`, they carry NO TTL (#2423, #1782) and would NOT auto-unload — this is the main threat to H1; it pushes weight toward H2 unless a per-model saved TTL was set. Resolvable by reading each remote's Studio server-settings + model-load settings (file: %APPDATA%/LM Studio or ~/.lmstudio on host).
- White survived the night serving this chat (quinn-q4) — weak against H1 only if White's models were also JIT-loaded; White's loads go through recover_all.py (explicit), so no contradiction. Not decisive.

## Pending live checks (need LAN access — my sandbox has none; web_search only)
Ask Mechanic/Arnold to run per remote host (Red via WinRM user `Red` empty pw; Pale/Black analogous):
1. `(Get-CimInstance Win32_OperatingSystem).LastBootUpTime` + uptime.
2. `Get-WinEvent -LogName System -MaxEvents 50 | where Message match 'sleep|resume|shutdown'` for the overnight window (or Event IDs 42/107/6008/1074/41).
3. `dir llama-server.exe` mtime (engine-update test, H3).
4. Read Studio server settings: jitModelTTL / auto-evict value + per-model saved TTL (H1 confirmation) — %APPDATA%\LM Studio or ~/.lmstudio on the host.
First result of #1/#2 decides H1 vs H2; #4 converts H1 from inferred to supported.

## Verdict (current)
Most likely: JIT idle-TTL eviction (H1) if any TTL is configured in remote server/model settings, else overnight host power state (H2). Both fully consistent with all recorded observations. Confidence: mechanism exists = HIGH; specific cause per host = MEDIUM pending checks 1+4.
