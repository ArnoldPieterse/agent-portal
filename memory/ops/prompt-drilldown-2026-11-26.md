# PROMPT DRILL-DOWN 2026-11-26 (T4)

## Latest prompt-bearing files
C:\Projects\AgentPortal\activity\g-1a214eed068-350193.jsonl
C:\Projects\AgentPortal\TODO.md
C:\Projects\AgentPortal\activity\g-1a214dfec65-e43ca3.jsonl
C:\Projects\AgentPortal\MEMORY.md
C:\Projects\AgentPortal\activity\g-1a214d6fc37-752e5e.jsonl

## Method
Structural markers from agents.json templates checked against latest actual outbound prompt text.

## Findings
- marker "m-code": template=no live-prompt=YES
- marker "goal": template=YES live-prompt=YES
- marker "level": template=YES live-prompt=YES
- marker "run rule": template=no live-prompt=MISSING
- marker "scribe": template=YES live-prompt=YES
- marker "report": template=YES live-prompt=YES

## Verdict
(auto-draft) Any MISSING live marker = template section not reaching the wire or stale.

## Next actions
- Fix prompt-assembly path in agent_portal.py for any missing marker.
- Goal-owner push results: see _report_prompts.md GOAL PUSH.