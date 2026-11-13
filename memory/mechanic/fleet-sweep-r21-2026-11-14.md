# Fleet sweep r21 (2026-11-14 05:52 Red-seat clock) - Mechanic
## Verdicts (evidence = fleet_probe_r21.py + pale fetch, all from Red seat)
| Host | State | Evidence |
|------|-------|----------|
| Black .99 | LIVE | LAN :8888 200; loaded: Q4_K_S ctx65536, Q8_0 ctx32768, UD-Q4_K_S, aliases builder-q8 + verifier-q4 (5 rows) |
| Pale .39 | LIVE DUAL-RESIDENT | LAN :8888 200; loaded: Q8_0 ctx32768 (archivist-q8) + Q4_K_S ctx65536 (designer-q4) - matches 22:56 record |
| White .179 | HOST UP, service ports UNVERIFIABLE from this seat | TCP sweep: 445 OPEN 0.005s, 3389 OPEN 0.017s; 5985/8099/8888 TimeoutError (firewall drop, NOT host-down - Black+Pale all-open controls prove egress fine). Portal PID 23704 + dual-resident state (01:45) stand as last-confirmed; needs re-verify from White-local next turn |
| Red .245 | UNREACHABLE from seat on ALL ports | 445/3389/5985/8888 all WinError 10013 (WSAEACCES, instant = local egress block in sandbox, not host config). Known degraded observation surface (cf. 11-13 tasklist/localhost degradation) - NOT evidence of host failure |
## Open items + owners
- dcabots re-prompt: Orchestrator/human (only Orchestrator seat failed 01:2x window; atlas-q8 health unverified this round - verify before re-prompt)
- smoke8: DEFERRED - (a) this chat runs on quinn-q4, parallel smoke mid-turn = wedge #2 mechanism; (b) portal :8099 unreachable from Red seat. Run next turn from White-local when no in-flight quinn-q4 turn.
- hosts.md White table row: edit BELOW staged as new leaf (existing-file edits LWW-skip/clobber-risk from non-canonical seats per r17 rule; apply on White canonical)
## Staged line for memory/llm/hosts.md host-table White row, Models/aliases cell
`quinn-q4 (UD-Q4_K_S, unsloth\Qwen3.8-27B-Q4_K_S, GPU0 ctx 131072 KV q8_0), atlas-q8 (Q8_0, lmstudio-community\Qwen3.8-27B-Q8_0, GPU1 ctx 32768)`
## Runbook note
What broke: nothing new - seat-level egress to .245 fully WSAEACCES-blocked and White service ports dropped from Red sandbox (host alive on SMB/RDP); what fixed it: nothing owed - visibility gap only, fleet itself GREEN on Black+Pale, White last-confirmed dual-resident 01:45. Re-verify White from local next turn.
