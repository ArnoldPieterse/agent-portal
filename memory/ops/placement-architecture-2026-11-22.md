# Host-agnostic placement (agents are not pinned to hosts) - 2026-11-22

User directive: with hot-load-on-demand in place, agents must NOT depend on specific hosts.
A turn picks the FIRST AVAILABLE host where the agent's model is already resident, drops the
agent's profile + working activities on top (profile = prompt context from the shared tree;
working state = mirrored memory/ tree - already host-independent), and runs there. The backend
(host/Studio) is thereby split from the agents: **the whole portal + all agents can operate
from a single active host.**

## How it works (agent_portal.py)
- `_resolve_seat(agent)` - placement engine, called at the top of every `stream_chat` turn:
  candidates = [home host, local White, other hosts in agents.json order]; first host with the
  model RESIDENT wins. Home keeps the agent's alias id (behavior unchanged); a foreign host
  gets the loaded-models id of the resident model. Quant-family fallback (q8<->q4) is offered
  ONLY when the home host itself is unreachable. No loading happens here - if no host has it
  resident, the turn falls back to the P1 home hot-load path (`_ensure_seat_ready`: native
  /api/inference/load + WinRM reboot chain).
- The chosen seat is a THREAD-LOCAL override: `studio_base()`, `studio_headers()` and both
  request bodies (main + `_aux_chat` ReadMem/StoreMem rounds) follow it for the duration of
  the turn. No global state; parallel turns on different hosts are isolated per worker thread.
- Autoloop ready filter: a seat whose home model is down is still fired when another reachable
  host serves its model (single-host operation); home recovery chain keeps running in parallel.
- SSE frame `{"model_load": "<agent> -> placed on <host> (<model> resident[, quant fallback])"}`
  + activity-log event `placed` - visible in the chat bubble (.loadnote) and activity timeline.

## Rules / invariants
1. Placement only uses models that are ALREADY RESIDENT (VRAM-safe by construction); loading is
   still home-only via the P1 path (recipes carry per-host model paths).
2. Home-first ordering: zero behavior change while a seat's home serves it.
3. Candidate host set derives from agents.json 'studio' fields + local STUDIO - no new config.
4. hotload-catalog.json is STALE for placement (missing remote models, swapped black/red labels)
   - do not use it for routing; the recovery recipes + live loaded-models probes are truth.

## Verified
Scratch sim 8/8 (home resident / home-down exact on White / quant fallback / all-down -> P1
path / thread-local isolation / home-exact precedence). Live: portal restarted, APIs healthy.
