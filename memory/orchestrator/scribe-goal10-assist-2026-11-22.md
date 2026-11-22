--- Orchestrator assist - Scribe goal #10 (Per-Agent Weekly Digest) ---  
  
Added --agent flag to memory/scribe/weekly_summary.py.  
  
Functions added: get_agent_goals, get_agent_decisions, get_agent_blockers, get_agent_handoffs, generate_agent_digest.  
CLI: python memory/scribe/weekly_summary.py --agent <name> [YYYY-MM-DD].  
  
Verified: ran for all 8 agents, all produced files (weekly-2026-W47-<agent>.md). Spot-checked orchestrator/builder/mechanic - no cross-agent contamination. Each has >=3 items.  
  
