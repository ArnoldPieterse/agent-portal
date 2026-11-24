#!/usr/bin/env python3
"""Convergence Velocity Briefing (Scribe goal, cycle 15).

Per cycle: a three-sentence briefing on convergence speed, derived from the
close-out reports' completion percentages.

Usage: python memory/scribe/convergence_brief.py [--cycle N]
Output: memory/synthesis/convergence-brief-cycle{N}.md
"""
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
SYNTH_DIR = BASE / "memory" / "synthesis"


def load_closeouts():
    """[(cycle_num, date_str, pct)] sorted by cycle number."""
    out = []
    pat = re.compile(r"closeout-cycle(\d+)-(\d{4}-\d{2}-\d{2})\.md")
    for f in SYNTH_DIR.glob("closeout-cycle*.md"):
        m = pat.match(f.name)
        if not m:
            continue
        txt = f.read_text(encoding="utf-8", errors="replace")
        pm = re.search(r"Fleet completion:\*\* (\d+)/(\d+) \(([\d.]+)%\)", txt)
        if not pm:
            pm = re.search(r"Completion rate \| ([\d.]+)%", txt)
            if not pm:
                continue
            pct = float(pm.group(1))
        else:
            pct = float(pm.group(3))
        out.append((int(m.group(1)), m.group(2), pct))
    return sorted(out, key=lambda x: (x[0], x[1]))

def generate(cycle_num):
    rows = load_closeouts()
    if not rows:
        return None, "no close-out reports found"
    cur = next(((n, d, p) for n, d, p in reversed(rows) if n == cycle_num), None)
    if cur is None:
        cur = rows[-1]
    cn, cd, pct = cur
    prev = None
    for n, d, p in reversed(rows):
        if (n, d) < (cn, cd):
            prev = (n, d, p)
            break
    L = ["# Convergence Velocity Briefing - Cycle %d" % cn, ""]
    if prev:
        delta = pct - prev[2]
        s1 = ("The fleet moved from %.1f%% (cycle %d, %s) to %.1f%% (cycle %d, %s): "
              "+%.1f points this cycle." % (prev[2], prev[0], prev[1], pct, cn, cd, delta))
        if delta > 0:
            days = max((datetime.strptime(cd, "%Y-%m-%d") -
                        datetime.strptime(prev[1], "%Y-%m-%d")).days, 1)
            rate = (100.0 - pct) / (delta / days)
            eta = (datetime.now(timezone.utc).date() +
                   __import__("datetime").timedelta(days=int(rate) + 1)).isoformat()
            s2 = ("At that pace, the remaining %.1f points need about %d more cycle(s); "
                  "projected full convergence near %s." % (100.0 - pct, int(rate) + 1, eta))
        else:
            s2 = "No forward movement this cycle; convergence is stalled at %.1f%%." % pct
        if delta > prev_delta(rows, cn, cd):
            s3 = "Convergence is ACCELERATING versus the prior cycle's gain."
        elif delta < prev_delta(rows, cn, cd):
            s3 = "Convergence is DECELERATING versus the prior cycle's gain."
        else:
            s3 = "Convergence is STEADY - same gain as the prior cycle."
    else:
        s1 = "First measured close-out: fleet at %.1f%% (cycle %d, %s)." % (pct, cn, cd)
        s2 = "No prior cycle to compare; this sets the baseline for velocity tracking."
        s3 = ("At a typical 10-20 point gain per cycle, full convergence is "
              "projected in %d-%d cycles." % (max(1, int((100-pct)/20)), max(1, int((100-pct)/10))))
    L += [s1, "", s2, "", s3, ""]
    return "\n".join(L), None

def prev_delta(rows, cn, cd):
    """Gain of the cycle before (cn,cd); 0 if unknown."""
    seq = [(n, d, p) for n, d, p in rows if (n, d) < (cn, cd)]
    if len(seq) < 2:
        return 0.0
    a, b = seq[-2], seq[-1]
    return b[2] - a[2]


def selftest():
    import tempfile
    global SYNTH_DIR
    real = SYNTH_DIR
    td = tempfile.mkdtemp()
    SYNTH_DIR = Path(td)
    for cn, date, pct in [(10,"2026-11-01",25.0),(14,"2026-11-20",30.0),(15,"2026-11-24",50.0)]:
        (SYNTH_DIR / ("closeout-cycle%d-%s.md" % (cn, date))).write_text(
            "# Cycle %d Close-Out Report\n\n**Fleet completion:** 40/80 (%.1f%%)" % (cn, pct), encoding="utf-8")
    rows = load_closeouts()
    ok = (len(rows) == 3 and rows[1][2] == 30.0 and rows[2][2] == 50.0)
    rep, err = generate(15)
    ok &= (err is None and rep is not None)
    lines = [l for l in rep.splitlines() if l and not l.startswith("#")]
    ok &= (len(lines) == 3)
    ok &= ("ACCELERATING" in rep)
    SYNTH_DIR = real
    print("Result: %s" % ("PASS" if ok else "FAIL"))
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    cycle_num = 15
    if "--cycle" in sys.argv:
        i = sys.argv.index("--cycle")
        if i + 1 < len(sys.argv):
            cycle_num = int(sys.argv[i + 1])
    rep, err = generate(cycle_num)
    if err:
        print(err)
        sys.exit(1)
    out = SYNTH_DIR / ("convergence-brief-cycle%d.md" % cycle_num)
    SYNTH_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(rep, encoding="utf-8")
    print("Convergence brief written to: %s" % out.relative_to(BASE))

