# Host idle-time investigation - 2026-11-26 (Studio seat, user request)
Symptom: fleet panel showed Red CPU 0%, Pale VRAM 1.4%/CPU 0%, Black no data while "we should be constantly busy". Fleet DEGRADED (health 75), 29 open blockers = exactly the 8 Pale agents' open goals.

## Findings (all verified live 21:20-21:35)
1. PALE MODEL-DROP 18:26->19:55: model-load.jsonl missing-set jumped from {Builder,Forge} to all 8 Pale agents. Pale Studio healthy (/api/health <1s) but VRAM 1.4% = models UNLOADED (not a network fault). Recovery chain self-healing: Q8_0 resident on Pale again by ~21:30; Splice reloaded 21:24.
2. SEAT PROBE MISCLASSIFIES: _model_load_status pings /v1/chat/completions max_tokens=1, timeout 15s. Absent/loading model HANGS instead of 404 -> status 'unreachable' (not 'not_loaded') -> agent excluded from autoloop cast for the whole load window; Archivist misread as 'busy' (active_generations match, busy_ticks=7). Loads serialize per host (LOAD QUEUE) so multi-model recovery takes many minutes while probes keep failing.
3. BLACK INVISIBLE TO SEAT RESOLUTION (FIXED): memory/llm/hotload-catalog.json was INVALID JSON - 54 bad escapes, all `C:\Users\<host>\` single-backslash folder paths -> _fleet_host_names()={} (swallowed) -> _fleet_host_key(Black)="" -> /api/inference/loaded-models 401 -> Black's resident models (verifier-q4, builder-q8) never offered as fallback seats. FIXED 2026-11-26: doubled the backslashes, file parses; running portal still needs RESTART to clear _HOST_NAME_CACHE.
4. NO RECOVERY RECIPES for Lumen/Reel/Splice in _FLEET_RECOVER_RECIPES -> down_episode reloads=0 since Nov 23 (Designer's subs ride designer-q4/Q4_K_S on Pale; a recipe like Designer's with gguf_variant UD-Q4_K_S would let the chain reload them).
5. CHRONIC EPISODES (autoloop.json down_episode): Verifier+Designer down since Nov 22; Researcher/Outlet since ~Nov 25 21:30; Archivist since Nov 23 - repeated reloads, never a full recovery of the Pale Q4 slot.
6. SECONDARY: cycle_30m rc=124 (memory_mirror.py >900s TIMEOUT, SMB slowness); cycle_1h step 3/6 rc=2 (snapshot/daily-commit skipped that run); White disk 94.3%; /api/health/fleet probe entries stale since 2026-11-16 while last_probe_line is fresh (two probe systems, old one dead).

## Why hosts looked idle
Only 2 of 4 hosts usable: White busy (VRAM 77.8%, this chat on quinn-q4), Red working fine (Mechanic, inference_active=true; CPU 0% = between bursts). Pale = 8 agents/29 open goals blocked by the model-drop + slow serialized recovery. Black = healthy with 2 resident models but zero seats mapped AND catalog bug hid it from fallback placement too.

## Recommended actions (for Orchestrator/Mechanic)
- Restart portal to activate fixed catalog (Black becomes a fallback seat: Verifier q4 -> Black verifier-q4).
- Add Lumen/Reel/Splice recipes (pale, UD-Q4_K_S, gpu 0) to _FLEET_RECOVER_RECIPES.
- Seat probe: on timeout, follow up with GET /api/inference/loaded-models to distinguish 'loading' vs 'unreachable' (cleaner recovery classification).
- Watch White disk 94.3% (cleanup before dream-sync window).
