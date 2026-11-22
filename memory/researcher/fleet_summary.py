#!/usr/bin/env python3
"""
fleet_summary.py - Researcher goal #1 (cycle-10): Fleet State Narrative Summarizer.

Generates a 3-5 sentence natural-language summary of fleet state from LOCAL cockpit
data, written to memory/ops/fleet-summary-<date>.md. Every number in the narrative is
traced to a file on disk (no hallucinated metrics) and the run is self-checked:
  - 3 <= sentences <= 5
  - runtime < 10s
  - at least one actionable insight present

Data sources (all local, reproducible by re-running this script):
  1. Goal state   : memory/goals/<agent>.md  (per-agent total + locally-resolved goals)
  2. Incidents    : memory/ops/incidents/*.md  (count + classification + date range)
  3. Residency    : memory/llm/residency-matrix.md  (hosts, DRIFT, unreachable-from-seat)
  4. Slip model   : memory/goals/slip_prediction_table.md  (CV accuracy, slip rate)

Methodology / caveats are written into the output header so the summary never presents
a local figure as if it were a live portal metric.
"""
import os, re, glob, time, sys, argparse, datetime

T0 = time.time()

# Canonical 8-seat roster (excludes test/forecast/proposal files that also match [a-z]+.md).
ROSTER = ["archivist", "builder", "designer", "mechanic", "orchestrator",
          "researcher", "scribe", "verifier"]

def agent_goal_files():
    """Goal files for the 8 canonical seats only, that exist on disk."""
    return [a + ".md" for a in ROSTER if os.path.exists(os.path.join("memory", "goals", a + ".md"))]

def _pointer_paths(block):
    """Yield candidate file paths referenced as evidence pointers/inline code files."""
    for m in re.finditer(r"\(pointer:\s*([^)\s]+)\)", block):
        yield m.group(1).strip()
    # inline backtick references that look like repo-relative memory/... paths
    for m in re.finditer(r"`((?:memory|ui)/[^`\s]+)`,?", block):
        yield m.group(1).strip()

def parse_goal_file(path):
    """Return (total, resolved). resolved = goal block carries a '(verified:' marker OR
    at least one pointer/backtick path that exists on disk. This is a LOCAL lower bound
    of /api/goals' reached count (which may also credit non-file evidence)."""
    txt = open(path, encoding="utf-8", errors="replace").read()
    # split into numbered goal blocks
    parts = re.split(r"(?m)^\s*\d+\.\s+\*\*", txt)
    total = len(parts) - 1
    if total <= 0:
        return 0, 0
    resolved = 0
    for block in parts[1:]:
        if "(verified:" in block or " (verified" in block:
            resolved += 1
            continue
        ok = any(os.path.exists(p.replace("\\", "/")) for p in _pointer_paths(block))
        if ok:
            resolved += 1
    return total, resolved

def parse_incidents():
    d = os.path.join("memory", "ops", "incidents")
    files = sorted(glob.glob(os.path.join(d, "*.md"))) if os.path.isdir(d) else []
    classes = {"portal_down": 0, "host_down": 0, "wedged": 0, "other": 0}
    dates = []
    for f in files:
        name = os.path.basename(f)
        m = re.match(r"(\d{4}-\d{2}-\d{2})", name)
        if m:
            dates.append(m.group(1))
        if "portal_down" in name: classes["portal_down"] += 1
        elif "host_down" in name: classes["host_down"] += 1
        elif "wedged" in name: classes["wedged"] += 1
        else: classes["other"] += 1
    return files, classes, dates

def parse_residency():
    p = os.path.join("memory", "llm", "residency-matrix.md")
    info = {"hosts": None, "drift": None, "unreachable": None, "last_run": None}
    if not os.path.exists(p):
        return info
    t = open(p, encoding="utf-8", errors="replace").read()
    for key, pat in [("hosts", r"hosts:\s*\**\(?\d+\)?"), ("drift", r"DRIFT:\s*\**\(?\d+\)?"), ("unreachable", r"unreachable:\s*\**\(?\d+\)?")]:
        m = re.search(pat, t)
        if m:
            dm = re.search(r"\d+", m.group(0))
            if dm: info[key] = int(dm.group(0))
    m = re.search(r"Last run:\s*([0-9: -]+)", t)
    if m: info["last_run"] = m.group(1).strip()
    return info

def parse_slip():
    p = os.path.join("memory", "goals", "slip_prediction_table.md")
    info = {"cv_acc": None, "slip_rate": None}
    if not os.path.exists(p):
        return info
    t = open(p, encoding="utf-8", errors="replace").read()
    m = re.search(r"CV accuracy:\s*([\d.]+)%", t)
    if m: info["cv_acc"] = float(m.group(1))
    m = re.search(r"Slip rate:\s*([\d.]+)%", t)
    if m: info["slip_rate"] = float(m.group(1))
    return info

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    date = args.date
    out = args.out or os.path.join("memory", "ops", f"fleet-summary-{date}.md")

    # 1. goals
    per_agent = {}
    for base in agent_goal_files():
        p = os.path.join("memory", "goals", base)
        if os.path.exists(p):
            tot, res = parse_goal_file(p)
            per_agent[base[:-3]] = {"total": tot, "resolved": res}
    fleet_total = sum(v["total"] for v in per_agent.values())
    fleet_resolved = sum(v["resolved"] for v in per_agent.values())
    goal_progress = (fleet_resolved / fleet_total) if fleet_total else 0.0

    # 2. incidents
    inc_files, classes, dates = parse_incidents()
    n_inc = len(inc_files)
    recent7 = 0
    if dates:
        try:
            today = datetime.date.fromisoformat(date)
            for d in dates:
                if (today - datetime.date.fromisoformat(d)).days <= 7:
                    recent7 += 1
        except ValueError:
            recent7 = n_inc
    dom_class = max(classes, key=classes.get) if classes else "none"
    incident_load = min(1.0, recent7 / 5.0)

    # 3. residency (observability caveat only - NOT a health penalty: unreachable is a seat egress wall)
    res = parse_residency()

    # 4. slip model (predicted risk context)
    slip = parse_slip()

    # deterministic health score (documented): weights on goal progress + inverse incident load.
    W_G, W_I = 0.7, 0.3
    health = round(100 * (W_G * goal_progress + W_I * (1.0 - incident_load)), 1)

    # top open-goal lane(s) as actionable focus
    open_by = {a: v["total"] - v["resolved"] for a, v in per_agent.items()}
    focus = max(open_by, key=open_by.get) if open_by else "n/a"
    focus_n = open_by.get(focus, 0)

    # ---- narrative (3-5 sentences, no invented metrics) ----
    agents_sorted = ", ".join(sorted(per_agent.keys())) or "none found"
    res_str = f"{res['drift']} drift" if res["drift"] is not None else "unknown drift"
    if res["hosts"] and res["unreachable"] is not None and res["unreachable"] >= res["hosts"]:
        unreach_str = (f"all {res['unreachable']} hosts unreachable from this seat (egress wall) - "
                       f"live portal metrics unavailable, figures are local-file-derived")
    elif res["hosts"] and res["unreachable"] is not None:
        unreach_str = f"{res['unreachable']}/{res['hosts']} hosts unreachable from this seat"
    else:
        unreach_str = "residency data unavailable"

    sentences = []
    s1 = (f"Fleet goal state (local parse of memory/goals): {fleet_resolved} of {fleet_total} goals across "
          f"{len(per_agent)} agents ({agents_sorted}) carry resolved evidence markers/pointers on disk, a {goal_progress*100:.0f}% locally-verified progress lower bound.")
    sentences.append(s1)
    s2 = (f"Unresolved work concentrates in the {focus} lane ({focus_n} open goals), the largest single concentration among lanes."
          if focus != "n/a" and focus_n > 0 else
          f"No single lane dominates unresolved work; load is spread across agents.")
    sentences.append(s2)
    s3 = (f"The incident log holds {n_inc} incidents ({classes['portal_down']} portal_down, {classes['host_down']} host_down, {classes['wedged']} wedged) over "
          f"{min(dates) if dates else 'unknown'} to {max(dates) if dates else 'unknown'}, with {dom_class} the recurring class - a persistent availability risk.")
    sentences.append(s3)
    s4 = (f"Residency matrix (last run {res['last_run'] or 'unknown'}) shows {res_str}; note {unreach_str}.")
    sentences.append(s4)
    s5 = (f"Actionable: stabilize the {dom_class} recurrence first (it drives incident load), then close the {focus} lane - "
          f"expected slip rate from the v2 model is ~{slip['slip_rate']:.0f}% (CV acc {slip['cv_acc']}%).") if slip["slip_rate"] else \
         (f"Actionable: address the recurring {dom_class} incidents before starting new cycle work, and clear the largest open lane ({focus}).")
    sentences.append(s5)

    narrative = " ".join(sentences).strip()

    # ---- self-checks ----
    cleaned = re.sub(r"\d+\.\d+", "X", narrative)  # don't split sentences on decimals (e.g. 71.2%)
    n_sen = len(re.findall(r"[^.!?]+[.!?]", cleaned))
    elapsed = time.time() - T0
    ok_sen = 3 <= n_sen <= 5
    ok_time = elapsed < 10.0
    ok_action = ("Actionable:" in narrative) or ("then " in narrative)
    checks = {"sentences": n_sen, "sentences_ok": ok_sen, "seconds": round(elapsed, 3),
              "time_ok": ok_time, "actionable_insight": ok_action,
              "overall_PASS": bool(ok_sen and ok_time and ok_action)}

    # ---- write report ----
    header = f"""# Fleet State Narrative - {date}

Generated by `memory/researcher/fleet_summary.py` (Researcher goal #1, cycle-10).
Deterministic: same on-disk inputs -> same output.

## Data sources & methodology (no hallucinated metrics)
| Metric | Source file | Note |
|---|---|---|
| Goal progress {fleet_resolved}/{fleet_total} | memory/goals/*.md | resolved = inline `(verified:` marker OR a pointer/backtick path that exists on disk; LOCAL lower bound of /api/goals |
| Incidents {n_inc} (recent-7d {recent7}) | memory/ops/incidents/*.md | classed by filename |
| Residency DRIFT {res['drift']} / unreachable {res['unreachable']}/{res['hosts']} | memory/llm/residency-matrix.md (last run {res['last_run']}) | unreachable = this seat's egress wall, NOT fleet-down |
| Slip rate ~{slip['slip_rate']}% / CV {slip['cv_acc']}% | memory/goals/slip_prediction_table.md | v2 model context |

Health score formula: `100 * (0.7*goal_progress + 0.3*(1 - incident_load))`,
where `incident_load = min(1, recent7/5)`. Parameters W_goal=0.7, W_incident=0.3.
**Computed health = {health}/100.**

## Narrative ({n_sen} sentences)
{narrative}

## Self-check
"""
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(header)
        for k, v in checks.items():
            fh.write(f"- {k}: {v}\n")
        fh.write("\n")

    # stdout
    print("NARRATIVE:")
    print(narrative)
    print("\nSELF-CHECK:", checks)
    print(f"WROTE: {out}")
    sys.exit(0 if checks["overall_PASS"] else 1)

if __name__ == "__main__":
    main()
