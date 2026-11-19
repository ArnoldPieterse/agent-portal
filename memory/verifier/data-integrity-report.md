# Data Integrity Report

Run: 2026-11-19 17:00:32Z

**Summary: 14 issues found**

## ❌ A_agents_json: FAIL

  - duplicate model_id 'Qwen3.8-27B-Q8_0' (agents: {'atlas-q8', 'Qwen3.8-27B-Q8_0', 'quinn-q4'})

## ❌ B_goal_agent_refs: FAIL

  - cycle2-dependency-map.md: references unknown agent 'cycle2'
  - cycle2-kickoff-2026-11-16.md: references unknown agent 'cycle2'

## ❌ C_index_pointers: FAIL
 (339 pointers checked)
  - memory\archivist\INDEX.md: pointer 'archivist/index_check.py' -> file not found
  - memory\builder\INDEX.md: pointer 'icons.js' -> file not found
  - memory\builder\INDEX.md: pointer 'core.js' -> file not found
  - memory\orchestrator\INDEX.md: pointer 'memory/orchestrator/execute-engine' -> file not found
  - memory\researcher\INDEX.md: pointer 'mirror/allowlist/sandbox' -> file not found
  - memory\researcher\INDEX.md: pointer '2/7' -> file not found
  - memory\researcher\INDEX.md: pointer 'rc0/LOW/WARN' -> file not found
  - memory\researcher\INDEX.md: pointer '12/45' -> file not found
  - memory\researcher\INDEX.md: pointer '74/80' -> file not found
  - memory\verifier\INDEX.md: pointer 'memory/verifier/THIS_FILE_DOES_NOT_EXIST_12345.md' -> file not found

## ❌ D_mirror_py: FAIL

  - memory_mirror.py is EMPTY (0 bytes) - PIN_FILES logic missing
