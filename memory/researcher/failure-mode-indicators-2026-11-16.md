# Researcher — failure-mode prediction from logs (goal #4, first report 2026-11-16)

Method: mined ALL runs/*.journal (11-13..11-16) for inter-frame gaps >90s per agent, correlated with nudge/auto-continue events. Raw miner output kept inline below; feed to Mechanic#1 adaptive probe as the "leading indicators" input named in that goal.

## Ranked leading indicators
1. **Cluster of >90s gaps across >=2 agents in one pass** — strongest stall predictor: every run that received a nudge (9 nudges total) had multiple such gaps first. 93 gaps >90s found fleet-wide; the three most-nudged runs (g-...66d42d, g-...727470, g-...7ebd18) each had 24-26 of them. *Action for Mechanic#1: WARN when 2+ agents gap >90s in the same pass window.*
2. **Repeated per-pass gaps on ONE specific agent (>=3 consecutive passes)** — dead-seat signature, not a wedge: Orchestrator and Researcher show exactly this today (22 gaps each, the fleet max), matching their 404 not_loaded meta-frames. A wedge silences ALL agents on a host simultaneously (11-15 17:52 incident); a dead seat only its own agent. *Action: CRIT + auto-HOTLINE H-MODEL when one agent gaps >=3 consecutive passes.*
3. **Max-gap magnitude >300s** — all top-12 gaps today were 317-591s and preceded either a nudge or an auto-resume chain. Sub-120s single gaps are mostly benign slow generation (resumed without intervention). *Action: WARN threshold 300s, CRIT 480s.*
4. **Journal mtime frozen while run_state says busy** — the classic wedge signature from the 11-15 incident (journal frozen + GPU idle); today's data adds: it co-occurs with indicator 1 across agents. *Action: keep as the existing stall-killer trigger; add the gap-cluster as an EARLIER warning so recovery can start before the hard kill.*

## Data
- Gaps >90s total: 93 | nudges observed: 9
- By agent (gap counts): Researcher 22, Orchestrator 22, Designer 12, Verifier 12, Archivist 7, Builder 7, Mechanic 6, Scribe 5
- Largest today: 591s (Researcher+Orchestrator, run g-...a0b02c @14:43 — the two dead seats), 513s Designer, 504s Archivist, 499s Scribe
- Runs with both big gaps AND nudges: 66d42d (25 gaps, max 405s), 727470 (24, max 463s), 7ebd18 (26, max 242s)

Confidence: HIGH for indicators 1-2 (direct correlation in this dataset + two independent incident records); MEDIUM for threshold values (single-fleet sample).
