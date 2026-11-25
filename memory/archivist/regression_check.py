#!/usr/bin/env python
"""Convergence Regression Test runner (Archivist goal #4, cycle 18).

Spec: memory/archivist/convergence-regression-spec.md
Reads live data, runs 5 checks over the last-3-cycle window, writes a report,
exit 0 = all PASS/SKIP (lock may advance), exit 1 = any FAIL (lock resets).

Usage: python memory/archivist/regression_check.py [--window 3]
"""
import json, sys, re, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]
TREND = ROOT / "memory/scribe/autonomy-trend.jsonl"
CLOSEOUT = ROOT / "memory/ops/cycle-closeout.jsonl"
HIST = ROOT / "memory/ops/cycle-history-consolidated.jsonl"
BLOCKERS = ROOT / "memory/ops/blockers.md"
OUT_JSON = ROOT / "memory/archivist/regression-report.json"
OUT_MD = ROOT / "memory/archivist/regression-report.md"

SCORE_DROP_BAND = 2.0        # RC1/RC2 autonomy
INTERV_RISE_BAND = 1        # RC2 interventions rise tolerance
COMPL_DROP_BAND = 5.0       # RC2 completion drop tolerance
REWORK_FLOOR = 90.0         # RC4 decision-quality floor
SLOPE_TOL = 0.5             # RC5 interventions/cycle slope tolerance


def load_jsonl(p):
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def latest_cycles(rows, key, n):
    """Return up to n most-recent rows sorted ascending by cycle."""
    have = [r for r in rows if isinstance(r.get(key), int)]
    have.sort(key=lambda r: r[key])
    return have[-n:]


def slope(vals):
    """Least-squares slope over equally-spaced indices (per-cycle)."""
    n = len(vals)
    if n < 2:
        return None
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(vals) / n
    den = sum((x - mx) ** 2 for x in xs)
    if den == 0:
        return None
    return sum((xs[i] - mx) * (vals[i] - my) for i in range(n)) / den


def new_blocker_classes(window_start_date):
    """Parse blockers.md: a class is 'new' if its dated OPS-NOTE header >= window start."""
    if not BLOCKERS.exists():
        return [], "source-missing"
    text = BLOCKERS.read_text(encoding="utf-8")
    # split into blocks by section header
    blocks = re.split(r"(?m)^## ", text)
    new = []
    seen_all = set()
    for b in blocks:
        head = b[:200]
        mdate = re.search(r"OPS-NOTE\s+(\d{4}-\d{2}-\d{2})", head)
        mclass = re.search(r"\*\*Class:\*\*\s*([^\n]+)", b)
        if not (mdate and mclass):
            continue
        cls = mclass.group(1).strip()
        seen_all.add(cls)
        try:
            d = datetime.date.fromisoformat(mdate.group(1))
        except ValueError:
            continue
        if window_start_date and d >= window_start_date:
            new.append((mdate.group(1), cls))
    return new, "ok"


def main():
    window = 3
    for i, a in enumerate(sys.argv):
        if a == "--window" and i + 1 < len(sys.argv):
            window = int(sys.argv[i + 1])

    trend = load_jsonl(TREND)
    closeout = load_jsonl(CLOSEOUT)
    hist = load_jsonl(HIST)

    tcur = latest_cycles(trend, "cycle", window)
    checks = {}
    notes = []

    # --- RC1: autonomy non-regression (delta band) ---
    if tcur:
        last = tcur[-1]
        d = last.get("delta_from_prev")
        if d is None:
            checks["RC1"] = {"status": "SKIP", "reason": "no delta (first record)"}
        else:
            ok = d >= -SCORE_DROP_BAND
            checks["RC1"] = {"status": "PASS" if ok else "FAIL",
                             "cycle": last["cycle"], "delta": d, "band": -SCORE_DROP_BAND}
    else:
        checks["RC1"] = {"status": "SKIP", "reason": "no trend data"}

    # --- RC2: multi-metric delta band (current vs prior) ---
    r2 = {}
    if len(tcur) >= 2:
        prev, cur = tcur[-2], tcur[-1]
        sd = cur["score"] - prev["score"]
        r2["autonomy_score"] = {"delta": round(sd, 2), "breach": sd < -SCORE_DROP_BAND}
    # interventions
    icur = latest_cycles(closeout, "cycle", window)
    if len(icur) >= 2:
        iprev, icurr = icur[-2], icur[-1]
        idelta = (icurr.get("interventions_count") or 0) - (iprev.get("interventions_count") or 0)
        r2["interventions_per_cycle"] = {"delta": idelta, "breach": idelta > INTERV_RISE_BAND}
    # completion
    hcur = latest_cycles(hist, "cycle", window)
    if len(hcur) >= 2:
        pa, ca = hcur[-2].get("completion_pct"), hcur[-1].get("completion_pct")
        if pa is not None and ca is not None:
            cd = ca - pa
            r2["completion_pct"] = {"delta": round(cd, 2), "breach": cd < -COMPL_DROP_BAND}
    if not r2:
        checks["RC2"] = {"status": "SKIP", "reason": "insufficient paired cycles"}
    else:
        breaches = [k for k, v in r2.items() if v.get("breach")]
        checks["RC2"] = {"status": "PASS" if not breaches else "FAIL",
                         "metrics": r2, "breaches": breaches}

    # --- RC3: new blocker classes in window ---
    # window start date ~ earliest cycle's start_date from closeout, else today-~72d
    ws = None
    if icur:
        sd = icur[0].get("start_date")
        if sd:
            try:
                ws = datetime.date.fromisoformat(sd)
            except ValueError:
                ws = None
    if ws is None:
        ws = datetime.date.today() - datetime.timedelta(days=window * 24)
    new_cls, src = new_blocker_classes(ws)
    checks["RC3"] = {"status": "PASS" if len(new_cls) == 0 else "FAIL",
                     "new_classes": [c for _, c in new_cls],
                     "window_start": str(ws), "source": src}

    # --- RC4: decision-quality floor (rework_score) ---
    if tcur:
        cb = tcur[-1].get("component_breakdown") or {}
        rw = cb.get("rework_score")
        if rw is None:
            checks["RC4"] = {"status": "SKIP", "reason": "no rework_score component"}
        else:
            ok = rw >= REWORK_FLOOR
            checks["RC4"] = {"status": "PASS" if ok else "FAIL",
                             "cycle": tcur[-1]["cycle"], "rework_score": rw, "floor": REWORK_FLOOR}
    else:
        checks["RC4"] = {"status": "SKIP", "reason": "no trend data"}

    # --- RC5: intervention trend slope ---
    if len(icur) >= 2:
        vals = [c.get("interventions_count") or 0 for c in icur]
        s = slope(vals)
        if s is None:
            checks["RC5"] = {"status": "SKIP", "reason": "slope undefined"}
        else:
            ok = s <= SLOPE_TOL
            checks["RC5"] = {"status": "PASS" if ok else "FAIL",
                             "slope_per_cycle": round(s, 3), "tolerance": SLOPE_TOL,
                             "values": vals}
    else:
        checks["RC5"] = {"status": "SKIP", "reason": "fewer than 2 cycles"}

    fails = [k for k, v in checks.items() if v["status"] == "FAIL"]
    verdict = "PASS" if not fails else "FAIL"
    report = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "window_cycles": window,
        "verdict": verdict,
        "failing_checks": fails,
        "checks": checks,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    fail_str = ", ".join(fails)
    if fails:
        verdict_line = "**VERDICT: {}** - failing: {}".format(verdict, fail_str)
    else:
        verdict_line = "**VERDICT: {}** (lock may advance)".format(verdict)
    lines = ["# Convergence Regression Report",
             "*generated {} | window={} cycles*".format(report["generated_at"], window), "",
             verdict_line,
             ""]
    for k in sorted(checks):
        v = checks[k]
        lines.append(f"- **{k}**: {v['status']}  `{json.dumps({kk: vv for kk, vv in v.items() if kk != 'status'})}`")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
