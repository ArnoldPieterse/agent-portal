# Fleet Status Panel — decision, contract, evidence
Last updated: 2026-11-13 (BUILT + VERIFIED). Source: 8-agent round-table (group_e2e_result_8agent.json) + Orchestrator build notes.

## Decision
Live view of all 4 hosts on the portal — loaded models, quantization, busy/idle/unknown per host — so backend swaps and fleet state are visible instead of buried in logs. Arnold approved the build 2026-11-13 ("build").

## Locked state definitions (round-table)
- **busy** = >=1 active generation on that Studio (`/api/inference/active-generations` count > 0)
- **idle** = reachable, no active generations
- **unknown** = probe failed; `last_seen` from cache ages as stale (TTL 15s); a dead host never renders green/idle

## Spec adaptation (recorded honestly)
The round-table spec assumed each host runs its own portal process writing `fleet-state-<host>.json`. Ground truth: **only White runs :8099**; Red/Pale/Black run bare Studio on :8888. So v1 = **on-demand lightweight probes**: `GET /api/fleet` queries each host's `/api/inference/active-generations` + `/v1/models` (metadata only, no inference load), 3s timeout per endpoint, and only when a human opens/refreshes the panel (frontend polls every 5s while open). No background timer in agent_portal.py (Mechanic's veto preserved), no new ports/tasks/deps. The mount asymmetry that broke the file-based design was separately fixed 11-13 (SMB mirror + per-turn sync) — but there is still no shared writable store, so on-demand probing remains the correct transport.

## API contract — GET /api/fleet (:8099)
`{"ts": <unix>, "ttl": 15, "hosts": [{host, base, agents[], models[{id,quant}], generations, state: busy|idle|unknown, last_seen, reason}]}`
- Host list derived at request time from unique `studio` bases in agents.json + local Studio (nothing hardcoded).
- Remote hosts probed with that host's agent Bearer key; local probe uses no key.
- Dead host: probe returns None -> state unknown + reason unreachable/stale(Ns); response stays 200, no hang.

## UI (index.html)
🛰 Fleet button in the mode bar (next to ⏱ Activity) -> collapsible `#fleetPanel`: per-host row with colored dot (amber busy / green idle / red unknown), models + quant, assigned agents, "last seen Ns ago" aging; 5s auto-refresh while open; loading/error states; native button = keyboard reachable.

## Verification evidence (2026-11-13)
- Live capture: 4 hosts — White busy (gens=1, Qwen3.8-27B-GGUF loaded); .99/.39/.245 idle with **zero models loaded** (raw /v1/models confirms every entry unloaded — fleet had gone to sleep overnight; first thing the panel revealed).
- Dead-host repro: temporary fake host [LAN-IP] -> `unknown`/`unreachable`, HTTP 200, bounded ~7s; agents.json restored byte-identical (md5 match).
- Regression: /api/memory, /api/agents, /api/activity all 200; index.html serves each new block exactly once; agent_portal.py first-1600-chars header md5 unchanged (2ba0b031a46c70b1ab5e643ae1347acd); /api/chat Solo proven by live operation through the restarted portal.
- Portal restart: PID 24808 killed -> relaunched detached via one-shot schtask (wmic removed on this OS; `start` children are reaped by the terminal wrapper) -> new PID 21988, task deleted immediately after.

## Ops notes
- The probe endpoint IS the ground-truth check: `GET :8099/api/fleet` -> 200 + one entry per host; a dead host must show unknown, never idle/green.
- Hard refresh required after frontend edits (index.html changed).
- If a remote Studio key rotates, /api/fleet shows that host unknown until agents.json keys are refreshed.

## Ratification (Orchestrator, 2026-11-15) — Designer's tabled proposals CLOSED
Decision: **RATIFY** both of Designer's 2026-11-13 fleet-status proposals; they are no longer "PROPOSED/tabled."
- **Open item 1 (idle/busy definition): RATIFIED.** The "Locked state definitions (round-table)" above ARE the ratified contract — busy = >=1 active generation, idle = reachable + no generations, unknown = probe failed / stale (never rendered green/idle). Basis: the panel is BUILT + VERIFIED (2026-11-13) against exactly these definitions; nothing to re-derive. Compression owner was Scribe+Mechanic; since the locked defs are live and verified, Orchestrator records ratification here to clear the tabled status.
- **Open item 2 (one-sentence spec): RATIFIED** (this was my explicit gate). Realized as: `GET /api/fleet` = on-demand, metadata-only probes of each host's `/api/inference/active-generations` + `/v1/models`, no background timer in agent_portal.py (Mechanic veto preserved), no new ports/tasks/deps. Builder may cut the stub against this contract; Verifier accepts per AC-1…AC-5.
Consequence: upgrade-plan.md Open items 1 & 2 -> CLOSED. Verifier's /api/fleet evidence (open item 3) remains the only fleet-status gate still open.
