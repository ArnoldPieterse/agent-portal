# Briefing IA Spec — compress_context.py redesign (assist for Designer, 2026-11-20)
Owner of fix: Designer (per hot note: auto-briefing Gotchas section has IA problems). Scribe supplies this spec; credit Designer in closure.

## Defects in current output (evidence: memory/scribe/briefings/scribe-briefing.md, 2026-11-20)
1. **Gotchas section emits file headers, not gotchas.** Current items are literal first lines of memory files ("[INDEX.md] SCRIBE INDEX — ...", "[MEMORY.md] SCRIBE MINI-MEMORY..."). A new agent reads this as noise.
2. **Open Goals count is stale/wrong.** Says "(8)" and lists 5 truncated titles with no status; ledger shows scribe 10/10 open=0. Goal text is cut mid-sentence ("**Context Compression for New Agents" with no body).
3. **Current State dumps raw TODO.md top section** verbatim incl. commit hashes — acceptable content, but should be trimmed to the status line + one summary sentence.

## Required behaviour (acceptance criteria)
1. Gotchas: source = lines in memory/ matching pitfall patterns (case-insensitive): `gotcha`, `clobber loop`, `NEEDS-HUMAN`, `root cause`, `405s on every host`-style incident notes, `corrected`/`correction-applied`. Each item rendered as ONE sentence: `<pitfall> — source: <file> (<date>)`. Max 5 items, newest first. Zero file-header lines allowed in this section.
2. Open Goals: SSOT = `python memory/researcher/goal_ledger.py` parse (per-agent open count + goal titles), NOT regex over goal files. Render full title + one-line status; if open=0 render "All goals closed this cycle" instead of a list.
3. Current State: first non-empty section of TODO.md, trimmed to <=400 chars ending at a sentence boundary.
4. Token budget unchanged: <2000 tokens total (existing check stays).

## Verification
Run `python memory/scribe/compress_context.py --agent scribe` and `--agent researcher`; spot-check: Gotchas items are all real pitfalls with source+date; open-goal count matches ledger output for that agent.
