# OPS INDEX — index of indexes for Windows ops & verification.
Last updated: 2026-11-15.

## Entries (keyword -> pointer | use case)
- reboot / auto-start / RecoverAll / PortalRun / ground-truth checks / Windows quirks -> memory/ops/windows-runbook.md   post-reboot recovery order + portal lifecycle rules
- probe scripts / schtasks / e2e / result files / detached workers / stale chain summaries / hash-verify copies -> memory/ops/probes.md   verification tooling inventory (what each script proves)
- PDF reports / fpdf2 / _gen_report.py pattern / report layout pitfalls / PNG verify step -> memory/ops/pdf-reporting.md   Archivist's repeatable PDF-reporting recipe
- MEMORY.md trim 2026-11-14 / pre-trim content archive / lossless hot-file shrink -> memory/ops/memory-trim-archive-2026-11-14.md   full pre-trim MEMORY.md (8,042 B) preserved verbatim

## Global pointers
- -> agent_portal.py  server;  -> MEMORY.md hot state;  -> TODO.md plan
- daily health check / PID + :8099 listener + /api/git reachability / .gitignore allowlist audit -> memory/ops/verifier-healthcheck-2026-11-15.md   2026-11-15: all OK; junk untracked (430->417)
- git hygiene / commit conventions / commit-only-after-verification / no secrets in git -> memory/ops/git-hygiene.md   2026-11-14 Archivist: message convention + rules
- host port + task map / 4 hosts / PortalRun + daily git + fleet probe tasks -> memory/ops/host-port-task-map-2026-11-15.md   White verified live; remotes from hosts.md recon (pending power-on)
- 4-host probe / every-10min schtask / failure log -> fleet_probe.py (root)   PortalFleetProbe task; failures + hourly OK to fleet_probe.log
- AC V-09 provenance determinism / goal_provenance.py two-run md5 test / generated field tree-derived -> memory/ops/verifier-ac-v09-2026-11-15.md   FAIL->fixed->PASS 2026-11-15 (wall-clock timestamp was the only nondeterminism)
-> ops/left-orchestrator.md  orchestrator goals - 7/8 closed with evidence 2026-11-14; goal 4 drill verdict pending (SwapDrill1114)
-> ops/left-researcher.md  7 open goals (researcher) - split from what_is_left.txt 2026-11-13
-> ops/left-builder.md  4 open goals (builder) - split from what_is_left.txt 2026-11-13
-> ops/left-archivist.md  8 open goals (archivist) - split from what_is_left.txt 2026-11-13
-> ops/left-scribe.md  10 open goals (scribe) - split from what_is_left.txt 2026-11-13
-> ops/left-verifier.md  3 open goals (verifier) - split from what_is_left.txt 2026-11-13
-> ops/left-designer.md  1 open goals (designer) - split from what_is_left.txt 2026-11-13
-> ops/left-mechanic.md  9 open goals (mechanic) - split from what_is_left.txt 2026-11-13
-> memory/ops/fleet-state-2026-11-15.md  fleet state change (Red .245 UP idle no-models; Pale/Black down) + 5 planned portal restarts (~10 s each, PID 7032) + /api/fleet 5s-budget fix record 2026-11-15
-> memory/ops/public-repo-agent-portal-2026-11-15.md  PUBLIC repo live (ArnoldPieterse/agent-portal); hosts.md untracked+INTERNAL_ONLY mirror; tracked files = public, no secrets; ~50 files w/ LAN IPs pending human scrub decision

## 2026-11-16 (cycle-2 kickoff)
- -> memory/ops/risk-register-cycle2.md | milestone risk register (O5, living doc)
- -> memory/ops/hotline-v2.md | HOTLINE protocol v2 + exercise log (M1 model residency, M2 Black down, R1 Red :8099)
