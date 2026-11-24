# Idle Task Injector - Evidence (2026-11-24)

## What was done
Modified agent_portal.py dispatch logic to inject role-specific maintenance tasks
from the idle-maintenance-rotation table when fleet_mode is MAINTENANCE or IDLE.

## Changes
1. **agent_portal.py L4033-4070**: Added `_read_fleet_mode()` and `_idle_task_for_role()` helper functions + `_IDLE_ROTATION` dict (8 roles x 5 tasks)
2. **agent_portal.py L4232-4235**: Modified the maintenance dispatch branch to check fleet mode; when MAINTENANCE/IDLE, injects specific rotation task; when WORK, keeps generic menu

## Verification
- `memory/builder/test_idle_task_injector.py`: 17/17 PASS
  - Mode reader returns valid enum values
  - All 8 roles get distinct tasks per day
  - Unknown role -> fallback message
  - MAINTENANCE/IDLE -> specific task in dispatch body
  - WORK -> generic menu preserved

## Artifact paths
- agent_portal.py (modified)
- memory/builder/test_idle_task_injector.py (new test file)
- memory/goals/builder.md (goal marked reached)
