# Fleet Topology (Designer goal #9) - 2026-11-17

Live SVG fleet topology in the Fleet panel: ui/fleet_topology.js (new module, header pointer per file-modularity rule),
CSS appended to ui/app.css (all values via existing :root tokens, 0 new hex literals), mount node #fleetTopo + script tag
in index.html (pin advanced same turn: memory_mirror.py index.html sha12 815d64fa70b5).

Renders per host: name, IP, agent count, generation count, status dot; per-agent rows with role + load state.
Data source: /api/health/fleet (Mechanic #8) - no new endpoint.

Evidence (CDP headless Edge 157, d9_d7_verify_20261117.py):
- svg rendered, 40 nodes; hosts: Portal :8099 (local), IP_PALE (2 agents/0 gen), IP_RED (2 agents/1 gen)
- console errors 0, page exceptions 0
- axe-core: 0 violations on repeatable loads (one transient nested-interactive x2 seen once on first load only; not reproducible in 2 follow-up runs incl. goals+fleet panels open)
- landmarks nav/main/aside/header = 1 each; 10 aria-labeled elements; 15-step Tab chain all :focus-visible with visible outline
- screenshots: evidence_d9_fullpage.png, evidence_fleet_topo.png; data: evidence_d9d7.json, evidence_axe_detail.json

Also this turn (Designer #5): design_breakpoint_check.py live run PASS 375px + 768px, 0 horizontal overflow
(log breakpoint-run-20261117.txt).
