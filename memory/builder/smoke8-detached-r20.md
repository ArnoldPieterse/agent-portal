# smoke8 detached one-shot r20 (Builder, 2026-11-14 auto-continue)
Closes the TODO NEXT item "smoke8 when convenient" as far as an agent seat can: I run on Black (192.168.1.99) and have NO portal reachability from here — 127.0.0.1:8099 = WinError 10013, LAN 192.168.1.179:8099 = timeout (consistent with r16/r17 sandbox-degradation findings; probe artifact `probe_white_portal_r20.py`).

## Artifact
- `memory/builder/smoke8_detached_r20.ps1` — 2,801 B / md5 6efce4d7e0ee536ddc07f4210ffc8607 (LF).
- Gates: canonical-root check (agent_portal.py + smoke8.py present) → **smoke8.py hash gate** (pin 520323ca051c044db6d5f0ff0ba6a497 / 2,514 B, measured this round from the shared mirror) → single-instance gate (refuses a second launch — 01:24 double-launch lesson) → :8099 listener gate.
- Launches `python smoke8.py` DETACHED with `-RedirectStandardOutput smoke8_r20.log`; smoke8.py writes `smoke8_result.json` incrementally and ends with verdict line ALL_OK/PARTIAL.

## Why detached is the only safe shape
- Portal serializes (parallel_slots=1): a smoke started mid-turn simply queues behind this chat's slot and makes progress after the turn frees it — no parallel quinn-q4 traffic, so wedge #2 mechanism (hosts.md) is not triggered. In-process/mid-turn execution would instead block on its own queue (420 s timeouts per agent).
- smoke8.py docstring already mandates serial-only + detached-after-turn; this one-shot just adds the gates.

## Run instruction (HUMAN LEG — Arnold, White console)
```
cd <canonical root>            # folder containing agent_portal.py
powershell -ExecutionPolicy Bypass -File memory\builder\smoke8_detached_r20.ps1
```
Then check `smoke8_result.json` → expect `"verdict": "ALL_OK"` (8/8: ORCH/RES/BUILDER/VERIFIER/DESIGNER/ARCHIVIST/SCRIBE/MECHANIC -OK). Relay verdict + per-agent secs to chat; Verifier can close on the JSON.

## Status
- Artifact LANDED in shared folder (this seat) 2026-11-14 ~02:0x; propagation to White per normal mirror behavior — re-verify md5 on White before first use (standing rule from r16b).
- NOT YET RUN: pending Arnold's console leg. Remaining non-agent items on the TODO NEXT line are chat-level (dcabots group re-prompt = Orchestrator/Arnold; cleanup ≈39 GB candidates stay untouched per note).
