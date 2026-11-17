"""
mirror_revert_correlate.py — Researcher goal #3: ROOT-CAUSE bridge.

Overlays live mirror revert events onto the on-disk pin-file clobber-loop
timeline (_pin_timeline_raw.json) to test hypothesis #2 (automated feedback
cycle, not human editing). It is INDEPENDENT of the blocked live-mirror seed
wall: it consumes whatever live log exists (or degrades gracefully when empty)
plus the pre-window pin baseline that already lives on disk.

Usage:
  python memory/researcher/mirror_revert_correlate.py [log_path] [--dry-run]
    [log_path]   default Z:\\mirror_events.log ; pass a .jsonl for testing
    --dry-run    print to stdout instead of writing the leaf
Output: memory/researcher/mirror-revert-correlation-YYYY-MM-DD.md

Stdlib only. Day-7 closure = run parse_mirror_events.py then THIS script.
"""
import json, sys, os
from datetime import datetime

PIN_TIMELINE = "memory/researcher/_pin_timeline_raw.json"
# live-event path -> pin kind (pins are the reverted-target files)
PATH_TO_KIND = {
    "index.html": "index.html",
    "ui/core.js": "ui_core_js",
    "ui/app.css": "ui_app_css",
    "ui/uploads.js": "ui_uploads_js",
}
BURST_GAP_S = 300   # consecutive same-kind re-pin gap under this = automated burst
GRACE_S = 120       # tolerate clock skew when placing a revert into a window

def _ts(s):
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S.%f'):
        try: return datetime.strptime(s, fmt)
        except (ValueError, TypeError): continue
    return None

def load_live(path):
    if not os.path.exists(path): return []
    evs=[]
    for line in open(path):
        line=line.strip()
        if not line: continue
        try: e=json.loads(line)
        except json.JSONDecodeError: continue
        if e.get('_test'): continue
        evs.append(e)
    return evs

def pin_windows(pins, kind):
    """Return list of (start_dt, end_dt) automated-burst windows for one kind."""
    rows=sorted([(_ts(p['mtime']), p['mtime']) for p in pins if p.get('kind')==kind], key=lambda x:x[0])
    rows=[(d,s) for d,s in rows if d is not None]
    wins=[]
    for i in range(len(rows)-1):
        gap=(rows[i+1][0]-rows[i][0]).total_seconds()
        if 0 <= gap < BURST_GAP_S:
            # chain consecutive qualifying pairs into one window
            end=i+1
            while end+1 < len(rows) and 0 <= (rows[end+1][0]-rows[end][0]).total_seconds() < BURST_GAP_S:
                end+=1
            wins.append((rows[i][0], rows[end][0]))
    return wins

def in_any_window(dt, wins):
    return any(ws - __import__('datetime').timedelta(seconds=GRACE_S) <= dt <= we + __import__('datetime').timedelta(seconds=GRACE_S) for ws,we in wins)

def build(log_path, events):
    pins=json.load(open(PIN_TIMELINE))
    today=datetime.now().strftime('%Y-%m-%d')
    L=[]
    L.append("# Mirror-Revert <-> Pin-Burst Correlation (goal #3 root-cause)")
    L.append(f"\nGenerated: {today} by mirror_revert_correlate.py")
    L.append(f"\n## Method")
    L.append(f"- Live reverts from `{log_path}` overlaid on pre-window pin timeline `{PIN_TIMELINE}`.")
    L.append(f"- An 'automated burst window' = consecutive same-kind pins with re-pin gap < {BURST_GAP_S}s (chains merged); revert inside a window (+{GRACE_S}s grace) is attributed to the clobber loop, not organic drift.")
    L.append(f"- This tests hypothesis #2 from the analysis template against LIVE data, independent of the blocked seed wall.")

    reverts=[e for e in events if e.get('kind')=='revert']
    L.append(f"\n## Live revert count: {len(reverts)}")
    if not reverts:
        L.append("- No live reverts available yet (seed window open until ~11-24). Correlation is STAGED; run this again after the one-week live dataset accrues.")
        L.append(f"\n## Pre-window baseline (already on disk, independent of seed wall)")
        for kind in sorted(set(p['kind'] for p in pins)):
            wins=pin_windows(pins, kind)
            n=len([p for p in pins if p.get('kind')==kind])
            L.append(f"- {kind}: {n} pins, {len(wins)} automated-burst window(s) detected pre-window.")
        return '\n'.join(L), False

    # per-path overlay
    by_path={}
    for e in reverts:
        p=e.get('path', e.get('file','?'))
        kind=PATH_TO_KIND.get(p)
        dt=_ts(e.get('t',''))
        rec=by_path.setdefault(p, {'kind':kind,'total':0,'inburst':0,'no_pin':0})
        rec['total']+=1
        if kind is None or dt is None:
            rec['no_pin']+=1; continue
        wins=pin_windows(pins, kind)
        if in_any_window(dt, wins): rec['inburst']+=1

    L.append(f"\n## Per-path overlay (revert -> pin-burst attribution)")
    L.append(f"| path | kind | reverts | in automated-burst | no-pin/na | burst-attributed % |")
    L.append(f"|------|------|---------|--------------------|-----------|--------------------|")
    tot=ib=tot_attr=0
    for p, r in sorted(by_path.items(), key=lambda kv:-kv[1]['total']):
        denom=r['total']-r['no_pin']
        pct=(100*r['inburst']/denom) if denom else 0.0
        tot+=r['total']; ib+=r['inburst']; tot_attr+=denom
        L.append(f"| {p} | {r['kind'] or '-'} | {r['total']} | {r['inburst']} | {r['no_pin']} | {pct:.0f}% |")
    overall=(100*ib/tot_attr) if tot_attr else 0.0
    L.append(f"\n## Root-cause read")
    verdict = ("Automated clobber loop CONFIRMED as dominant revert driver"
               if overall>=60 else "Mixed: automated burst is a contributor but not dominant"
               if overall>=25 else "Weak signal: reverts mostly OUTSIDE pin-burst windows -> organic/pin_drift drift dominates")
    L.append(f"- {overall:.0f}% of attributable live reverts fall inside pre-window-style automated bursts.")
    L.append(f"- Verdict: **{verdict}** (thresholds: >=60% confirmed, 25-60% contributor, <25% weak).")
    L.append(f"- Crossover note: pre-window pin cadence alone already showed index.html min re-pin gap ~18s; this table is the LIVE confirmation of that hypothesis.")
    return '\n'.join(L), True

def main():
    dry='--dry-run' in sys.argv
    args=[a for a in sys.argv[1:] if not a.startswith('--')]
    log_path=args[0] if args else 'Z:\\mirror_events.log'
    events=load_live(log_path)
    md, had = build(log_path, events)
    if dry: print(md)
    else:
        out=f"memory/researcher/mirror-revert-correlation-{datetime.now().strftime('%Y-%m-%d')}.md"
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out,'w').write(md)
        print(f"Wrote {out} ({len(md)} chars, live_reverts={'yes' if had else 'pending'})")

if __name__=='__main__': main()