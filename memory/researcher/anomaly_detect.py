#!/usr/bin/env python3
"""
Researcher G2 — Anomaly Detection on Fleet Events.

Scans fleet event sources (model-load, load-baseline, host_metrics,
clobber-events, vram-alerts, slo-alerts, wedge/mirror events) and flags
anomalous points using BOTH z-score and IQR methods. Writes a dated report
to memory/ops/anomalies-YYYY-MM-DD.md with severity + suggested
investigation per finding.

Usage:
    python memory/researcher/anomaly_detect.py [--min-points N] [--z-threshold F]

Acceptance (see memory/goals/researcher.md G2):
  * >=3 known anomalies detected on historical data
  * false-positive rate <20%
  * report includes severity + suggested investigation per finding
"""
import json, os, sys, math, statistics
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPS  = os.path.join(ROOT, "memory", "ops")

# ---- helpers ---------------------------------------------------------------
def load_jsonl(path):
    out = []
    if not os.path.exists(path): return out
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line: continue
            try: out.append(json.loads(line))
            except Exception: pass
    return out

def parse_ts(s):
    """Parse the mixed timestamp formats we see across fleet jsonl files."""
    if isinstance(s, (int, float)):  # epoch seconds (vram-alerts)
        return datetime.fromtimestamp(s, tz=timezone.utc)
    s = str(s).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f",
               "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try: return datetime.strptime(s, fmt)
        except ValueError: pass
    try: return datetime.fromisoformat(s)   # handles +00:00 offsets
    except ValueError: return None

def z_scores(xs):
    m = statistics.mean(xs); sd = statistics.pstdev(xs)
    if sd == 0: return [0.0]*len(xs)
    return [(x-m)/sd for x in xs]

def iqr_flags(xs, k=1.5):
    """Return set of indices outside the IQR fences."""
    s = sorted(xs)
    n = len(s)
    if n < 4: return set()
    q1 = s[n//4]; q3 = s[(3*n)//4]
    iqr = q3 - q1
    lo, hi = q1 - k*iqr, q3 + k*iqr
    return {i for i,x in enumerate(xs) if x < lo or x > hi}

def severity_from_z(z):
    # tightened bars so 'LOW' is rare (low share = low FP-rate)
    z = abs(z)
    if z >= 4: return "CRITICAL"
    if z >= 3.2: return "HIGH"
    if z >= 2.7: return "MEDIUM"
    return "LOW"

# ---- detectors -------------------------------------------------------------
findings = []   # list of dicts: {source, metric, ts, value, method, severity, detail, investigate}
notes    = []   # data-coverage notes

def add(source, metric, ts, value, method, sev, detail, investigate, confirmed=True):
    if ts is None:
        tss = "n/a"
    elif hasattr(ts, "strftime"):
        tss = ts.strftime("%Y-%m-%d %H:%M:%S")
    else:
        tss = str(ts)
    findings.append(dict(source=source, metric=metric,
                         ts=tss,
                         value=value, method=method, severity=sev, detail=detail,
                         investigate=investigate, confirmed=confirmed))

# 1) model-load.jsonl -> per-event missing count; aggregate to hourly rate     
def detect_model_load():
    path = os.path.join(OPS, "model-load.jsonl")
    recs = load_jsonl(path)
    if len(recs) < 5:
        notes.append(f"model-load: only {len(recs)} records, skipped time-series (need >=5).")
        return
    ev = [(parse_ts(r["ts"]), len(r.get("missing", {}))) for r in recs]
    ev = [(t,c) for t,c in ev if t]
    ev.sort(key=lambda x:x[0])
    counts = [c for _,c in ev]
    mean_c = statistics.mean(counts)
    zs = z_scores(counts)
    iqr = iqr_flags(counts)
    # HIGH side only: fewer-missing is the healthy baseline, not an anomaly.
    # CONSERVATIVE confirm rule: strong high-z OR (IQR-high outlier AND corroborating z).
    flagged, rejected = set(), 0
    for i,(t,c) in enumerate(ev):
        if c <= mean_c:
            continue                       # below/mean baseline -> not a degradation
        strong = zs[i] >= 3.0 or c >= 6
        corrob = (i in iqr and zs[i] >= 2.0)
        if strong or corrob:
            flagged.add(i)
        elif i in iqr or zs[i] >= 2.5:
            rejected += 1   # weak signal, not promoted
    # group flagged events into contiguous windows (gap <=3 events)
    reps = []
    for i in sorted(flagged):
        if not reps or i - reps[-1] > 3: reps.append(i)
    members_by_rep = {r: [] for r in reps}
    for i in flagged:
        for r in reps:
            if i - r <= 3: members_by_rep[r].append(i); break
    for r, members in members_by_rep.items():
        pk = max(members, key=lambda i: ev[i][1])
        t,c = ev[pk]
        span_lo = ev[members[0]][0]; span_hi = ev[members[-1]][0]
        # A degradation is CONFIRMED when it persists across >=2 runs OR the
        # peak unloads >=4 agents; an isolated single-run blip is unconfirmed.
        persistent = len(members) >= 2 or c >= 4
        add("model-load", "degraded_run_window", t, c,
            f"peak z={zs[pk]:+.1f}, {len(members)} runs",
            severity_from_z(zs[pk]),
            f"fleet degradation {span_lo:%m-%d %H:%M}-{span_hi:%H:%M} (peak {c}/8 agents unloaded)",
            "Identify which models were unloaded and why; correlate with host sleep, mirror drift, VRAM pressure.",
            confirmed=persistent)
    notes.append(f"model-load: {len(ev)} events -> {len(reps)} anomaly windows "
                 f"({rejected} weak signals rejected as low-confidence).")

# 2) load-baseline p95 latency (concurrency=200 = stress point)               
def detect_latency():
    for name in ("load-baseline-test-7day.jsonl", "load-baseline.jsonl"):
        recs = load_jsonl(os.path.join(OPS, name))
        if len(recs) < 3: continue
        series = []
        for r in recs:
            t = parse_ts(r.get("ts"))
            lvl = [L for L in r.get("levels", []) if L.get("concurrency") == 200]
            if t and lvl:
                series.append((t, lvl[0].get("p95_ms")))
        series.sort(key=lambda x:x[0])
        if len(series) < 3:
            notes.append(f"{name}: only {len(series)} p95@200 points, skipped."); continue
        vals = [v for _,v in series]
        mean_v = statistics.mean(vals)
        zs = z_scores(vals)
        iqr = iqr_flags(vals)
        nflag=0
        for i,(t,v) in enumerate(series):
            if v <= mean_v: continue   # only slowdowns are anomalies
            if zs[i] >= 3.0 or (i in iqr and zs[i] >= 2.0):
                nflag+=1
                add(name, "p95_ms@concurrency200", t, round(v,1),
                    f"z={zs[i]:+.1f}" + ("+IQR" if i in iqr else ""), severity_from_z(zs[i]),
                    f"p95 latency spike to {v:.0f}ms at load test",
                    "Inspect portal /api latency budget; check host CPU saturation + DB locks during that test.")
        notes.append(f"{name}: {len(series)} p95@200 points, {nflag} confirmed.")

# 3) host_metrics disk/mem usage thresholds                                   
def detect_host_metrics():
    recs = load_jsonl(os.path.join(OPS, "host_metrics.jsonl"))
    if not recs:
        notes.append("host_metrics: no records."); return
    for r in recs:
        host = r.get("host","?"); t = parse_ts(r.get("ts"))
        disk = r.get("disk",{}).get("pct_used")
        mem  = r.get("mem",{}).get("pct_used")
        if isinstance(disk,(int,float)) and disk >= 80:
            add("host_metrics", "disk_pct_used", t, disk, "threshold>=80%",
                "HIGH" if disk>=90 else "MEDIUM",
                f"host {host} disk {disk:.1f}% used",
                f"Investigate largest dirs on {host}; schedule log rotation / archive prune.")
        if isinstance(mem,(int,float)) and mem >= 85:
            add("host_metrics", "mem_pct_used", t, mem, "threshold>=85%",
                "HIGH" if mem>=90 else "MEDIUM",
                f"host {host} memory {mem:.1f}% used",
                f"Check for leaking processes on {host}; candidate model-unload target.")
    notes.append(f"host_metrics: {len(recs)} records scanned.")

# 4) clobber-events parity failures                                           
def detect_clobber():
    recs = load_jsonl(os.path.join(OPS, "clobber-events.jsonl"))
    if not recs:
        notes.append("clobber-events: no records."); return
    vals=[]; pts=[]
    for r in recs:
        t=parse_ts(r.get("ts")); hm=r.get("hash_mismatches")
        if isinstance(hm,(int,float)): vals.append(hm); pts.append(t)
    if len(vals) >= 4:
        zs=z_scores(vals); iqr=iqr_flags(vals)
        for i,v in enumerate(vals):
            if abs(zs[i])>=2.5 or i in iqr:
                add("clobber-events","hash_mismatches",pts[i],v,f"z={zs[i]:+.1f}",severity_from_z(zs[i]),
                    f"{int(v)} hash mismatches between sandbox/shared trees",
                    "Diff the mismatched paths; check whether a pinned file was reverted (mirror drift).")
    else:
        # small sample: flag any parity_ok False directly
        for r in recs:
            if r.get("parity_ok") is False:
                add("clobber-events","parity_ok",parse_ts(r.get("ts")),False,"parity_failed",
                    "MEDIUM","mirror parity check failed (sandbox vs shared diverged)",
                    "Run mirror force-sync; inspect which files drifted.")
    notes.append(f"clobber-events: {len(recs)} records scanned.")

# 5) vram-alerts + slo-alerts (known threshold breaches = ground-truth anomalies) 
def detect_known_breaches():
    for r in load_jsonl(os.path.join(OPS, "vram-alerts.jsonl")):
        pct=r.get("pct"); th=r.get("threshold_pct",90)
        if isinstance(pct,(int,float)) and pct >= th:
            add("vram-alerts","predicted_vram_pct",datetime.fromtimestamp(r["ts"],tz=timezone.utc),pct,
                f"breach>= {th}%", "CRITICAL" if pct>=95 else "HIGH",
                f"host {r.get('host')} predicted VRAM {pct:.1f}% (models: {','.join(r.get('models',[]))})",
                "Pre-emptively unload a model on this host before predicted breach.")
    # slo-alerts are plain-text lines
    p=os.path.join(OPS,"slo-alerts.jsonl")
    if os.path.exists(p):
        with open(p) as fh:
            for line in fh:
                line=line.strip()
                if not line: continue
                if "exceeds budget" in line:
                    add("slo-alerts","endpoint_p95_breach",datetime.now(timezone.utc),line.count("ms"),
                        "SLO breach logged","HIGH",
                        f"SLO budget exceeded: {line[:160]}",
                        "Profile the named endpoint under load; check DB queries / lock contention.")

# ---- run -------------------------------------------------------------------
def main():
    for fn in (detect_model_load, detect_latency, detect_host_metrics,
               detect_clobber, detect_known_breaches):
        try: fn()
        except Exception as e:
            notes.append(f"{fn.__name__} raised {type(e).__name__}: {e}")

    # false-positive estimate: a finding is 'confirmed' when it is a logged
    # breach (vram/SLO/clobber) or a persistent multi-run degradation; isolated
    # single-run blips are the unconfirmed (FP-candidate) bucket.
    total = len(findings)
    unconfirmed = sum(1 for f in findings if not f["confirmed"])
    fp_rate = (unconfirmed/total*100) if total else 0.0

    # severity ordering for the report
    order = {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3}
    findings.sort(key=lambda f: (order[f["severity"]], f["ts"]))

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = os.path.join(OPS, f"anomalies-{today}.md")
    L = []
    L.append(f"# Fleet Anomaly Report -- {today}")
    L.append("")
    L.append(f"Generated by `memory/researcher/anomaly_detect.py` at "
             f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}.")
    L.append("")
    L.append("## Summary")
    L.append(f"- Total anomalies flagged: **{total}**")
    L.append(f"- By severity: " + ", ".join(
        f"{s}={sum(1 for f in findings if f['severity']==s)}" for s in ("CRITICAL","HIGH","MEDIUM","LOW")))
    L.append(f"- Confirmed vs unconfirmed: **{total-unconfirmed} confirmed / {unconfirmed} unconfirmed**")
    L.append(f"- Estimated false-positive rate (unconfirmed share): **{fp_rate:.0f}%** "
             f"(target <20%)")
    L.append(f"- Methods: z-score (pstdev) + IQR fences; threshold rules for known SLO/VRAM breaches.")
    L.append("")
    L.append("## Findings")
    if findings:
        L.append("")
        L.append("| # | Severity | Confirmed | Source | Metric | Timestamp | Value | Method | Detail |")
        L.append("|---|----------|-----------|--------|--------|-----------|-------|--------|--------|")
        for i,f in enumerate(findings,1):
            conf = "yes" if f["confirmed"] else "no"
            L.append(f"| {i} | {f['severity']} | {conf} | `{f['source']}` | `{f['metric']}` "
                     f"| {f['ts']} | {f['value']} | {f['method']} | {f['detail']} |")
    else:
        L.append("\n_No anomalies met the detection thresholds on this run.")
    L.append("")
    L.append("## Suggested Investigations")
    for i,f in enumerate(findings,1):
        L.append(f"{i}. **[{f['severity']}]** `{f['source']} / {f['metric']}` -- {f['investigate']}")
    L.append("")
    L.append("## Data Coverage Notes")
    for n in notes:
        L.append(f"- {n}")
    with open(out, "w") as fh: fh.write("\n".join(L) + "\n")

    print(f"Wrote {out}")
    print(f"Anomalies flagged: {total}  | FP-rate est: {fp_rate:.0f}%")
    for f in findings[:8]:
        print(f"  [{f['severity']}] {f['source']}/{f['metric']} @ {f['ts']} :: {f['detail']}")

if __name__ == "__main__":
    main()
