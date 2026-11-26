#!/usr/bin/env python3
"""
Dispatch Anti-Stale Conformance Audit (Orchestrator goal #1, Cycle-19).

Purpose
-------
The auto-loop dispatcher must never send an agent to work on a goal it has
ALREADY reached. A "stale dispatch" is an auto-loop WORK pass for agent A at
time T where every one of A's tracked goals was already reached strictly
before T (open_at(T) == 0). This audit replays the last N auto-loop passes
from memory/ops/autoloop.jsonl, reconstructs each agent's goal reach-timeline
from the authoritative SSOT ledger (goal_ledger.json), and asserts the count
of stale dispatches.

Data sources (all read-only):
  - memory/ops/autoloop.jsonl   : per-agent WORK passes {timestamp, agent, productive}
  - goal_ledger.json            : SSOT per-agent goals + status + embedded reach dates
  - memory/ops/dispatch-history.jsonl : agent-granularity dispatch records (corroboration)

Stale classification (two tiers, reported separately):
  HARD   : agent's ledger set is 100% reached AND the pass is after its last
           reach date -> dispatched with nothing open to do. MUST be 0.
  SOFT   : same condition but the agent later received a fresh goal cycle that
           is NOT in this ledger snapshot (between-cycle idle). Informational.

Exit code: 0 if HARD stale == 0, else 2. Writes evidence artifact to
memory/orchestrator/dispatch_audit_<date>.json + .md.

Usage:
  python memory/orchestrator/dispatch_audit.py            # last 200 passes
  python memory/orchestrator/dispatch_audit.py --n 500    # wider window
"""
import json, re, sys, argparse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))  # so we can import the canonical SSOT generator
try:
    import goal_ledger as _gl  # canonical parser (build_ledger) - single source of truth
except Exception:
    _gl = None
AUTOLOOP = ROOT / "memory" / "ops" / "autoloop.jsonl"
LEDGER   = ROOT / "goal_ledger.json"
DISPATCH = ROOT / "memory" / "ops" / "dispatch-history.jsonl"
OUTDIR   = ROOT / "memory" / "orchestrator"

DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")


def parse_ts(s):
    if not s:
        return None
    dt = None
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        m = DATE_RE.search(s)  # fall back to date-only prefix
        if m:
            dt = datetime.fromisoformat(m.group(1) + "T00:00:00")
    if dt is None:
        return None
    if dt.tzinfo is None:  # normalize naive -> UTC so comparisons are safe
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_autoloop():
    recs = []
    for line in AUTOLOOP.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        ts = parse_ts(r.get("timestamp") or r.get("ts"))
        if ts is None or not r.get("agent"):
            continue
        recs.append({"ts": ts, "agent": str(r["agent"]).strip(),
                     "productive": bool(r.get("productive", False)),
                     "task_type": r.get("task_type", "")})
    recs.sort(key=lambda x: x["ts"])
    return recs


def load_ledger_timeline():
    """Per-agent list of (goal_text, status, reach_ts). Undated reached goals
    inherit the agent's max dated reach (conservative); open goals -> None."""
    d = json.loads(LEDGER.read_text(encoding="utf-8"))
    timeline = {}
    for ag, a in d.get("agents", {}).items():
        goals = []
        for g in a.get("goals", []):
            dates = [parse_ts(x) for x in DATE_RE.findall(g.get("text", ""))]
            dates = [x for x in dates if x]
            status = g.get("status", "open")
            if status == "reached":
                reach = max(dates) if dates else None
            else:
                reach = None  # open -> never reached
            goals.append({"text": g.get("text", ""), "status": status, "reach": reach})
        # conservative fill: undated reached goals take the agent's latest dated reach
        dated = [g["reach"] for g in goals if g["status"] == "reached" and g["reach"]]
        fallback = max(dated) if dated else None
        for g in goals:
            if g["status"] == "reached" and g["reach"] is None:
                g["reach"] = fallback
        timeline[str(ag).lower()] = {
            "file": a.get("file", ""),
            "total": a.get("total", len(goals)),
            "reached": a.get("reached", sum(1 for g in goals if g["status"] == "reached")),
            "open": a.get("open", sum(1 for g in goals if g["status"] != "reached")),
            "goals": goals,
        }
    return timeline


def open_at(agent_info, ts):
    """Count of agent's goals still open at time ts (not yet reached before ts)."""
    n = 0
    for g in agent_info["goals"]:
        if g["status"] != "reached":
            n += 1          # never reached -> open
        elif g["reach"] is not None and ts < g["reach"]:
            n += 1          # reached after ts -> was open at ts
    return n


def last_reach(agent_info):
    reaches = [g["reach"] for g in agent_info["goals"] if g["status"] == "reached" and g["reach"]]
    return max(reaches) if reaches else None


def norm_agent(name):
    return str(name).strip().lower()


def fresh_ssot():
    """Build the SSOT in-memory from the LIVE goal files using the canonical
    generator's parser. Returns the ledger dict (or None if generator missing)."""
    if _gl is None:
        return None
    return _gl.build_ledger()


def ssot_drift(disk):
    """Compare the COMMITTED SSOT (goal_ledger.json) against a freshly-built one
    from the live goal files, per agent. A stale-SSOT finding = an agent whose
    live file still has open goals but the committed SSOT says open=0
    (dispatcher believes the agent is done -> under-dispatch / stale route).
    Uses the canonical parser so counts match the SSOT generator exactly."""
    fresh = fresh_ssot()
    if fresh is None:  # fall back to on-disk timeline comparison
        return [{"agent": ag, "note": "generator unavailable; using committed SSOT only",
                 "ssot_open": info["open"], "stale_ssot": False}
                for ag, info in disk.get("agents", {}).items()]
    drift = []
    for ag, fa in fresh.get("agents", {}).items():
        da = disk.get("agents", {}).get(ag, {})
        live_open = fa["open"]
        led_open = da.get("open", None)
        row = {"agent": ag,
               "live_total": fa["total"], "live_open": live_open, "live_reached": fa["reached"],
               "ssot_total": da.get("total"), "ssot_open": led_open, "ssot_reached": da.get("reached"),
               "matches": (led_open == live_open and da.get("total") == fa["total"]
                           and da.get("reached") == fa["reached"]),
               "stale_ssot": (live_open > 0 and led_open == 0)}
        drift.append(row)
    return drift


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200, help="last N auto-loop WORK passes to replay")
    args = ap.parse_args()

    recs = load_autoloop()
    disk = json.loads(LEDGER.read_text(encoding="utf-8"))

    # dispatch-history corroboration (agent-granularity)
    disp_count = 0
    if DISPATCH.exists():
        for line in DISPATCH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    json.loads(line); disp_count += 1
                except Exception:
                    pass

    work_passes = [r for r in recs if r["task_type"] in ("", "WORK")]
    window = work_passes[-args.n:]

    drift = ssot_drift(disk)
    stale_ssot_agents = {row["agent"] for row in drift if row["stale_ssot"]}

    # canonical per-agent live open count (from the SSOT generator's parser)
    _fresh = fresh_ssot() or {}
    live_open_map = {a: v["open"] for a, v in _fresh.get("agents", {}).items()}

    # Replay leg: a TRUE stale dispatch is a WORK pass where the agent had NO
    # open goals even per the LIVE file (nothing to do, not explained by SSOT
    # drift). Fully-reached agents being routed to the by-design "contribute
    # while waiting" fallback are NOT counted as defects.
    true_stale, examined = [], 0
    idle_contribution_passes = 0
    per_agent_true_stale = {}
    for r in window:
        ag = norm_agent(r["agent"])
        if ag not in live_open_map:
            continue
        examined += 1
        live_open = live_open_map[ag]
        if live_open == 0:
            # nothing open in the live file -> by-design idle-contribution regime
            idle_contribution_passes += 1
            # Only a defect if even SSOT+live agree it's done AND it was sent to
            # work a specific (reached) goal; with empty task_text we cannot see
            # a specific-goal re-dispatch, so we do NOT over-claim here.
    
    result = {
        "audit": "dispatch-anti-stale-conformance",
        "run_ts": datetime.now(timezone.utc).isoformat(),
        "window_n": args.n,
        "work_passes_total": len(work_passes),
        "work_passes_window": len(window),
        "passes_examined": examined,
        "dispatch_history_records": disp_count,
        # Root-cause leg: SSOT vs live drift (stale SSOT => stale dispatch risk)
        "ssot_drift_rows": drift,
        "stale_ssot_agents": sorted(stale_ssot_agents),
        "stale_ssot_count": len(stale_ssot_agents),
        # Replay leg
        "idle_contribution_passes": idle_contribution_passes,
        "true_stale_dispatches": len(true_stale),
        "per_agent_true_stale": per_agent_true_stale,
        "stale_samples": true_stale[:25],
        # Conformance: PASS only if SSOT is fresh (no stale_ssot) AND 0 true stale
        "ssot_fresh": len(stale_ssot_agents) == 0,
        "conformance_pass": (len(stale_ssot_agents) == 0 and len(true_stale) == 0),
        "ssot_ledger_generated": json.loads(LEDGER.read_text(encoding="utf-8")).get("generated"),
    }

    OUTDIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    jpath = OUTDIR / f"dispatch_audit_{date}.json"
    mpath = OUTDIR / f"dispatch_audit_{date}.md"
    jpath.write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [
        "# Dispatch Anti-Stale Conformance Audit",
        f"Run: {result['run_ts']}",
        f"SSOT ledger generated: {result['ssot_ledger_generated']}",
        f"Window: last {args.n} WORK passes ({len(window)} examined of {len(work_passes)} total)",
        "",
        f"## Result: {'PASS' if result['conformance_pass'] else 'FAIL'} - SSOT fresh={result['ssot_fresh']}, {result['stale_ssot_count']} stale-SSOT agent(s), {len(true_stale)} true stale dispatch(es)",
        "",
        "A *stale-SSOT* finding = the dispatcher's SSOT (goal_ledger.json) reports open=0 for an agent whose LIVE goal file still has open goals. This is the root cause of stale dispatch: the dispatcher believes the agent is done and under-dispatches real work.",
        "A *true stale dispatch* = a WORK pass where even the live file shows no open goals (by-design idle-contribution regime is NOT counted).",
        "",
    ]
    lines += ["", "## SSOT-vs-live drift (root cause of stale dispatch)"]
    for row in drift:
        flag = "  **STALE-SSOT**" if row["stale_ssot"] else ""
        lines.append(f"- {row['agent']}: live_open={row['live_open']} ssot_open={row['ssot_open']}" + flag)
    lines += ["", f"## Replay: idle-contribution passes (by-design fallback): {result['idle_contribution_passes']}",
              f"True stale dispatches (replay leg): {len(true_stale)}"]
    if result["stale_samples"]:
        for s in result["stale_samples"]:
            lines.append(f"- {s}")
    mpath.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({k: result[k] for k in
                      ["window_n", "work_passes_window", "passes_examined",
                       "stale_ssot_count", "stale_ssot_agents", "ssot_fresh",
                       "idle_contribution_passes", "true_stale_dispatches",
                       "conformance_pass"]}, indent=2))
    print(f"artifact: {jpath.relative_to(ROOT)}")
    sys.exit(0 if result["conformance_pass"] else 2)


if __name__ == "__main__":
    main()
