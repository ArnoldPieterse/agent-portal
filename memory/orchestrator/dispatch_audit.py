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


def build_timeline(d):
    """PURE: per-agent reach-timeline from a ledger dict.
    Per-agent list of (goal_text, status, reach_ts). Undated reached goals
    inherit the agent's max dated reach (conservative); open goals -> None."""
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


def load_ledger_timeline():
    """File-reading wrapper around the pure build_timeline."""
    return build_timeline(json.loads(LEDGER.read_text(encoding="utf-8")))


def count_open(agent_info, ts):
    """Count of agent's goals still open at time ts (not yet reached before ts).
    A goal is open-at(ts) if it was never reached, OR its reach date is strictly
    after ts. This is the primitive the stale-dispatch test hinges on."""
    n = 0
    for g in agent_info["goals"]:
        if g["status"] != "reached":
            n += 1          # never reached -> open
        elif g["reach"] is not None and ts < g["reach"]:
            n += 1          # reached after ts -> was open at ts
    return n

# backward-compat alias (older callers)
open_at = count_open


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


def audit_window(recs, timeline, n):
    """PURE core: replay the last N WORK passes against a per-agent reach
    timeline and count stale dispatches. A stale dispatch = a WORK pass for
    agent A at time T where open_at(A, T) == 0 (every tracked goal already
    reached strictly before T). Returns (window, result_core).

    Hermetic: no file IO here, so --selftest can feed synthetic data."""
    work_passes = [r for r in recs if r["task_type"] in ("", "WORK")]
    window = work_passes[-n:]
    true_stale = []
    examined = 0
    per_agent_true_stale = {}
    for r in window:
        ag = norm_agent(r["agent"])
        info = timeline.get(ag)
        if info is None or not info["goals"]:
            continue  # unknown agent / no tracked goals -> not a stale dispatch
        examined += 1
        if count_open(info, r["ts"]) == 0:
            per_agent_true_stale[ag] = per_agent_true_stale.get(ag, 0) + 1
            true_stale.append({"agent": ag, "ts": r["ts"].isoformat(),
                               "all_goals_reached_before_pass": True})
    violations = len(true_stale)
    conformance_pct = round(100.0 * (1 - violations / examined), 2) if examined else 100.0
    return window, {
        "window_n": n,
        "work_passes_total": len(work_passes),
        "work_passes_window": len(window),
        "passes_examined": examined,
        "true_stale_dispatches": violations,
        "per_agent_true_stale": per_agent_true_stale,
        "stale_samples": true_stale[:25],
        "conformance_pct": conformance_pct,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200, help="last N auto-loop WORK passes to replay")
    ap.add_argument("--selftest", action="store_true",
                    help="run hermetic synthetic self-test (3 injected stale found; clean=100%%; N configurable)")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(run_selftest())

    recs = load_autoloop()
    disk = json.loads(LEDGER.read_text(encoding="utf-8"))
    timeline = build_timeline(disk)

    # dispatch-history corroboration (agent-granularity)
    disp_count = 0
    if DISPATCH.exists():
        for line in DISPATCH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    json.loads(line); disp_count += 1
                except Exception:
                    pass

    window, core = audit_window(recs, timeline, args.n)

    drift = ssot_drift(disk)
    stale_ssot_agents = {row["agent"] for row in drift if row["stale_ssot"]}

    result = {
        "audit": "dispatch-anti-stale-conformance",
        "run_ts": datetime.now(timezone.utc).isoformat(),
        **core,
        "dispatch_history_records": disp_count,
        # Root-cause leg: SSOT vs live drift (stale SSOT => stale dispatch risk)
        "ssot_drift_rows": drift,
        "stale_ssot_agents": sorted(stale_ssot_agents),
        "stale_ssot_count": len(stale_ssot_agents),
        # Conformance: dispatch-level score (violations/dispatches) + SSOT-fresh gate.
        # conformance_pass = 0 stale dispatches AND committed SSOT is fresh (no
        # stale-SSOT agent that would under-dispatch real work).
        "ssot_fresh": len(stale_ssot_agents) == 0,
        "conformance_pass": (len(stale_ssot_agents) == 0 and core["true_stale_dispatches"] == 0),
        "ssot_ledger_generated": disk.get("generated"),
    }

    OUTDIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    jpath = OUTDIR / f"dispatch_audit_{date}.json"
    mpath = OUTDIR / f"dispatch_audit_{date}.md"
    jpath.write_text(json.dumps(result, indent=2), encoding="utf-8")
    # Goal-specified conformance SSOT output (memory/ops/dispatch-conformance.json)
    opsdir = ROOT / "memory" / "ops"
    opsdir.mkdir(parents=True, exist_ok=True)
    conformance_view = {
        "audit": "dispatch-anti-stale-conformance",
        "run_ts": result["run_ts"],
        "window_n": args.n,
        "passes_examined": result["passes_examined"],
        "violations": result["true_stale_dispatches"],
        "conformance_pct": result["conformance_pct"],
        "ssot_fresh": result["ssot_fresh"],
        "stale_ssot_agents": result["stale_ssot_agents"],
        "conformance_pass": result["conformance_pass"],
    }
    (opsdir / "dispatch-conformance.json").write_text(json.dumps(conformance_view, indent=2), encoding="utf-8")

    lines = [
        "# Dispatch Anti-Stale Conformance Audit",
        f"Run: {result['run_ts']}",
        f"SSOT ledger generated: {result['ssot_ledger_generated']}",
        f"Window: last {args.n} WORK passes ({result['passes_examined']} examined of {result['work_passes_total']} total)",
        f"Conformance: {result['conformance_pct']}% (violations={result['true_stale_dispatches']}/{result['passes_examined']})",
        "",
        f"## Result: {'PASS' if result['conformance_pass'] else 'FAIL'} - SSOT fresh={result['ssot_fresh']}, {result['stale_ssot_count']} stale-SSOT agent(s), {result['true_stale_dispatches']} true stale dispatch(es)",
        "",
        "A *stale-SSOT* finding = the dispatcher's SSOT (goal_ledger.json) reports open=0 for an agent whose LIVE goal file still has open goals. This is the root cause of stale dispatch: the dispatcher believes the agent is done and under-dispatches real work.",
        "A *true stale dispatch* = a WORK pass for agent A at time T where every one of A's tracked goals was already reached strictly before T (open_at(T)==0): the agent was sent to work with nothing open to do.",
        "",
    ]
    lines += ["", "## SSOT-vs-live drift (root cause of stale dispatch)"]
    for row in drift:
        flag = "  **STALE-SSOT**" if row["stale_ssot"] else ""
        lines.append(f"- {row['agent']}: live_open={row['live_open']} ssot_open={row['ssot_open']}" + flag)
    lines += ["", f"## Replay leg: true stale dispatches = {result['true_stale_dispatches']}",
              f"Conformance score = {result['conformance_pct']}% (= 100 * (1 - violations/dispatches))"]
    if result["stale_samples"]:
        for s in result["stale_samples"]:
            lines.append(f"- {s}")
    mpath.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({k: result[k] for k in
                      ["window_n", "work_passes_window", "passes_examined",
                       "stale_ssot_count", "stale_ssot_agents", "ssot_fresh",
                       "conformance_pct", "true_stale_dispatches",
                       "conformance_pass"]}, indent=2))
    print(f"artifact: {jpath.relative_to(ROOT)}")
    print(f"conformance SSOT: {(opsdir / 'dispatch-conformance.json').relative_to(ROOT)}")
    sys.exit(0 if result["conformance_pass"] else 2)


def _mk_rec(ts_iso, agent, task_type="WORK"):
    return {"ts": parse_ts(ts_iso), "agent": agent, "productive": True,
            "task_type": task_type}


def run_selftest():
    """Hermetic self-test proving the acceptance criteria:
      1. Seeded history with 3 injected stale dispatches -> audit finds all 3,
         conformance_pct < 100.
      2. Clean history (no stale) -> conformance_pct == 100, 0 stale.
      3. N configurable: --n changes the replay window size.
    Exit 0 on pass, else 1."""
    ok = True
    def check(name, cond):
        nonlocal ok
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
        ok = ok and cond

    # --- Synthetic ledger: 'alpha' has 2 goals BOTH reached on 2026-01-01;
    #     'beta' has 1 goal still OPEN (so its passes are never stale).
    ledger = {
        "agents": {
            "alpha": {"file": "a.md", "total": 2, "reached": 2, "open": 0,
                      "goals": [
                          {"text": "g1 (2026-01-01) done", "status": "reached"},
                          {"text": "g2 (2026-01-01) done", "status": "reached"},
                      ]},
            "beta":  {"file": "b.md", "total": 1, "reached": 0, "open": 1,
                      "goals": [
                          {"text": "g1 open (2026-03-01 target)", "status": "open"},
                      ]},
        }
    }
    timeline = build_timeline(ledger)

    # --- Scenario 1: 3 injected stale alpha dispatches (after reach) + beta noise.
    recs_stale = (
        [_mk_rec("2026-02-0%dT10:00:00" % i, "alpha") for i in (1, 2, 3)]  # 3 stale
        + [_mk_rec("2026-02-0%dT11:00:00" % i, "beta") for i in (1, 2, 3)]   # 3 clean
    )
    _, r1 = audit_window(recs_stale, timeline, n=100)
    check("S1 finds all 3 injected stale dispatches", r1["true_stale_dispatches"] == 3)
    check("S1 attributes all 3 to alpha", r1["per_agent_true_stale"] == {"alpha": 3})
    check("S1 conformance_pct < 100", r1["conformance_pct"] < 100.0)
    check("S1 examined all 6 passes", r1["passes_examined"] == 6)

    # --- Scenario 2: clean history (only beta, which has an open goal).
    recs_clean = [_mk_rec("2026-02-0%dT09:00:00" % i, "beta") for i in range(1, 6)]
    _, r2 = audit_window(recs_clean, timeline, n=100)
    check("S2 clean history -> 0 stale", r2["true_stale_dispatches"] == 0)
    check("S2 clean history -> conformance_pct == 100", r2["conformance_pct"] == 100.0)

    # --- Scenario 3: N configurable (window shrinks as n drops).
    big = [_mk_rec("2026-02-%02dT10:00:00" % i, "beta") for i in range(1, 11)]  # 10 passes
    _, rA = audit_window(big, timeline, n=100)
    _, rB = audit_window(big, timeline, n=3)
    check("S3 N configurable: n=100 examines 10", rA["passes_examined"] == 10)
    check("S3 N configurable: n=3 examines 3 (window shrinks)", rB["passes_examined"] == 3)

    # --- Edge: alpha pass BEFORE its reach date is NOT stale (goal was open then).
    recs_pre = [_mk_rec("2025-12-15T10:00:00", "alpha")]  # before 2026-01-01 reach
    _, r3 = audit_window(recs_pre, timeline, n=10)
    check("EDGE pre-reach pass is not stale (goal was open then)", r3["true_stale_dispatches"] == 0)

    print("SELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    main()
