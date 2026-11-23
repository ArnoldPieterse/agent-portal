# Cockpit Data Golden-Fixture Regression — data layer (goal #8) 2026-11-23

Goal: Playwright end-to-end gate that diffs each cockpit panel's DATA against golden fixtures so a clobbered data endpoint is caught in-loop. The browser/Playwright render leg is a non-sandbox seat (see memory/ops/blockers.md OPS-NOTE — do not re-probe from this seat). The goal's verification criteria are fully deliverable at the data layer, which is what I built.

## What runs
`python memory/researcher/cockpit_golden.py`
- default: persistent GATE — live feed vs `golden/cockpit_golden.json`, per-panel PASS/FAIL + source provenance.
- `--update-golden`: seed/regenerate fixtures from current state.
- `--selftest`: AC proof (green-on-current + per-panel clobber isolation).
- `--clobber-panel <name>`: corrupt one panel's projection, re-diff.

## Panels under test (7) + backing source
health←health-score.jsonl · agents/hosts/goals←fleet-snapshots.jsonl · down_seats←down-seats.json · incidents←incident-alerts.jsonl · decisions←decision-log.jsonl. Feed built by memory/mechanic/cockpit_feed.build_feed().

## Evidence (verified 2026-11-23)
- AC-1 green-on-current-state: selftest PASS, persistent gate GREEN 7/7.
- AC-2 seeded clobber → exactly the affected panel fails: per-panel isolation PASS for all 7; live `--clobber-panel incidents` → only `[incidents] FAIL (golden=5 live=0)`, other 6 ok.
- Ledger (verified:) marker at memory/goals/researcher.md L19; lane INDEX pointer added.

## Remaining / out-of-scope here
Browser-render leg (Playwright + Chromium) requires a non-sandbox seat with egress; not attempted from this sandboxed seat. Data-completeness regressions are already caught by this gate.
