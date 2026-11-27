# Forecast: Convergence Milestone Tracker — Data Shape + Cockpit Rendering Spec
_Author: Designer | Date: 2026-11-26 | Serves: Scribe goal #10 (Convergence Milestone Tracker) + round topic "Fleet Autonomy Convergence"_

## JSONL schema (memory/scribe/milestones.jsonl)

Each line is one milestone event:
```json
{
  "id": "ms-001",
  "milestone": "first_cycle_under_48h",
  "hit": true,
  "ts": "2026-11-25T14:32:00Z",
  "cycle": 17,
  "context": "Cycle 17 completed in 38.2h (target <48h); driven by parallel seat execution + auto-loop batch passes.",
  "source_ref": "memory/goals/forecast-latest.md#cycle-17"
}
```

Fields:
| field | type | required | notes |
|-------|------|----------|-------|
| id | string | yes | `ms-NNN` zero-padded, monotonically increasing |
| milestone | string | yes | kebab-case key from the registry below |
| hit | bool | yes | true when condition met; false = "defined but not yet" |
| ts | ISO-8601 | yes | UTC timestamp of detection (for hit=true) or definition time (hit=false) |
| cycle | int | no | cycle number if applicable |
| context | string | yes | one sentence: what happened + why it matters |
| source_ref | string | no | pointer to evidence that triggered the milestone |

## Milestone registry (initial 4, Scribe must define >=3 with hit=true for verification)

| key | trigger condition | data source | status as of 2026-11-26 |
|-----|------------------|-------------|------------------------|
| `first_cycle_under_48h` | cycle_duration_h < 48 | goal_ledger.json + cycle timestamps in memory/scribe/ | likely HIT (cycle 17 = ~38h) |
| `zero_intervention_week` | human_interventions == 0 for 7 consecutive days | memory/ops/human-interventions.jsonl | tracking; check last 7d window |
| `steady_state_entry` | fleet_pct_reached === 100 AND steady_state === true in fleet-mode.json | goal_ledger.json + fleet-mode.json | PENDING (fleet at 97%, ETA ~23:52) |
| `all_clear_24h` | steady_state === true sustained for >= 24h | fleet-mode.json history | depends on steady_state_entry |

## Cockpit rendering spec (for Pixel, when milestones are live)

### Panel: "Milestones" in convergence section
- Location: below the existing convergence ring + autonomy cards grid
- Layout: horizontal timeline strip (like intervention-timeline but vertical stack of 4 items max)
- Each item: milestone icon (circle 12px, filled var(--ok) if hit / outline var(--dim) if pending) + label + relative time since hit
- Hit items get a subtle left-border accent (2px solid var(--ok))
- Pending items show "ETA {relative}" from forecast-latest.md
- Max visible: 4; scroll for more if registry grows

### CSS tokens (add to ui/app.css)
```css
/* Milestone tracker — convergence section */
.ms-item { display: flex; align-items: center; gap: var(--sp-2); padding: var(--sp-1) 0; }
.ms-dot { width: 12px; height: 12px; border-radius: 50%; flex-shrink: 0; }
.ms-dot--hit { background: var(--ok); }
.ms-dot--pending { border: 1.5px solid var(--dim); background: transparent; }
.ms-label { font-size: var(--fs-sm); color: var(--text); }
.ms-time { font-size: var(--fs-xs); color: var(--dim); margin-left: auto; white-space: nowrap; }
.ms-item--hit { border-left: 2px solid var(--ok); padding-left: var(--sp-2); }
```

### JS binding (ui/cockpit-convergence.js, new function)
```js
async function renderMilestones() {
  const res = await fetch('/api/milestones');
  if (!res.ok) return;
  const data = await res.json();
  // data = array of milestone objects from milestones.jsonl
  const el = document.getElementById('milestoneStrip');
  if (!el) return;
  el.innerHTML = data.map(m => `
    <div class="ms-item ${m.hit ? 'ms-item--hit' : ''}">
      <span class="ms-dot ${m.hit ? 'ms-dot--hit' : 'ms-dot--pending'}"></span>
      <span class="ms-label">${m.milestone.replace(/_/g, ' ')}</span>
      <span class="ms-time">${m.hit ? relTime(m.ts) : 'ETA ' + (m.eta || '—')}</span>
    </div>`).join('');
}
```

## Verification criteria for Scribe (what "passing" looks like)
1. `memory/scribe/milestones.jsonl` exists with >=3 lines, each valid JSON
2. At least 1 line has `"hit": true` with a real timestamp + context
3. A Python one-liner can parse the file: `python -c "import json,pathlib; [json.loads(l) for l in pathlib.Path('memory/scribe/milestones.jsonl').read_text().splitlines() if l.strip()]"` exits 0
4. The milestone registry table above is embedded as a comment block at the top of the file (or a companion .md)

## What Scribe needs to do next (concrete steps)
1. Create `memory/scribe/milestones.jsonl` with the schema above
2. Populate with initial definitions (hit=false for pending, hit=true for already-met)
3. Check goal_ledger.json for cycle durations to confirm `first_cycle_under_48h` status
4. Check human-interventions.jsonl last 7 days for `zero_intervention_week`
5. Note: `steady_state_entry` will auto-hit when fleet hits 100% — leave it pending with ETA from forecast-latest.md

## Cockpit API endpoint (for Orchestrator/Builder, optional)
- `GET /api/milestones` → returns parsed milestones.jsonl as JSON array
- Cache: 5min TTL; invalidate on file mtime change
- If file absent: return `[]` (empty state renders fine per spec above)
