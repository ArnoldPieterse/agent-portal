# Data Integrity Report

Run: 2026-11-20 11:25:30Z

**Summary: 16 issues found**

## ❌ A_agents_json: FAIL

  - duplicate model_id 'Qwen3.8-27B-Q8_0' (agents: {'quinn-q4', 'Qwen3.8-27B-Q8_0', 'atlas-q8'})

## ❌ B_goal_agent_refs: FAIL

  - cycle2-dependency-map.md: references unknown agent 'cycle2'
  - cycle2-kickoff-2026-11-16.md: references unknown agent 'cycle2'

## ❌ C_index_pointers: FAIL
 (387 pointers checked)
  - memory\archivist\INDEX.md: pointer 'archivist/index_check.py' -> file not found
  - memory\builder\INDEX.md: pointer 'icons.js' -> file not found
  - memory\builder\INDEX.md: pointer 'core.js' -> file not found
  - memory\orchestrator\INDEX.md: pointer '46/80' -> file not found
  - memory\orchestrator\INDEX.md: pointer 'memory/orchestrator/execute-engine' -> file not found
  - memory\researcher\INDEX.md: pointer '/api/activity' -> file not found
  - memory\researcher\INDEX.md: pointer '20/20' -> file not found
  - memory\researcher\INDEX.md: pointer 'mirror/allowlist/sandbox' -> file not found
  - memory\researcher\INDEX.md: pointer '2/7' -> file not found
  - memory\researcher\INDEX.md: pointer 'rc0/LOW/WARN' -> file not found
  - memory\researcher\INDEX.md: pointer '12/45' -> file not found
  - memory\researcher\INDEX.md: pointer '74/80' -> file not found

## ❌ D_mirror_py: FAIL

  - memory_mirror.py is EMPTY (0 bytes) - PIN_FILES logic missing
