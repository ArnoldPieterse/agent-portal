# Host Recovery Matrix
Updated: 2026-11-18. Covers White, Black, Red, Blue.

## White (primary; portal + memory root)
1. Check port 8099: `netstat -ano | findstr :8099` → expect LISTENING.
2. If down: `python agent_portal.py &` → wait 10s → re-check port.
3. Check disk: `wmic logicaldisk where caption='C:' get FreePercent` → expect <85%.
4. Check memory_mirror.py last run: tail memory/memory_mirror.log for errors.
5. Verify /api/goals returns 200: `curl -s -o nul -w "%%{http_code}" http://localhost:8099/api/goals`.
6. If mirror stuck: kill + restart `python memory_mirror.py` → confirm next cycle completes.
Expected recovery: <30s (portal), <2min (mirror).

## Black (LLM host; dual-residency secondary)
1. Check LLM alias reachability: portal /api/agents → all 8 model_ids respond.
2. If one agent down: check process list for its runner → restart via `python elev.py --shell "taskkill /F /PID <pid>"` then relaunch.
3. Verify no zombie processes: `tasklist | findstr python` → count matches agents.json entries.
4. Check log rotation: ls -la memory/*.log → none >10MB.
5. If disk pressure: run `python memory/mechanic/disk_monitor.py --clean`.
Expected recovery: <60s (single agent), <3min (full fleet reload).

## Red (build/test; Builder + Verifier seat)
1. Check build artifacts current: ls -la index.html ui/*.js → timestamps within last mirror cycle.
2. If stale: trigger mirror sync `python memory_mirror.py --once` → verify files updated.
3. Run contract test: `python memory/verifier/contract_test.py` → all pass.
4. Check for orphaned temp dirs: `dir /s /b __pycache__ | find /c /v ""` → clean if >100.
5. Verify no lock files blocking: `dir *.lock 2>nul` → remove stale ones (>1h old).
Expected recovery: <60s (stale sync), <3min (full rebuild).

## Blue (research; Archivist + Researcher seat)
1. Check KB search endpoint: `curl -s http://localhost:8099/api/kb/search?q=test` → 200 + JSON.
2. If RAG host unreachable: check network `ping <rag_host>` → if down, log NEEDS-HUMAN.
3. Verify dictionary files intact: `dir memory\researcher\dictionary_*.json` → all present, non-zero size.
4. Check stale entries: `python memory/researcher/stale_check.py --report` → no critical flags.
5. If disk pressure from research cache: clean temp/ >7d old files.
Expected recovery: <30s (endpoint check), <5min (full KB rebuild).

## Escalation
- Any host down >5min after auto-recovery: write NEEDS-HUMAN to memory/ops/blockers.md with exact command + error.
- Two hosts down simultaneously: treat as fleet incident → generate post-mortem skeleton via `python memory/mechanic/postmortem_gen.py`.