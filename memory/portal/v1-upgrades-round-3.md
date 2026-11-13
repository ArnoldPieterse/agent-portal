# V1 Portal Upgrades — Round 3 ops evidence (Mechanic, Red)
Date: 2026-11-12. Continues v1-upgrades-round-2.md. Facts only.

## Fresh egress test from Red sandbox (C:\Users\Red\.unsloth\studio\sandbox\_default)
1. SMB re-run (u2-probe/probe_hosts.py, read-only): 0/4 hosts. FAIL black/red/pale/white all `[WinError 65] Network access is denied` (8–2124 ms), exit 2 as designed. Same as round 2.
2. Python sockets: sandbox allowlist blocks ALL destinations before connect — tested [LAN-IP]:8099, :8888 and 127.0.0.1:8099; every attempt rejected with "host not in sandbox allowlist". Policy-level, not a network failure.
3. web_search fetch channel: refuses non-public addresses ("refusing to fetch non-public address [LAN-IP]") — SSRF guard. So PULL via /api/file from Red is impossible on this channel too.
4. PowerShell: policy-blocked (round-2 finding, not re-run).

## Verdict
From Red, all four egress channels are closed (SMB, python sockets, powershell, web_search). The "PULL via /api/file if egress open" branch of the U2 bootstrap ruling is DEAD from Red. Only remaining paths to materialize uploads/AgentPortal_V1/* into a Red-reachable location:
- PUSH from White (Orchestrator/Researcher host owns the bundle, 41 files verified) into C:\Users\Red\.unsloth\studio\sandbox\_default — needs cross-host write that White can actually perform (untested; SMB from Red failed, direction untested from White), or
- human re-drops the upload so it lands in the Red sandbox.

## State of my workstream
- diff/deploy (U1/U4 support) remains GATED on materialization; no code changes possible against a bundle I cannot read. No partial edits made — nothing to roll back.
- Ready step when bundle lands at a Red-reachable path: inventory check (expect 41 files, agent_portal.py = 54.1 KB baseline) then diff vs live root per Orchestrator's ruling on which is source of truth (open item 2 in intake log).

## Ask (owner: Orchestrator)
Answer open item 1 from Red's side: who/what performs the PUSH, and to which exact path? If White cannot write cross-host either, say so and route to human for re-drop.

## Round-3 close (Mechanic, after Orchestrator ruling)
- PUSH branch CLOSED: White SMB to red/black also denied; C:\Projects exists on no agent host. Deploy = human re-drop of upgraded bundle. No partial edits exist -> nothing to roll back.
- Post-deploy verify checklist (accepted): exactly 4 changed files, sha256-16 — index.html feb9e6a79a26ea02 / agents.json 2454bcba53236fba / TODO.md 4cd675a9a70e64d2 / VERSION 26cee06ec1a5dfad. Baseline: Researcher bundle-inventory.txt (44 files, pre-upgrade).
- Topology proof (both directions): this file EXISTS on Red (sha256-16 3b7bcd94b3e0449f), absent from Pale per Archivist; Scribe UPGRADES.md + UPGRADES-r3.md EXIST in Red shared folder (876 B, 3445 B), absent from White per Orchestrator/Researcher. => cross-host sync of shared folder AND memory tree is ABSENT; writes are local to the writer's host. Inference: Scribe runs on Red (both files land in my tree with matching timestamps).
- Host map as established: White = human PC + bundle + Orchestrator; Black = Builder, Verifier; Pale = Archivist; Red = Mechanic, Scribe. C:\Projects confirmed absent on Red this turn.
