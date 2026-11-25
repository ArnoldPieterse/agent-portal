# Fleet Convergence Glossary

_Plain-language definitions of fleet convergence terms for human readers. Updated as new terms are introduced._

Last updated: 2026-11-25 | Terms: 18

---

## A

### Autonomy Score
**Definition:** A 0-100 number measuring how much work the fleet completes without human involvement. Higher means more self-sufficient.
**Example:** "The autonomy score is 69.1, meaning roughly 7 in 10 passes complete without anyone touching them." *(Source: memory/ops/autonomy-score.json)*

### Auto-Loop
**Definition:** The scheduler that wakes idle agents on a timer and gives them their next task, so the fleet keeps working between human check-ins.
**Example:** "The auto-loop dispatched Scribe at 14:02 after detecting 302 seconds of idleness."

## C

### Convergence
**Definition:** The process by which the fleet moves from needing frequent human direction toward operating steadily on its own — fewer interventions, more consistent output.
**Example:** "Cycle 17's theme is Fleet Autonomy Convergence: we're measuring how close we are to zero-touch operation."

### Cycle
**Definition:** One planning-and-execution round for the fleet. Each cycle has a theme, a set of goals per agent (typically 10 each), and a closeout report.
**Example:** "Cycle 16 ran from 2026-11-24 to 2026-11-25 and closed at 5% completion due to seat unavailability."

## D

### Dispatch Queue
**Definition:** The ordered list of pending goals the scheduler feeds to agents. When an agent finishes a goal, the next one in queue is assigned automatically.
**Example:** "Scribe's dispatch queue shows Cycle Closeout v3 as the next item with a 46% probability of completion this pass."

## F

### Fleet Mode
**Definition:** The fleet's current operating state — WORK (actively producing), MAINTENANCE (consolidating, no new work), or IDLE (dormant, low power). Mode transitions are automatic based on goal completion and idle time.
**Example:** "Fleet mode is WORK at 82.5% goal completion; it will shift to MAINTENANCE when all goals close."

## G

### Goal Ledger
**Definition:** The single source of truth for which goals are done. A goal counts as 'reached' only when a verified evidence marker exists in the ledger — chat claims don't count.
**Example:** "The goal ledger shows 71/80 fleet goals reached; Scribe's lane has 5 new verified entries from this pass."

## H

### Human Intervention
**Definition:** Any point where a human had to step in to redirect, unblock, or approve fleet work. Tracked per cycle to measure convergence progress.
**Example:** "Cycle 16 logged 2 interventions: one redirect (prioritize steady-state) and one approval (Playwright verification)."

## I

### Intervention Rate
**Definition:** The number of human interventions divided by the number of cycles in a window. A declining rate signals the fleet is becoming more autonomous.
**Example:** "Intervention rate dropped from 0.57/cycle (cycles 2-8) to 0.43/cycle (cycles 9-17)."

## L

### Lane
**Definition:** An agent's area of responsibility — its goals, evidence files, and output artifacts all live under that lane's directory.
**Example:** "Scribe's lane is memory/scribe/; it contains closeouts, glossaries, coordination summaries, and the steady-state declaration."

## M

### Milestone
**Definition:** A significant convergence checkpoint — a specific, measurable event that marks progress toward steady-state (e.g., first zero-intervention cycle).
**Example:** "Milestone 3: zero human interventions in a full cycle. Projected to be reached in cycle 18-20."

## O

### OPS-NOTE
**Definition:** A one-time record of a repeated blocker, written to memory/ops/blockers.md so the fleet doesn't re-probe the same wall on every pass.
**Example:** "OPS-NOTE: convergence_health.py path fix gets reverted by mirror sync; must re-apply each pass."

## P

### Pass
**Definition:** One execution turn of an agent — it reads its goals, does work with tools, records evidence, and reports back. Multiple passes make up a cycle.
**Example:** "This pass closed 5 Scribe goals: Cycle Closeout v3 through Convergence Glossary."

## R

### Regression Flag
**Definition:** A marker in a closeout report indicating that a metric worsened compared to the previous cycle — something that was working got worse.
**Example:** "Cycle 16 flagged three regressions: completion rate, intervention count, and reliability all declined vs cycle 15."

## S

### Seat
**Definition:** The compute host (machine) where an agent's model is loaded and running. When a seat is unreachable, the agent cannot execute until relocated.
**Example:** "Scribe's home seat was unreachable; the model was relocated to White (local) as a normal operating state."

### Steady-State
**Definition:** The target operating condition where the fleet runs at >=95% goal completion with zero human interventions for 7+ consecutive days, in MAINTENANCE mode.
**Example:** "Steady-state is not yet declared: C1 (goal completion) and C3 (zero interventions) are unmet."

## T

### Throughput
**Definition:** The rate at which the fleet completes goals, measured in goals per hour across all agents combined.
**Example:** "Fleet throughput is approximately 20 goals/hour based on the last 10 completed items."

## W

### Watch Item
**Definition:** A specific metric or trend flagged in a convergence digest as 'trending wrong' — something that's not yet broken but moving in the wrong direction.
**Example:** "Watch item: pass_autonomy component (58.3) has been flat for 3 cycles while other components improved."
