# Goal #10: UI Regression Baseline — Infrastructure Built (2026-11-18)

**Status: TOOLING COMPLETE, awaiting pixel capture (blocker logged)**

## What was built this pass
Three files in `memory/designer/baseline/`:

| File | Purpose |
|------|---------|
| `README.md` | Documents 8 expected panels, naming convention, usage, closure criteria |
| `manifest.py` | SHA256 hash manifest generator + verifier (`--verify`, `--list`) |
| `visual_diff.py` | Pixel-level comparison with configurable tolerance/threshold; exit 0=PASS, 1=FAIL |

## Validation performed
- `manifest.py`: generated manifest from 2 test PNGs → correct SHA256 + closure check (2/8 NOT MET)
- `visual_diff.py`: 3% synthetic change vs 5% threshold → PASS (exit 0); same images vs 2.5% threshold → FAIL (exit 1)
- Both scripts use Pillow (confirmed available on this host)

## What remains for closure
1. **Capture >=8 real panel screenshots** (requires browser-capable seat — Chrome + CDP or RDP)
   - Blocker already logged in `memory/ops/blockers.md` (2026-11-17): "Live-browser verification unavailable from this sandbox seat"
   - Unblock: any seated agent on White/Pale/Black/Red runs the capture command against :8099
2. Run `python memory/designer/baseline/manifest.py` to generate production manifest.json
3. Record via ledger: `python memory/researcher/goal_ledger.py --record designer 10 --note 'baseline infra + N screenshots captured'`

## Anti-loop note
The browser-capture blocker has been logged ONCE (2026-11-17). Not re-probing. This pass built the remaining non-browser work (tooling + docs) so closure is now a single capture session on any display-capable seat.
