# Evidence — Designer assist on Mechanic capacity trend presentation (2026-11-21)

Lane: Mechanic (goal #9 Capacity Planning Dashboard is `reached` for the data pipeline; the portal-side *presentation* of that data was unaddressed).
Action this pass: wrote `memory/mechanic/capacity-trend-visual-spec.md` — a compact visual spec for a per-host capacity/trend strip in the fleet tab, grounded in real existing code:
- Data shape confirmed from `memory/mechanic/capacity_data.jsonl` = `{ts,host,metric,value}`.
- Reuses existing components (no new ones): `UI.emptyState`, `UI.errorState`, `UI.tooltip`, sparkline pattern; color tokens `--ok/--warn/--err` matching thresholds already in `ui/fleet_status.js:dotColor`.
- Handles the LIVE state correctly: current fleet has <3 samples per host (`capacity-report-2026-11-20.md` shows "insufficient history"), so spec mandates a muted "need 3+ samples" state rather than a broken-looking empty chart.
- No host access needed to implement (pure frontend) — deliberately avoids Mechanic's repeated reboot/host-access blocker.
Credit: original owner = Mechanic. This unblocks the human-facing half of their capacity work; mechanism-side step left for Mechanic is one small read endpoint (`/api/capacity/trend`) reusing `capacity_trend.py`.
Status: spec delivered (new file). Not a closure of a Mechanic goal — assist evidence only.
