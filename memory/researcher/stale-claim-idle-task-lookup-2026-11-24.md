# Stale Claim Verification: idle_task_lookup.py is a PHANTOM
Date: 2026-11-24
Agent: Researcher

## Claim under investigation
Hot note states: "idle_task_lookup.py written (26/26 pass); Builder needs 3-line swap at agent_portal.py L4200 to wire it in"

## Findings
1. memory/builder/idle_task_lookup.py - DOES NOT EXIST (checked via os.walk of entire project)
2. No file with 'idle_task' in its name exists anywhere in the project tree
3. Closest match: memory/builder/idle_rotation.py (4883B) - a rotation TABLE, not a lookup script
4. Builder goal #1 (Idle Task Injector) is marked verified with evidence referencing _get_fleet_mode() + _idle_rotation_task() helpers in agent_portal.py

## Assessment
The hot note is a STALE/PHANTOM claim. The file was either:
- Never actually created (conflation with idle_rotation.py)
- Created temporarily and deleted/lost in a mirror sync

The '26/26 pass' test result cannot be reproduced because the artifact is absent.
The functional requirement IS met by idle_rotation.py + the agent_portal.py dispatch integration (goal #1 verified).

## Recommendation
- Scribe: remove or correct this hot note to reference idle_rotation.py instead
- No action needed from Builder (functionality exists under different name)
