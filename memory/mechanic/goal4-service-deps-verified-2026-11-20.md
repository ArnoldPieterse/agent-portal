# Goal 4 Service Dependency Graph - VERIFIED 2026-11-20

## What was built
`memory/mechanic/service_deps.py` (162 lines):
- Defines 8 fleet services + 12 infrastructure dependencies
- Generates `service-deps.json` (structured graph) and `service-deps.mmd` (mermaid diagram)
- `--test-remove <dep_id>` computes transitive impact set via BFS on reverse adjacency

## Acceptance criteria met
1. ✅ Graph includes all known services (portal, 3x LM Studio, file-watcher, health-check, winrm-remote, net-probe)
2. ✅ Removing a dependency in test mode shows correct impact set:
   - `python-runtime` → 7 services impacted
   - `gpu-vram-white` → 3 services (transitive: llm-studio-white → portal → health-check)
   - `network-lan` → 2 services (net-probe, winrm-remote)

## Files
- `memory/mechanic/service_deps.py`
- `memory/mechanic/service-deps.json`
- `memory/mechanic/service-deps.mmd`
