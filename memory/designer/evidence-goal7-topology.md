# Goal 7 — Fleet Topology Live Graph (REACHED 2026-11-23)
Artifact: ui/cockpit-topology.js (8847 chars)
Criteria:
- [x] 4 hosts render at correct relative positions (layout() places by index left-to-right)
- [x] Simulated host-down desaturates node within 500ms (simulateDown() adds .ct-node--down class; CSS transition on fill .4s)
- [x] Agent reassignment shown as edge re-routing (reassign() updates data-target + adds .ct-agent-edge--routed)
- [x] Graph legible at 768px simplified mode (isSimple() checks window.innerWidth <= 768, hides labels, shrinks viewBox)

Spec: Self-contained SVG, no deps. Data from /api/fleet with SAMPLE fallback.
Auto-init on #fleetTopo element. Live poll 30s. Resize-aware.
