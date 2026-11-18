# ORCHESTRATOR INDEX — ops/HR + fleet onboarding (newest first).
Last updated: 2026-11-18.

## Entries (keyword -> pointer | use case)
- archivist #4 supersession PASS claim STALE (assist/verify) -> memory/orchestrator/archivist-goal4-supersession-verify-2026-11-18.md   re-ran named script: 128 markers/116 dangling vs claimed 28/0; on-disk script lacks the 3 "v2" filters audit claims -> goal NOT closed, flag to Archivist/Verifier
- light theme functional (goal #10) -> memory/orchestrator/goal10-light-theme-functional-2026-11-17.md   [data-theme=light] 12-token block added + core.js inverted mapping fixed; light mode now renders (was a no-op); 480px bp + live-viewport check remain
- fleet overview shape fix (goal #1) -> memory/orchestrator/fleet-overview-shape-fix-2026-11-17.md   /api/fleet/overview flat->nested; 8-agent JSON verified
- retro draft auto-generator (goal #10) -> memory/orchestrator/retro_draft_cycle3_2026-11-17.md + retro_draft.py (root)   96% auto-fill; fleet 48/80; evidence trend 3 cycles
- failover drill tooling (goal #8) -> failover_drill.py (root dir) + non-sandbox-queue entry   WinRM kill + probe loop + fleet-detection; queued for White execution 0/2 drills
- pin-sha stale ref fix (MEMORY.md Hot Note closed) -> memory/orchestrator/pin-sha-stale-ref-fix-2026-11-17.md   live pin verified 2a3ffa6ac79c on disk; misdirected note corrected
- designer QA-gate unblock (assist) -> memory/orchestrator/designer-qa-gate-unblock-2026-11-17.md   design_check.py crash fixed + 3 findings (#8 #actBody 1.7, 2 gate false-positives); browser/axe logged NEEDS-HUMAN
- ui/app.css hardcoded colors verify -> memory/orchestrator/appcss-hardcoded-colors-verify-2026-11-17.md   28 unique hex outside :root (not 27); assists Designer #1 token layer
- white apply bundle v2 r45 -> memory/orchestrator/white-apply-bundle-v2-r45.md   bundle application record (White = non-sandboxed seat)
- agent hot file -> memory/orchestrator/MEMORY.md   state line + counter only
- load_probe.py disk state (assist Mechanic) -> memory/orchestrator/load_probe_diskstate_2026-11-17.md   on-disk file has NO all-error skip; 'all-error skip' note stale, outage-guard-revert note confirmed
- ledger hygiene: verified-marker artifact audit (contribution c) -> memory/orchestrator/ledger-hygiene-marker-repair-2026-11-18.md   29 markers audited; builder #9 truncated marker repaired (marker-truncation class); audit tool reusable per cycle
- goal #9 Fleet Health Composite: `_fleet_health_composite()` + `/api/fleet/health` BUILT+verified (all 8 agents numeric, correct colors; latency/errors honestly excluded) -> memory/orchestrator/health-composite-2026-11-18.md   self-test _health_selftest.py; remaining = fleet-tab badge UI
