# Productive Pass — Formal Definition (per role)

Scope: Cycle 15 (Fleet Autonomy Convergence). This document is the SSOT for what counts as a
"productive pass" when measuring idle-productivity (`memory/researcher/idle_productivity.py`),
idle-waste (`idle_waste.py`), and per-agent productivity baselines.

## 1. Baseline: what a "pass" is

A **pass** is one auto-loop iteration performed by exactly one agent, bounded by its
`start_ts`/`end_ts` in `memory/ops/autoloop.jsonl`. Because each pass has exactly one owner
agent, productiveness is judged against that owner's role criterion and can never be counted
toward two roles at once. This is the core of mutual exclusivity (see §4).

A pass is **productive** iff it produces a *new, durable artifact* attributable to that pass
window — not merely reading, waiting, re-verifying already-green work, or emitting idle chatter.
The operational signal is: at least one qualifying artifact (file created/modified, new
measurement/evidence entry, written test result) with an mtime inside `[start_ts, end_ts]`,
or an explicit `"productive": true` + non-empty `evidence_files` in the autoloop record.

## 2. Per-role definitions (all 8 roles)

| Role | Productive-pass criterion (sufficient) | Positive example | NOT productive |
|---|---|---|---|
| **Orchestrator** | Wrote/updated a cycle plan, dispatch artifact, or TODO/goal file with a concrete new decision line (not a re-issue of a closed goal). | Appends a new verified-goal evidence line to `TODO.md`; writes next-cycle proposal skeleton. | Re-posting an already-closed goal; only reading state. |
| **Builder** | Created/modified a code or config file with >10 lines changed (net, not whitespace) AND the change compiles/loads (no syntax error). | Adds a new function to `agent_portal.py` (+24 LOC) that imports cleanly. | 3-line comment-only edit; touching a file but reverting it. |
| **Verifier** | Wrote a test result/evidence artifact recording a PASS or FAIL with proof (assertion output, command + exit code). | Appends a Playwright/pytest result line to an evidence file. | Re-running a green test and re-stating "still passes" with no new artifact. |
| **Designer** | Created/modified a UI/design artifact (CSS/HTML/JS/markup or a design spec) that renders without layout regression, OR added a new component/token. | Adds a mode-banner CSS block to `ui/app.css` that renders in the cockpit. | Renaming a class with no visual/behavioral change; spec text with no concrete spec. |
| **Researcher** | Produced a *new* measurement, KB entry, or evidence leaf (a previously-absent data point / finding), not a re-measurement of an existing one. | Builds `dispatch_audit.py` and writes a new audit report with novel results. | Re-running the same script and copying the same numbers. |
| **Archivist** | Added/reconciled knowledge-base content: a new pointer, index entry, provenance note, or archived artifact that was not previously present. | Archives a daily productivity snapshot to `memory/archivist/productivity-history/`. | Rewriting an existing pointer with identical target. |
| **Scribe** | Produced a new synthesis artifact (decision brief, runbook section, close-out report) capturing content not already in the knowledge base. | Writes a cycle close-out report summarizing this cycle's goals + blockers. | Re-emitting last cycle's digest verbatim. |
| **Mechanic** | Performed a fleet-ops action with a durable effect: a host lifecycle change, OOM recovery, config write, or a probe/measurement artifact for fleet health. | Writes `memory/ops/budget-alert.md` after detecting >80% budget use; recovers an OOM host. | A no-op probe that found the same healthy state with no new artifact. |

## 3. Edge cases & partial credit

| Case | Ruling |
|---|---|
| **Cross-assist** (agent X works agent Y's goal) | Attributed to the *performer* X; judged against X's role criterion. It does NOT also count as productive for Y. No double counting. |
| **Partial artifact** (work started, not committed/verified) | 0.5 credit if a durable partial file exists in-window and is on-track; 0 if nothing new was written. Partial credit is recorded but only full-credit passes count toward the "productive" boolean rate. |
| **Fix that reverts** (change made then undone in same pass) | Not productive — net change ≈ 0. Count as a diagnostic pass only. |
| **Verification of someone else's green work with no new artifact** | Not productive (see Verifier row). Re-verification needs a *new* result line to count. |
| **Blocked pass** (no progress due to a real external dependency) | Not productive, but tagged `blocked` and excluded from the idle-waste denominator (it is not waste, it is gated work). Record once in `memory/ops/blockers.md`. |
| **Idle chatter / [SILENT] / no-op echo** | Never productive. |

## 4. Mutual exclusivity (why a pass can't be productive for two roles)

1. **Single owner:** every pass has exactly one agent → it is judged against exactly one role's row in §2.
2. **Disambiguation order for cross-assist:** performer's role wins (§3). The assisted goal's owner gets no credit from that pass.
3. **Artifact uniqueness:** a single new file/evidence entry is credited to the one pass that created it; a later pass touching the same file must produce a *new* delta to be productive itself.

Consequently, summing per-role productive passes over all agents equals the total productive
passes — there is no double counting.

## 5. Operational measurement (how scripts apply this)

`idle_productivity.py` classifies each pass as productive when:
- `record["productive"] is True`, **or**
- any path in `record["evidence_files"]` has an mtime within the pass window, **or**
- a qualifying artifact (role-appropriate file type) was created/modified in-window.

The per-role table above is the *semantic* definition; the script above is the *operational*
proxy. Where they diverge (e.g., a role's criterion not yet detectable from file mtimes), the
script under-counts and that gap is logged for later instrumentation, never silently guessed.
