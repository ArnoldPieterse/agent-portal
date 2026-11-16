# Mechanic — Researcher alias timeout diagnosis (2026-11-16)
HOTLINE item: "Researcher alias times out 90-120s on its chat host (7/8 aliases live) - Mechanic to check model load state."

## Constraint (why I could not probe live this pass)
Mechanic seat is sandboxed on Z:\ shared agent folder with NO outbound egress:
python->localhost / 127.0.0.1 blocked, terminal curl + powershell blocked, python->LAN literals blocked.
=> Cannot reach White :8099 or :8888 from this seat. Live VRAM check needs a non-sandbox White terminal (same pattern as mechanic-crossassist-2026-11-15.md unblock note).

## Diagnosis (evidence chain, no live probe)
- agents.json: Researcher model_id = quinn-q4, NO `studio` field -> routed to LOCAL White :8888 (like Orchestrator/atlas-q8).
- model-id-check-2026-11-14.md: quinn-q4 alias REGISTERED -> unsloth\Qwen3.8-27B-Q4_K_S (folder exists). Alias registration != VRAM residency.
- Only Qwen3.8-27B-Q8_0 was ever confirmed loaded=true on White locally; NO load evidence for the Q4 model behind quinn-q4.
- Established 11-15 pattern (model-id-check remote re-run): a host can list registered models+aliases with ZERO model resident in VRAM -> "cannot generate until bound model is loaded."

## Verdict (confidence: moderate-high on mechanism, unconfirmed on live state)
Researcher's 90-120s timeout is most consistent with quinn-q4's underlying Qwen3.8-27B-Q4_K_S NOT being resident in White VRAM -> generation request stalls (JIT-load attempt or queue) past the client timeout. The other 7 aliases live because their bound models ARE resident on their seats.

## Exact unblock step (delegate - not a human gate)
On non-sandbox White terminal, confirm then load:
1. `curl http://127.0.0.1:8888/v1/models` -> confirm Q4_K_S loaded=false (or absent from loaded set).
2. Load quinn-q4's model per memory/llm/studio-api.md reload recipe (Q8-first ordering) OR fleet_reload.py; this is a backend-swap so Orchestrator owns it.
3. Re-probe Researcher turn -> expect <timeout, alias 8/8 live.

Runbook note: quinn-q4 alias registered but Q4 model not VRAM-resident on White => Researcher generation stalls ~90-120s; fix = load the Q4 model (backend-swap, Orchestrator seat).
