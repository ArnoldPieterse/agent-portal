# TODO.md `## AGENT GOALS` summary section - written 2026-11-23 (Orchestrator)

Continuation of prior pass's remaining work: "Update TODO.md with `## AGENT GOALS` section summarizing the new goals."

What was done
- Added a top-of-file `## AGENT GOALS (summary, set 2026-11-23)` section to TODO.md.
- Per-seat open-goal state compiled from on-disk canonical files in memory/goals/<lane>.md (SSOT):
  - Builder: 5 open (newer dispatched cycle; disk file still holds prior cycle 10/10 reached).
  - Verifier: 10 open / 20 total.
  - Designer: 5 open (newer dispatched cycle; disk file still holds prior cycle 10/10 reached).
  - Researcher: 10 open / 10 total (proposed, none verified yet).
  - Scribe 10/10, Mechanic 9/9, Archivist 20/20, Orchestrator 3/3 all reached.
- Section ordered above the MODE-BUTTON SQUEEZE FIX section (verified idx agent-goals=129 < modebtn=2127).
- Notes it supersedes the two older `## AGENT GOALS` sections (2026-11-13).

Verification
- edit_file replacement applied (1 replacement); file re-read confirms section present and correctly ordered.
- Open-goal titles cross-checked against memory/goals/<lane>.md via regex extract of "N. **Title**" lines + verified-marker scan.

Follow-up (not this pass): Builder.md and Designer.md on-disk files are a fully-reached prior cycle but the live dispatch carries a newer 5-goal open-set each; next pass should land those newer sets into the .md files so disk == dispatch.
