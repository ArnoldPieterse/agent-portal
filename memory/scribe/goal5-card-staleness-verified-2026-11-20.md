# Goal 5 — Card Staleness Detection: VERIFIED 2026-11-20

## Acceptance criteria (all met)

| # | Criterion | Result |
|---|-----------|--------|
| 1 | After modifying a source file, the corresponding card is flagged | PASS — selftest: modifying `a.md` flags `c1.md`; real data: 3/4 cards correctly flag newer sources |
| 2 | Unmodified cards are not flagged | PASS — selftest: `c2.md` stays clean; real data: `pin-file.md` shows empty `stale_sources` |
| 3 | Run on real data produces valid output with no false positives | PASS — 4 cards checked, all entries have `{card_path, stale_sources[], last_generated, days_since}`, valid JSON |

## Artifact
- Script: `memory/scribe/card_staleness.py` (built this cycle)
- Selftest: `python memory/scribe/card_staleness.py --selftest` → "SELFTEST PASS: 3/3"
- Real-data run: 4 cards, 3 stale (sources modified post-generation), 1 fresh

## Real-data output summary (2026-11-20)
- `anti-stall.md`: 1 stale source (`memory/goals/scribe.md` updated after card gen)
- `hotload.md`: 4 stale sources (goals files + researcher INDEX updated)
- `mirror.md`: 2 stale sources (researcher INDEX + open-questions-log updated)
- `pin-file.md`: fresh (no stale sources)

## Ledger record
