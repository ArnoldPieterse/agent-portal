# Idle-Time Maintenance Rotation - 2026-11-24 (Orchestrator)

## Problem
When all agents reach 100% goals, auto-loop passes dispatch the generic menu:
"pick one of (a)(b)(c)(d)". Result: low-productivity passes where agents reply
[CONCLUDED] after minimal work. Evidence: autoloop.json last_pass.productive=false.

The system wastes ~60-300s per agent per pass on idle cycles that produce no file
changes, measurements, or evidence. Over a 4-hour idle window this is 20-80 wasted
agent-passes per seat.

## Proposed Fix: Per-Role Maintenance Task Table
Replace the generic (a)(b)(c)(d) menu with a concrete task table. Each agent gets
ONE specific task per idle pass, rotated daily. Tasks are short (<2 min), produce
a measurable output, and feed data back into the cockpit.

| Role | Mon-Task | Tue-Task | Wed-Task | Thu-Task | Fri-Task |
|------|----------|----------|----------|----------|----------|
| Orchestrator | Validate agents.json aliases resolve (probe each model endpoint) | Check TODO.md sync with /api/goals SSOT | Review blocker log for stale entries >72h | Audit goal files for format consistency | Generate fleet placement snapshot + diff vs prior day |
| Researcher | Run KB freshness scan, flag leaves >3d stale | Cross-check 5 random citations in decision-log.jsonl | Update open-questions log with any newly answerable items | Verify dictionary_*.json coverage of last cycle's key terms | Measure retrieval accuracy on 3 held-out queries |
| Verifier | Run one regression self-test from prior cycle (pick oldest) | Check evidence leaves for phantom artifact paths | Validate that /api/fleet/cockpit response <5s | Run pointer integrity check (dangling/orphan/stale) | Spot-check 3 random verified claims against their artifacts |
| Scribe | Compress last auto-loop pass into 1-line decision + open items | Check runbooks for stale commands (do they still match current file layout?) | Update memory/scribe/MEMORY.md hot state | Review cross-talk for unresolved questions needing synthesis | Generate a 3-sentence "state of the fleet" summary |
| Designer | Run WCAG contrast check on cockpit panels (wcag_contrast_check.py) | Check UI asset inventory for orphaned files in ui/ | Validate that app.css custom properties are all referenced | Screenshot 1 viewport, flag layout overflow issues | Review recent UI changes for consistency with design tokens |
| Builder | Run one self-test from a prior cycle script (verify still passes) | Check git status: any uncommitted changes >24h old? | Validate that /api/fleet/cockpit endpoint responds <3s | Scan for TODO/FIXME comments in code files not tracked as goals | Verify model-swap scripts still work (dry-run mode) |
| Archivist | Run kb_delta.py, verify output is valid JSON + <2KB | Check citation integrity: 5 random pointers resolve | Run freshness heatmap, flag any dir >3d stale | Validate knowledge-index.json fact count matches prior day +/-5% | Check auto-linker: are new leaves getting links? |
| Mechanic | Probe all 4 hosts (ping + port check), log results | Check load-trend for anomalies vs baseline | Validate elev.py helper is responsive (<2s ping) | Review schtasks snapshot: any tasks failing >3 consecutive runs? | Run fleet_probe_v2.py, compare to prior snapshot |

## Implementation
The auto-loop dispatch code (in agent_portal.py, _autoloop_behaviour_hint or the
task-assignment section) should:
1. On idle pass, look up the agent's role + current weekday from this table
2. Inject the specific task text into that agent's @Name section instead of the generic menu
3. After the pass, check if the agent produced a file change or measurement (productive=true/false)
4. If productive=false 3 consecutive times on the same task, escalate: write an OPS-NOTE

## Expected Impact
- Productive idle passes increase from ~10% to >70%
- Continuous low-cost monitoring replaces periodic batch checks
- Data accumulated during idle feeds directly into next-cycle goal proposals
- No new infrastructure needed; just a lookup table + one code change in dispatch

## Verification
After implementation: run 3 consecutive auto-loop passes during an all-idle window.
Confirm: (1) each agent received its specific task from the table, (2) at least 6/8
agents produced productive=true, (3) at least 2 new files or measurements appeared.

## Status
SPEC - ready for Builder to implement in agent_portal.py dispatch logic.
