# RUNBOOK - White rename closeout (Mechanic, 2026-11-14 ~03:4x, Red seat)

## One-line note
What broke: `fleet_reload.py` WHITE section pointed at a never-executed folder rename + v1 unload sent `{'id'}` to an endpoint requiring `model_path`; what fixed it: v2 (unload by full path, load Q8-first per proven recipe, idempotent rename step) landed 01:26-01:45, dual-resident verified on the fleet panel.

## Closeout verification (this round, from Red seat)
- AC-A2-2 probe restaged byte-exact: `memory/mechanic/ac_a2_live_leg_r20.py` = 2,341 B / md5 46f529dde45b21276be49a6ce1bd8e15 (pin 46f529dd) - PASS.
- `llm/hosts.md` White line + "White model folders -> fleet convention" section DONE (file mtime 02:14; Researcher path-corrections in lines 22-23). Cross-checked against `studio-api.md` rename record (DONE 01:45) and `instances.md` convention patch (lines 13-15): all three leaves agree on `unsloth\Qwen3.8-27B-Q4_K_S` + `lmstudio-community\Qwen3.8-27B-Q8_0`. Only remaining quant-less path in llm/ = hosts.md line 47 (11-11 WSL-Inbox provenance, explicitly annotated historical at line 25) - correct as-is.
- smoke8 PARTIAL from Red: REMOTE4_OK 03:23 (Black .99 + Pale .39 dual-resident, 4/4 seats GREEN; evidence `smoke8_partial_red_seat.json` + runbook above).
- White live state NOT re-probable from Red seat (sandbox allowlist excludes .179; portal :8099 unreachable per lan_probe 02:46; no WinRM to White). Last ground truth = 01:45 panel verification (dual-resident, both quant tags shown) - consistent with all memory leaves.

## Still open = HUMAN LEGS only (Arnold / White console)
1. Re-prompt the dcabots group task (only Orchestrator's turn failed; other seven seats answered).
2. Full smoke8 from White console (portal :8099 local leg; covers orchestrator/researcher/scribe/mechanic seats).

## Durable rules carried forward
- After ANY Studio load: poll /api/inference/loaded-models until resident; the 200 ack is async (Q8 took ~4 min to become resident on White).
- On White a COUNT-based loaded check is the only reliable guard (both variants report bare id `Qwen3.8-27B-GGUF`).
- If hub download `unsloth/Qwen3.8-27B-GGUF` (UD-Q8_K_XL) resumes it may recreate a quant-less folder - rename again (idempotent step in white_realias_rename.py v2 doubles as recovery).
