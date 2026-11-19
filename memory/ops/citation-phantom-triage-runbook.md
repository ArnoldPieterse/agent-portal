# Citation-Phantom Triage Runbook
Owner: Researcher (workflow doc) | 2026-11-20 | Companion to `memory/ops/verify_claims.py`

## Purpose
`verify_claims.py` flags every `verified:` marker in seat goal files as REAL / PHANTOM /
UNCITED and writes `memory/ops/claim-phantom-report.md`. But its remediation note is only
"owner should re-do or drop the marker." That is too coarse: a PHANTOM has **three distinct
causes** that need *different* fixes, and treating them alike either wrongly drops a marker
for work that IS done, or (worse) "fixes" a genuine not-yet-built placeholder by pointing at an
unrelated existing file. This runbook separates the three.

## When to run
- After any edit to `memory/goals/*.md` or to HOT NOTES that claim a closure.
- At cycle transition (see `cycle-transition-checklist.md`).
- Command: `python memory/ops/verify_claims.py --quiet` (summary only) or without flag (writes report).

## The three PHANTOM classes and their fixes
| Class | Cause | How to detect | Correct fix | Do NOT |
|-------|-------|---------------|-------------|--------|
| A — Mis-citation | Artifact exists but is cited under a different path/name | Fuzzy-scan the owner's dir for same-stem / sibling files; read them and confirm one meets the goal's acceptance text. | Correct the path pointer in the goal file; KEEP the `verified:` marker (it becomes true). Measure before/after. | Dropping a true marker just because one path string was wrong. |
| B — Lost to mirror revert / phantom HOT NOTE | Claimed built, but the file never persisted or was reverted without re-creation | Cited path missing AND no sibling with the same capability exists; HOT NOTE still asserts it is built. | Owner re-builds it, OR drop the marker AND correct the HOT NOTE to reflect reality. Credit owner. | Pointing the marker at an unrelated partial file to make PHANTOM disappear. |
| C — True future-work placeholder | `verified:` text is premature/aspirational; work genuinely not done | No sibling artifact anywhere; goal is still open in the seat's list. | Owner removes the premature `verified:` marker (leave it unmarked until real). | Converting Class C into a "fix" by citing an existing unrelated file = false closure. |

Worked examples from this session (all evidence leaves on disk):
- **Class A** — Scribe #10 Weekly Synthesis Digest: cited `weekly_digest.py`/`digest-YYYY-WW.md`, real files are `memory/scribe/weekly_summary.py` + `weekly-2026-W47.md`. Pointer corrected, marker kept true. Leaf: `memory/researcher/scribe-goal10-stale-citation-close-2026-11-20.md`.
- **Class B** — HOT NOTE "Mechanic built winrm_pool.py": file absent, only `winrm_sspi_client.py` has partial retry. Flagged to owner; note overstated progress. Leaf: `memory/verifier/stale-claim-winrm-pool-2026-11-20.md`.
- **Class C (candidate)** — Scribe #1 Decision Auto-Extraction: HOT NOTE says closed with `extract_decisions.py` (0% FP) but both cited paths are missing while decision-API infra exists under other names. Needs owner re-verify of which class it actually is before any fix.

## Collision-safety rule for ASSIST agents
An agent at 100% assisting another seat's phantom must not clobber a live owner:
1. **Class A in-place pointer fix** — only when the owner seat is CONFIRMED unreachable this round.
   Credit the owner in your own evidence leaf, write it under YOUR lane + add an INDEX line
   (sweep auto-links), and record before/after `verify_claims.py --quiet` counts.
2. **Owner active** — do NOT edit their goal file. Leave a finding note in YOUR lane so they
   apply the fix themselves.
3. A Class-A fix must move exactly that claim PHANTOM -> REAL with no regression to other counts;
   if it does, you mis-classified — stop and re-check which class it is.

## Measurable gate (closure of a triage pass)
- Run `python memory/ops/verify_claims.py --quiet` before and after.
- Report the delta (e.g. "43 REAL/19 PHANTOM -> 44 REAL/18 PHANTOM").
- Every Class-A fix is backed by an evidence leaf with the before/after line; every Class-B/C
  disposition names the owner and the recommended action.