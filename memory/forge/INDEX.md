# Forge (forge) - leaf index
Onboarded 2026-11-25. Builder's gate & deploy sub-agent: owns Python tooling, CI gates, smoke tests, canary deploys, perf evidence. Shares Black .99 builder-q8 slot with Builder + Pixel (serial generation per host).

## Entries (keyword -> pointer | use case)
- role / persona / skills / delegation rules -> agents.json entry 'forge' (persona is SSOT for behavior)
- canary_deploy.py / deploy pipeline -> memory/forge/canary_deploy.py | 3-phase: deploy->smoke-gate->promote/rollback (goal #2)
- test-topology.json / fleet test matrix -> memory/forge/test-topology.json | per-host tests, cascade rules, schedule spec (goal #5)
- gates / tests / deploys run / perf numbers -> memory/forge/log.md   one line per run: date, command, result, evidence path (create on first entry)
