#!/usr/bin/env python3
"""
Goal #10 - Cycle Efficiency Report.
At cycle close, compute per-cycle efficiency metrics and write to
memory/ops/cycle-efficiency-{N}.json:
    total_passes, productive_pct, goals_closed_per_agent,
    time_to_100pct, avg_pass_duration, wasted_pass_count.

Acceptance criteria (verified via --self-test):
  * on synthetic cycle data, ALL required fields are populated;
  * productive_pct matches a manual count from the pass records within 5%;
  * report generation completes in <10s.

Live run: reads autoloop.jsonl (cycle window) + closed_topics.json +
mode-transitions.jsonl. Real cycle data is small, so live numbers are
small but every field is populated; the self-test proves correctness on
data with a known ground-truth productive count.
"""
import json, os, sys, time, tempfile
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUTOLOOP = os.path.join(ROOT, "memory", "ops", "autoloop.jsonl")
CLOSED = os.path.join(ROOT, "memory", "goals", "closed_topics.json")
TRANSITIONS = os.path.join(ROOT, "memory", "ops", "mode-transitions.jsonl")
OUT_DIR = os.path.join(ROOT, "memory", "ops")

REQUIRED_FIELDS = ["total_passes", "productive_pct", "goals_closed_per_agent",
                   "time_to_100pct_h", "avg_pass_duration_s", "wasted_pass_count"]


def _parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def _read_jsonl(p):
    out = []
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def is_productive(rec):
    """Productive per productive-pass-definition.md operational signal."""
    if isinstance(rec.get("productive"), bool):
        return rec["productive"]
    ev = rec.get("evidence_files")
    if isinstance(ev, (list, tuple)):
        return len([x for x in ev if str(x).strip()]) > 0
    return False


def compute(passes, closed_topics, transitions, now=None):
    """Core metrics. Pure -> importable + self-testable."""
    now = now or datetime.now(timezone.utc)
    durations = [float(p["duration_s"]) for p in passes if isinstance(p.get("duration_s"), (int, float))]
    total = len(passes)
    prod = sum(1 for p in passes if is_productive(p))
    productive_pct = round(100.0 * prod / total, 2) if total else 0.0
    wasted = total - prod
    avg_dur = round(sum(durations) / len(durations), 3) if durations else 0.0

    # goals_closed_per_agent: count closed topics per agent (cycle window = all known).
    per_agent = {}
    for c in closed_topics:
        ag = str(c.get("agent") or "unknown").strip().lower() or "unknown"
        per_agent[ag] = per_agent.get(ag, 0) + 1

    # time_to_100pct: hours from cycle start (earliest transition) to first completion
    # proxy = a MAINTENANCE/IDLE entry with goal_pct>=95 or trigger containing closeout.
    t_start = None
    t_done = None
    cands = []
    for tr in transitions:
        dt = _parse_ts(tr.get("ts") or tr.get("timestamp"))
        if dt is None:
            continue
        to_mode = str(tr.get("to_mode", "")).upper()
        gp = tr.get("goal_pct")
        trigger = str(tr.get("trigger", "")).lower()
        cands.append(dt)
        if t_start is None or dt < t_start:
            t_start = dt
        if (to_mode in ("MAINTENANCE", "IDLE") and isinstance(gp, (int, float)) and gp >= 95) \
           or "closeout" in trigger or "cycle_close" in trigger:
            if t_done is None or dt < t_done:
                t_done = dt
    time_to_100 = None
    if t_start is not None and t_done is not None and t_done >= t_start:
        time_to_100 = round((t_done - t_start).total_seconds() / 3600.0, 3)

    return {
        "total_passes": total,
        "productive_pct": productive_pct,
        "goals_closed_per_agent": per_agent,
        "time_to_100pct_h": time_to_100,
        "avg_pass_duration_s": avg_dur,
        "wasted_pass_count": wasted,
    }


def run(cycle="latest", hours=24, now=None):
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours)
    allp = _read_jsonl(AUTOLOOP)
    passes = []
    for p in allp:
        dt = _parse_ts(p.get("timestamp") or p.get("ts"))
        if dt is None or dt >= cutoff:
            passes.append(p)   # keep undated + recent
    closed = json.load(open(CLOSED, encoding="utf-8")) if os.path.exists(CLOSED) else []
    transitions = _read_jsonl(TRANSITIONS)
    m = compute(passes, closed, transitions, now=now)
    out = {"cycle": cycle, "window_hours": hours, "generated": now.isoformat()}
    out.update(m)
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"cycle-efficiency-{cycle}.json")
    json.dump(out, open(path, "w", encoding="utf-8"), indent=2)
    return out, os.path.relpath(path, ROOT).replace("\\", "/")


def self_test():
    now = datetime(2026, 11, 24, 12, 0, 0, tzinfo=timezone.utc)
    # 40 passes; exactly 28 productive -> 70.0%. durations alternate 1.0/3.0 -> avg 2.0.
    passes = []
    for i in range(40):
        passes.append({
            "timestamp": (now - timedelta(minutes=40 - i)).isoformat(),
            "agent": ["builder", "verifier", "researcher"][i % 3],
            "productive": (i < 28),           # first 28 productive
            "duration_s": 1.0 if i % 2 == 0 else 3.0,
            "evidence_files": ["x.md"] if i < 28 else [],
        })
    closed_topics = [
        {"agent": "builder", "at": "2026-11-24"},
        {"agent": "builder", "at": "2026-11-24"},
        {"agent": "verifier", "at": "2026-11-24"},
        {"agent": "researcher", "at": "2026-11-24"},
    ]
    transitions = [
        {"ts": (now - timedelta(hours=10)).isoformat(), "to_mode": "WORK", "trigger": "cycle_start"},
        {"ts": (now - timedelta(hours=2)).isoformat(), "to_mode": "MAINTENANCE",
         "goal_pct": 95.0, "trigger": "cycle_closeout"},
    ]

    t0 = time.time()
    m = compute(passes, closed_topics, transitions, now=now)
    elapsed = time.time() - t0

    # manual ground truth: productive count from the records themselves
    manual_prod = sum(1 for p in passes if p["productive"])
    manual_pct = 100.0 * manual_prod / len(passes)
    ok_fields = all(k in m for k in REQUIRED_FIELDS)
    ok_pct = abs(m["productive_pct"] - manual_pct) <= 5.0
    ok_waste = m["wasted_pass_count"] == (len(passes) - manual_prod)
    ok_avg = abs(m["avg_pass_duration_s"] - 2.0) < 1e-6
    ok_agent = m["goals_closed_per_agent"] == {"builder": 2, "verifier": 1, "researcher": 1}
    ok_time = abs(m["time_to_100pct_h"] - 8.0) < 1e-6   # 10h start -> 2h ago closeout = 8h
    ok_speed = elapsed < 10.0

    print(f"required fields present: {ok_fields}")
    print(f"productive_pct={m['productive_pct']} manual={manual_pct} within5%={ok_pct}")
    print(f"wasted_pass_count={m['wasted_pass_count']} (expect {len(passes)-manual_prod}) ok={ok_waste}")
    print(f"avg_pass_duration_s={m['avg_pass_duration_s']} (expect 2.0) ok={ok_avg}")
    print(f"goals_closed_per_agent={m['goals_closed_per_agent']} ok={ok_agent}")
    print(f"time_to_100pct_h={m['time_to_100pct_h']} (expect 8.0) ok={ok_time}")
    print(f"generation time={elapsed:.4f}s (<10s) ok={ok_speed}")
    if not (ok_fields and ok_pct and ok_waste and ok_avg and ok_agent and ok_time and ok_speed):
        print("SELF-TEST: FAIL")
        sys.exit(1)
    print("SELF-TEST: ALL PASS")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        cyc = "latest"
        hrs = 24
        a = sys.argv[1:]
        i = 0
        while i < len(a):
            if a[i] == "--cycle" and i + 1 < len(a):
                cyc = a[i + 1]; i += 2; continue
            if a[i] == "--hours" and i + 1 < len(a):
                hrs = int(a[i + 1]); i += 2; continue
            i += 1
        out, rel = run(cycle=cyc, hours=hrs)
        print(f"Cycle efficiency [{cyc}]: passes={out['total_passes']} "
              f"productive%={out['productive_pct']} wasted={out['wasted_pass_count']} "
              f"avg_dur={out['avg_pass_duration_s']}s time_to_100pct={out['time_to_100pct_h']}h")
        print("output ->", rel)
