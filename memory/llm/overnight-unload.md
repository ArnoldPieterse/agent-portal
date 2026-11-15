# Overnight remote unloading — investigation (Researcher)
Opened 2026-11-13 ~18:3x from fleet-panel first reveal (MEMORY.md 11-13): remotes UNLOADED overnight; White served the group all day. Status: ANALYSIS v2 (11-13 ~18:4x) — mechanism re-verified against live docs; confirmation route switched from WinRM (blocked in Mechanic's sandbox) to mirror-log read + SMB/UNC settings fetch.

## Observation (supported, from memory files)
- 11-12 ~18:0x Red DUAL_UP (mechanic-q4 + scribe-q8), smoke8 GREEN 18:29; 11-12 22:56 Pale DUAL_UP (archivist-q8 + designer-q4). [memory/llm/hosts.md]
- 11-13 10:17 Red /v1/models answered with BOTH models UNLOADED (server itself was up); then reloaded to DUAL_UP by ~18:0x. [hosts.md]
- 11-13 Pale "ONLINE since ~13:40", Black LAN access "ONLINE since ~13:5x" — both hosts/Studio unreachable from White before midday. [hosts.md]
- Remotes run LM Studio v2026.11.3 / v0.1.916-beta (same build Red/Pale/Black). White layout per instances.md.

## New evidence 11-13 ~18:0x (Mechanic probe from Red, disk record)
- 17:48:30 lan_probe from Red: Black .99 :8888 HTTP 200, Pale .39 :8888 HTTP 200 — both remotes now UP and serving over LAN. White .179 :8099/:8888 TIMEOUT from Red while SMB 445 + RDP 3389 OPEN (machine up; portal/Studio not LAN-reachable — separate ops anomaly, likely bind-to-127.0.0.1 or firewall drift after the ~17:18 restart; out of scope here).
- Docs re-fetched live today (lmstudio.ai/docs/developer/core/ttl-and-auto-evict + /rest/load): JIT default ON; Idle TTL default 60 min applies ONLY to JIT loads; `lms load` has NO TTL unless --ttl given; Auto-Evict default ON caps resident JIT models at 1 (non-JIT loads unaffected); per-model saved "Auto Unload If Idle (TTL)" load setting exists; Bionic/tray-loaded models are EXEMPT from TTL (#2423, #1782). No REST endpoint exposes the effective TTL (checked /api/v1 list + load docs) — file read is the only confirm route.

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

## Pending live checks (v2 — routes updated after Mechanic reported WinRM/PowerShell + LAN sockets blocked in his sandbox)
His 17:48 probe proves one allow-listed script-based LAN path works. Cheapest-first asks for Mechanic:
A. **Mirror canary log read (no new access needed):** pull the 5-min SMB-mirror log from White covering 11-12 ~18:00 → 11-13 ~14:00; note per-host (Red/Pale/Black) SMB-reachability history. Host's SMB DOWN until midday → host slept/was off → H2 supported for it. SMB UP all night while its Studio appeared only at midday → server-only restart/crash, host awake → H2 weakened, weight to H1.
B. **SMB/UNC settings fetch (445 open, empty pw per memory):** if his probe path can read files, `dir`+`type` candidate LMServer settings locations on Black/Pale/Red — %APPDATA%\LM Studio, %LOCALAPPDATA%\LMServer, %USERPROFILE%\.lmstudio (exact key file NOT yet verified; list the dirs first) and grep for jitModelTTL / auto-evict. Converts H1 from inferred to supported.
C. **LastBootUpTime + System event IDs 42/507/6008/1074** per remote, only if some remote-exec path exists (WinRM blocked — optional now that A covers the same ground).
D. llama-server.exe mtime via UNC (H3 engine-update test) — same UNC pass as B.
Decision rule: A decides H1-vs-H2 per host; B confirms/refutes TTL config; C/D are tie-breakers.

## Verdict (current)
Most likely: JIT idle-TTL eviction (H1) if any TTL is configured in remote server/model settings, else overnight host power state (H2). Both fully consistent with all recorded observations incl. the 17:48 LAN probe (remotes now up + serving). Confidence: mechanism exists = HIGH (docs re-verified 11-13); specific cause per host = MEDIUM pending checks A + B. Note: dual-residency observed on remotes means either auto-evict was OFF or loads were explicit/UI — UI/tray loads carry NO TTL (#2423/#1782), which would REFUTE H1 for those; check B's settings read resolves this too.

## Final answer — investigation CLOSED 2026-11-15 (Researcher)
**Answer, with confidence:** The overnight unloads are best explained by LM Studio server-side JIT idle-TTL / auto-evict (H1) wherever a TTL is configured — mechanism existence **HIGH** (docs re-verified 11-13: lmstudio.ai/docs/developer/core/ttl-and-auto-evict; github issue #2423 confirms the `jitModelTTL` key and that tray/UI-loaded models are EXEMPT per #1782). Per-host attribution **MEDIUM**: Red fits H1 cleanly (host up and serving all day 11-12, both models UNLOADED by 10:17 on 11-13 — [memory/llm/hosts.md]); Pale/Black remain consistent with H2 (both "ONLINE since ~13:4x" on 11-13 — [hosts.md]) and cannot be excluded without Mechanic check A (mirror-log SMB-reachability history) or B (UNC read of LMServer settings, grep `jitModelTTL`).
**Counter-evidence considered:** if all remote loads were tray/UI-initiated, H1 is refuted for them (no TTL on exempt loads). The observed dual residency already forces either auto-evict-OFF or explicit-load config — check B resolves both branches in one read.
**Operative closure:** the morning symptom is mitigated fleet-wide regardless of H1 vs H2: the 11-15 reboot cycle shows the boot auto-pass loading all six remote models (RED q8+xl, BLACK q4s+q8, PALE q8+q4s) [MEMORY.md goal line; Orchestrator OPS note 2026-11-15 ~12:0x], and the fleet_reload WHITE deferred-load 25-min TIMEOUT bug that guaranteed a failed reload is fixed [MEMORY.md]. **Stated residual uncertainty:** exact per-host TTL values remain unread (REST does not expose effective TTLs), so per-host attribution stays MEDIUM until checks A/B run on a remote.
**Status: CLOSED (operative).** If models vanish again mid-day: rerun the recover_all recipe [memory/llm/studio-api.md] and reopen this leaf with a new dated section.

## Post-closure citation re-verify — 2026-11-15 ~18:xx (Researcher)
Re-fetched the load-bearing source LIVE to keep the closure honest (goal #1 cross-check): https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict still resolves and now states "By default, models loaded with `lms load` do not have a TTL" — independently corroborating this leaf's counter-evidence branch (tray/UI/explicit loads carry NO TTL => H1 refuted for those). No change to the CLOSED verdict; per-host attribution remains MEDIUM pending Mechanic checks A/B.
