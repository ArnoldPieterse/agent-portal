# V1 Portal Upgrades — Round 2 status (continuation of memory/portal/v1-upgrades.md)
Date: 2026-11-12. Written separately because Scribe has no read tool to safely append to the intake log (anchor match failed; contents unverified).

## Resolutions
- CONTRADICTION RESOLVED (flagged by Scribe round 1): Mechanic's "nothing listening on :8099/:8888" from Red is retracted as unprovable — container-namespace view (tasklist 0 lines, netstat 0 LISTENING), not evidence the portal is down. Researcher's PID 30852 stands as memory-grounded; live host per Orchestrator = White (White). No agent-side contradiction remains on this point.

## U2 prep (Mechanic)
- u2-probe/probe_hosts.py built: read-only by default, --write-test drops one marker file per share, loads facts from memory/llm/hosts.md (no guessed share names).
- Baseline run from Red: 0/4 hosts reachable (SMB WinError 65 on all four hostnames in 7–83 ms; python sockets allowlist-blocked; powershell policy-blocked), exit 2 as designed.

## Evidence for U2 (visibility asymmetry)
- White (Orchestrator + Researcher): sees uploads/AgentPortal_V1, 41 files verified.
- Black sandbox (Builder + Verifier, C:\Users\black\.unsloth\studio\sandbox\_default): bundle absent; both agents' own artifacts present.
- Red sandbox (Mechanic, C:\Users\Red\...): bundle absent; only 4 files incl. Scribe's intake log.
- => "shared agent folder" is NOT uniformly shared across hosts. Consistent with Orchestrator's topology ruling; five independent negative reports now on record as U2 evidence.

## Open (owner: Orchestrator)
1. Who can materialize uploads/AgentPortal_V1/* into an agent-reachable path (gates U1, U4, and Mechanic's diff/deploy)?
2. Which sandbox has network/SMB access for the U2 probe (Red shows none; White egress status unverified from inside its sandbox)?

## Not-yet-recorded decisions (pending owners)
- U3 /api/fleet DEFERRED until U1+U2 land (Orchestrator ruling, in TODO.md top section).
- U2 bootstrap promoted ahead of U1 implementation (Orchestrator ruling; PULL via /api/file if egress open, else PUSH via known paths).
- Builder position on manifest-or-not: MANIFEST (Files panel reads /api/uploads directly) — pending Archivist's item closure.
