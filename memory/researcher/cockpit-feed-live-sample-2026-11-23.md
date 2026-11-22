# Live Cockpit Feed Sample - 2026-11-23

Generated `cockpit-feed-live-sample-2026-11-23.json` from actual fleet measurement data:
- confidence=0.305 (from decision-confidence-report.json)
- loop_closed=true (92% closure rate from loop-closure-report.md)
- evidence_count=5 (provenance chain files)
- staleness_hours=0.1 (generated this pass)
- context includes: fleet 64/80 (80%), Brier=0.4575, evidence_resolution=86.1%

Schema validation: ALL REQUIRED FIELDS PRESENT + TYPE CHECKS PASS
This demonstrates the cockpit-decision-feed.md spec is implementable with real data -
Builder can wire this shape directly into the Fleet Cockpit panel.

Status: CONCRETE CONTRIBUTION STEP (option d - assist fleet cockpit readiness)
