"""Generate memory/ops/efficiency-index.jsonl from REAL ops sources.

Builder cycle-17 goal 1 (Convergence API Endpoint) names this file as a required
source, but it did not exist. This builds it per-cycle from files that DO exist,
citing each field's source so no value is fabricated:
  - velocity        = goals_completed / passes_used   <- cycle-efficiency.json
  - rework_rate     = 1 - rework_score/100            <- autonomy-score.json (rework high => low rework)
  - idle_fraction   = wasted_pass_count / total_passes<- cycle-efficiency-<c>.json
  - composite       = velocity * (1-rework_rate) * (1-idle_fraction)
Fields with no source data are null (never invented).
"""
import pathlib, json, glob, os
OPS = pathlib.Path('memory/ops')
def jread(p):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    except Exception:
        return None

# collect cycle durations (real)
durs = {}
for line in (OPS/'cycle-durations.jsonl').read_text(encoding='utf-8').splitlines():
    line=line.strip()
    if not line: continue
    d=json.loads(line); durs[d['cycle']]=d

# autonomy-score rework -> global rework_rate (single latest snapshot)
aus = jread(OPS/'autonomy-score.json') or {}
rework_score = aus.get('components',{}).get('rework_score')
rework_rate = round(1 - rework_score/100.0, 4) if rework_score is not None else None

# merge all cycle-efficiency*.json records per cycle (dedupe), then emit one row each
bycycle={}
for f in sorted(glob.glob(str(OPS/'cycle-efficiency*.json'))):
    d=jread(f)
    if not d: continue
    c=d.get('cycle')
    try: c=int(c)
    except Exception: continue
    bycycle.setdefault(c,{}).update({k:v for k,v in d.items()})

rows=[]
for c in sorted(bycycle):
    m=dict(bycycle[c])
    gc=m.get('goals_completed'); pu=m.get('passes_used')
    velocity=round(gc/pu,4) if (gc is not None and pu) else None
    # idle: per-file total_passes can disagree with passes_used (1 vs 142 on c15);
    # use the consistent denominator passes_used and flag the conflict in notes.
    waste=m.get('wasted_pass_count'); tot=m.get('total_passes')
    idle=None; note=None
    if waste is not None:
        if pu: idle=round(waste/pu,4)
        elif tot: idle=round(waste/tot,4)
        if tot and pu and tot!=pu:
            note=f'per-file total_passes={tot} inconsistent with passes_used={pu}; used passes_used'
    composite=round(velocity*(1-rework_rate)*(1-idle),4) if (velocity is not None and rework_rate is not None and idle is not None) else None
    dur=durs.get(c)
    row={
        'cycle': c,
        'goals_completed': gc,
        'passes_used': pu,
        'velocity_goals_per_pass': velocity,
        'rework_rate': rework_rate,
        'idle_fraction': idle,
        'efficiency_index': composite,
        'duration_hours': (dur or {}).get('duration_hours'),
        'sources': {
            'velocity': 'memory/ops/cycle-efficiency.json',
            'rework_rate': 'memory/ops/autonomy-score.json',
            'idle_fraction': 'memory/ops/cycle-efficiency-{}.json'.format(c) if waste is not None else None,
            'duration_hours': 'memory/ops/cycle-durations.jsonl' if dur else None,
        },
    }
    if note: row['notes']=note
    rows.append(row)

out=OPS/'efficiency-index.jsonl'
with out.open('w',encoding='utf-8') as fh:
    for r in rows: fh.write(json.dumps(r)+'\n')
print('wrote', out.resolve(), 'rows=', len(rows))
for r in rows: print(' ', json.dumps(r))
