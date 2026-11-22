# Memory Compression Report
Generated: 2026-11-23 08:00
Scanned: 2534 .md files in memory/
Redundant claims (3+ locations): 5

## Findings and Consolidation Proposals

### port: [8099] (35 locations)
- Canonical source: memory/ops/network-config.md (canonical port assignments)
- Current duplicates:
  - memory/ONBOARDING.md
  - memory/builder/fleet_health_dashboard_2026-11-18.md
  - memory/builder/portal-startup-fix-2026-11-17.md
  - memory/goals/mechanic-forecast-recovery-matrix.md
  - memory/goals/verifier.md
  - memory/mechanic/auto-restart-goal2-closure-2026-11-18.md
  - memory/mechanic/designer-assist-fleet-spec-2026-11-17.md
  - memory/mechanic/goal1-root-cause-relative-path-2026-11-23.md
  - memory/mechanic/goal4-load-probe-remote-upgrade-2026-11-17.md
  - memory/mechanic/goal4-pipeline-validation-2026-11-17.md

Action: Consolidate into canonical source; replace others with pointer.

### residency: [white] (6 locations)
- Canonical source: memory/fleet/residency-matrix.md (model-to-host bindings)
- Current duplicates:
  - memory/goals/cycle2-kickoff-2026-11-16.md
  - memory/ops/black-studio-failover-2026-11-16.md
  - memory/orchestrator/goal8-event-stream-3events-verified-2026-11-18.md
  - memory/researcher/model-residency-study-2026-11-17.md
  - memory/scribe/cycle-narrative-discrepancy-resolved-2026-11-18.md
  - memory/goals/archive/cycle2-2026-11-17/cycle2-kickoff-2026-11-16.md

Action: Consolidate into canonical source; replace others with pointer.

### port: [2026] (5 locations)
- Canonical source: memory/ops/network-config.md (canonical port assignments)
- Current duplicates:
  - memory/archivist/decay-report.md
  - memory/archivist/freshness-report-2026-11-20.md
  - memory/archivist/freshness-report.md
  - memory/designer/timeline-panel-spec-2026-11-21.md
  - memory/researcher/failure-mode-indicators-2026-11-16.md

Action: Consolidate into canonical source; replace others with pointer.

### resource: [24] (4 locations)
- Canonical source: memory/fleet/residency-matrix.md (hardware specs)
- Current duplicates:
  - memory/goals/archivist.md
  - memory/goals/researcher.md
  - memory/llm/hotload-selector.md
  - memory/goals/archive/archivist-2026-11-23-cycle9.md

Action: Consolidate into canonical source; replace others with pointer.

### port: [5985] (3 locations)
- Canonical source: memory/ops/network-config.md (canonical port assignments)
- Current duplicates:
  - memory/goals/designer-forecast-mechanic-winrm-2026-11-20.md
  - memory/goals/forecast-mechanic4-reboot-recovery-2026-11-18.md
  - memory/mechanic/goal4-dryrun-status-2026-11-18.md

Action: Consolidate into canonical source; replace others with pointer.

## Compression Impact
- Removing redundant restatements saves ~48 lines across the tree.
- 5 facts would each have a single canonical home.
