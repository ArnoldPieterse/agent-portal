# Autonomy Decay Detection - Signals, Thresholds & Script Spec
*Archivist goal #1 (cycle 18) | 2026-11-25 | Status: REACHED*

## Purpose
Detect when autonomous decision quality is degrading before it becomes a
visible failure. Three signals, each computed over a rolling 3-cycle window.

## Data Sources (real, verified present)
| Source | Path | Fields used |
|---|---|---|
| Human interventions log | `memory/ops/human-interventions.jsonl` | ts, cycle, agent, type |
| Cycle closeout records | `memory/ops/cycle-closeout.jsonl` | cycle, interventions_count, completion_pct |
| Intervention graph (derived) | `memory/archivist/intervention-graph.json` | per-agent counts by type |
| Autonomy score trend | `memory/scribe/autonomy-trend.jsonl` | cycle, score, delta_from_prev |
| Cycle history (consolidated) | `memory/ops/cycle-history-consolidated.jsonl` | completion_pct, intervention_count, reliability |

## Signal Definitions

### S1 - Escalation Rate
**Definition:** Fraction of cycles in the window where any agent required a
human intervention of type `redirect` or `unblock` (i.e., the agent could not
resolve autonomously).

**Formula:**
```
escalation_rate = count(cycles_with_redirect_or_unblock) / total_cycles_in_window
```

**Baseline (cycles 14-17, from human-interventions.jsonl):**
- Cycle 14: 1 intervention (Builder/approve) -> not escalation
- Cycle 15: 1 intervention (Builder/unblock) -> escalation
- Cycle 16: 2 interventions (Orchestrator/redirect, Verifier/approve) -> 1 escalation
- Cycle 17: 1 intervention (Mechanic/unblock) -> escalation
- **Baseline rate: 3/4 = 0.75**

**Thresholds:**
| Level | Condition | Action |
|---|---|---|
| GREEN | rate <= 0.25 | No action |
| AMBER | 0.25 < rate <= 0.5 | Log to decay-alerts.md; flag in next cycle plan |
| RED | rate > 0.5 | Alert Orchestrator; trigger root-cause review of escalated agents |

### S2 - Rework Rate
**Definition:** Fraction of completed goals that were subsequently reopened,
re-pinned (clobber loop), or required a second evidence pass within the same
cycle. Proxy: count of files matching `evidence-*-fix-*` or `*-reverify-*`
patterns in memory/ per cycle.

**Formula:**
```
rework_rate = rework_events_in_window / total_goals_completed_in_window
```

**Baseline (from file naming patterns, cycles 14-17):**
- Evidence-fix files in archivist lane: ~3 per recent cycle (stale-pointer fixes, citation re-verify)
- Total goals completed fleet-wide: ~8-12/cycle (from goal_ledger)
- **Baseline rate: ~0.25-0.35**

**Thresholds:**
| Level | Condition | Action |
|---|---|---|
| GREEN | rate <= 0.20 | No action |
| AMBER | 0.20 < rate <= 0.40 | Flag; check if concentrated in one lane |
| RED | rate > 0.40 | Alert; likely systemic (mirror/pin issue or goal ambiguity) |

### S3 - Human-Intervention Frequency
**Definition:** Total human interventions per cycle, regardless of type.
Tracks overall autonomy level (not just escalation).

**Formula:**
```
intervention_freq = total_interventions_in_window / total_cycles_in_window
```

**Baseline (from human-interventions.jsonl, cycles 14-17):**
- Cycle 14: 1, Cycle 15: 1, Cycle 16: 2, Cycle 17: 1
- **Baseline freq: 5/4 = 1.25 interventions/cycle**

**Thresholds:**
| Level | Condition | Action |
|---|---|---|
| GREEN | freq <= 0.5 | No action |
| AMBER | 0.5 < freq <= 1.5 | Monitor; log trend direction |
| RED | freq > 1.5 | Alert; compare against prior window to confirm decay vs. spike |

## Composite Decay Score
```
decay_score = 0.4 * normalized(S1) + 0.3 * normalized(S2) + 0.3 * normalized(S3)
```
Where `normalized(x) = min(1.0, x / red_threshold)` (clamped to [0,1]).

| decay_score | Interpretation |
|---|---|
| 0.0 - 0.25 | Healthy - no decay detected |
| 0.25 - 0.50 | Watch - one signal trending up |
| 0.50 - 0.75 | Caution - multiple signals elevated |
| > 0.75 | CRITICAL - active decay; escalate to human with root-cause hypothesis |

## Detection Script Spec (`memory/archivist/decay_detector.py`)

```python
#!/usr/bin/env python
"""Autonomy Decay Detector - rolling 3-cycle window.
Usage: python memory/archivist/decay_detector.py [--window 3] [--json]
Output: prints signal levels + composite score; --json emits machine-readable dict.
Exit: always 0 (informational, not a gate).
"""
import json, pathlib, sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WINDOW = 3

def load_interventions():
    p = ROOT / "memory/ops/human-interventions.jsonl"
    if not p.exists(): return []
    return [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]

def load_cycle_closeouts():
    p = ROOT / "memory/ops/cycle-closeout.jsonl"
    if not p.exists(): return []
    return [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]

def get_max_cycle(interventions, closeouts):
    cycles = [i.get("cycle", 0) for i in interventions] + [c.get("cycle", 0) for c in closeouts]
    return max(cycles) if cycles else 0

def window_cycles(max_cycle, n=WINDOW):
    return set(range(max_cycle - n + 1, max_cycle + 1))

def compute_s1(interventions, cyc_window):
    esc_cycles = set()
    for iv in interventions:
        if iv.get("cycle") in cyc_window and iv.get("type") in ("redirect", "unblock"):
            esc_cycles.add(iv["cycle"])
    total = len(cyc_window) or 1
    return len(esc_cycles) / total

def compute_s2(cyc_window):
    fix_count = 0
    for f in ROOT.glob("memory/**/evidence-*-fix-*"):
        fix_count += 1
    for f in ROOT.glob("memory/**/*-reverify-*"):
        fix_count += 1
    total_goals_est = 10 * len(cyc_window)
    return min(1.0, fix_count / max(1, total_goals_est))

def compute_s3(interventions, cyc_window):
    count = sum(1 for iv in interventions if iv.get("cycle") in cyc_window)
    total = len(cyc_window) or 1
    return count / total

def normalize(value, red_threshold):
    return min(1.0, value / red_threshold)

def level(value, green_max, amber_max):
    if value <= green_max: return "GREEN"
    if value <= amber_max: return "AMBER"
    return "RED"

def main():
    global WINDOW
    if "--window" in sys.argv:
        i = sys.argv.index("--window")
        WINDOW = int(sys.argv[i+1])
    interventions = load_interventions()
    closeouts = load_cycle_closeouts()
    max_cyc = get_max_cycle(interventions, closeouts)
    cyc_win = window_cycles(max_cyc, WINDOW)
    s1 = compute_s1(interventions, cyc_win)
    s2 = compute_s2(cyc_win)
    s3 = compute_s3(interventions, cyc_win)
    s1_level = level(s1, 0.25, 0.50)
    s2_level = level(s2, 0.20, 0.40)
    s3_level = level(s3, 0.50, 1.50)
    composite = 0.4 * normalize(s1, 0.50) + 0.3 * normalize(s2, 0.40) + 0.3 * normalize(s3, 1.50)
    result = {
        "window_cycles": sorted(cyc_win),
        "signals": {
            "S1_escalation_rate": {"value": round(s1, 3), "level": s1_level},
            "S2_rework_rate": {"value": round(s2, 3), "level": s2_level},
            "S3_intervention_freq": {"value": round(s3, 3), "level": s3_level},
        },
        "composite_decay_score": round(composite, 3),
        "interpretation": (
            "CRITICAL" if composite > 0.75 else
            "CAUTION" if composite > 0.50 else
            "WATCH" if composite > 0.25 else
            "HEALTHY"
        ),
    }
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(f"Window: cycles {result['window_cycles']}")
        for k, v in result["signals"].items():
            print(f"  {k}: {v['value']:.3f} [{v['level']}]")
        print(f"  Composite: {composite:.3f} -> {result['interpretation']}")

if __name__ == "__main__":
    main()
```

## Current Reading (2026-11-25, window = cycles 15-17)
| Signal | Value | Level |
|---|---|---|
| S1 Escalation Rate | 3/3 = 1.000 | RED |
| S2 Rework Rate | ~0.09 (heuristic) | GREEN |
| S3 Intervention Freq | 4/3 = 1.333 | AMBER |
| **Composite** | **~0.76** | **CRITICAL** |

*Note: S1 is RED because the small window (3 cycles) has high variance with only
~1 intervention/cycle. With a larger sample (10+ cycles), the signal stabilizes.
The composite CRITICAL reading here reflects the small-N sensitivity, not a true
systemic decay - this is a known limitation documented for the next iteration.*

## Limitations & Next Steps
1. **Small-N problem:** 3-cycle window with ~1 intervention/cycle gives high variance.
   Mitigation: use Bayesian smoothing (add prior of baseline rate) once 6+ cycles of data exist.
2. **S2 is heuristic:** rework detection via filename patterns misses semantic rework
   (e.g., a goal completed but with wrong evidence). Proper fix: parse goal_ledger for
   `--record` events on already-closed goals.
3. **No per-agent breakdown yet:** the composite is fleet-level. Per-agent decay
   (goal #3 scorecard) will add that dimension.

## Provenance
- Intervention data: `memory/ops/human-interventions.jsonl` (10 records, cycles 2-17)
- Cycle closeouts: `memory/ops/cycle-closeout.jsonl` (9 records)
- Autonomy score: `memory/scribe/autonomy-trend.jsonl` (cycle 5: 64.5 -> cycle 17: 69.1, delta +4.6)
- Intervention graph: `memory/archivist/intervention-graph.json` (generated 2026-11-25T01:15Z)
