#!/usr/bin/env python
"""Seat Unavailability Impact Model v2 (Researcher goal #8).
Extends cycle-16 static-rate model with a recency-weighted predictive component.

Deliverable: per-seat 7-day unavailability probability forecast -> unavailability-forecast.json
Backtest: walk-forward (rolling origin) precision/recall/F1 for 'unavailable' predictions,
computed on the ACTUAL available window and reported honestly against the AC's 30-day target.

Honesty guardrail: if the label signal is degenerate (few/no positive 'unavailable' examples),
the script flags it instead of reporting a meaningless precision number.
"""
import pathlib, glob, re, json, math
from datetime import date, timedelta
from collections import defaultdict

ROOT = pathlib.Path('.')
DATE_RE = re.compile(r'(20\d{2})-(\d{2})-(\d{2})')
AGENT = re.compile(r'(?i)\b(archivist|builder|designer|mechanic|orchestrator|researcher|scribe|verifier)\b')
HALF_LIFE_DAYS = 3.0   # recency weighting for the predictive component
K = 7                  # forward horizon (days)
MIN_TRAIN_DAYS = 4     # rolling-origin minimum history before first forecast

# ---- build per-(seat, day) availability from file-activity presence ----
def build_labels():
    seat_days = defaultdict(set)
    for f in glob.glob('memory/**/*', recursive=True):
        p = pathlib.Path(f)
        if not p.is_file(): continue
        m = DATE_RE.search(p.name)
        if not m: continue
        try: d = date(*map(int, m.groups()))
        except ValueError: continue
        am = AGENT.search(p.name); agents = set()
        if am: agents.add(am.group(1).lower())
        else:
            try:
                head = p.open('r', encoding='utf-8', errors='ignore').read(400)
                for g in AGENT.findall(head): agents.add(g.lower())
            except (OSError, UnicodeDecodeError): pass
        for a in agents: seat_days[a].add(d)
    alldays = set()
    for s in seat_days: alldays |= seat_days[s]
    days = sorted(alldays)
    L = {s: [1 if days[i] in seat_days[s] else 0 for i in range(len(days))] for s in sorted(seat_days)}
    return L, days

# ---- recency-weighted unavailability probability at origin index T (uses history before T) ----
def weighted_unavail(label_hist):
    """label_hist: list of 0/1 from oldest->newest ending at the day BEFORE forecast.
       1=available. Returns P(unavailable) with exponential recency weighting."""
    n = len(label_hist)
    if n == 0: return None
    wsum = 0.0; usum = 0.0
    for j in range(n):
        age = (n - 1 - j)          # 0 = most recent day in history
        w = 0.5 ** (age / HALF_LIFE_DAYS)
        wsum += w
        usum += w * (1 - label_hist[j])   # weight unavailability
    recency_unavail = usum / wsum
    base_unavail = sum(1 - x for x in label_hist) / n
    return 0.6 * recency_unavail + 0.4 * base_unavail

def walk_forward_backtest(L, days):
    D = len(days)
    agg = {'tp':0,'fp':0,'tn':0,'fn':0}
    per_seat = {}
    for s in L:
        tp=fp=tn=fn=0
        for T in range(MIN_TRAIN_DAYS, D):      # origin at day index T (history < T)
            p = weighted_unavail(L[s][:T])
            if p is None: continue
            pred_unavail = 1 if p > 0.5 else 0
            end = min(T + K, D)                  # only score days that actually exist
            for i in range(T, end):
                actual_unavail = 1 - L[s][i]     # label: unavailable?
                if pred_unavail == 1 and actual_unavail == 1: tp+=1
                elif pred_unavail == 1 and actual_unavail == 0: fp+=1
                elif pred_unavail == 0 and actual_unavail == 1: fn+=1
                else: tn+=1
        d = {'tp':tp,'fp':fp,'tn':tn,'fn':fn}
        prec = tp/(tp+fp) if (tp+fp) else None
        rec = tp/(tp+fn) if (tp+fn) else None
        f1 = 2*prec*rec/(prec+rec) if (prec and rec) else None
        per_seat[s] = {**d, 'precision':prec,'recall':rec,'f1':f1,
                       'positive_examples': tp+fn}
        agg['tp']+=tp; agg['fp']+=fp; agg['tn']+=tn; agg['fn']+=fn
    prec = agg['tp']/(agg['tp']+agg['fp']) if (agg['tp']+agg['fp']) else None
    rec  = agg['tp']/(agg['tp']+agg['fn']) if (agg['tp']+agg['fn']) else None
    f1   = 2*prec*rec/(prec+rec) if (prec and rec) else None
    return {'window_days': D, 'span': [str(days[0]), str(days[-1])],
            'aggregate': {**agg, 'precision': prec, 'recall': rec, 'f1': f1,
                          'positive_unavail_examples': agg['tp']+agg['fn']},
            'per_seat': per_seat}

def risk_tier(p):
    if p >= 0.7: return 'high'
    if p >= 0.4: return 'medium'
    return 'low'

def main():
    L, days = build_labels()
    D = len(days)
    bt = walk_forward_backtest(L, days)

    # ---- forward 7-day forecast per seat (predictive component) ----
    forecasts = {}
    for s in L:
        p = weighted_unavail(L[s][:])   # full history to date
        base = sum(1 - x for x in L[s]) / D
        recency = 0.5
        wsum=usum=0.0; n=len(L[s])
        for j in range(n):
            age=(n-1-j); w=0.5**(age/HALF_LIFE_DAYS); wsum+=w; usum+=w*(1-L[s][j])
        recency_unavail = usum/wsum
        forecasts[s] = {
            'p_unavail_7d': round(p,3),
            'base_rate_unavail': round(base,3),
            'recency_weighted_unavail': round(recency_unavail,3),
            'available_days_last14': sum(L[s]),
            'risk_level': risk_tier(p),
        }

    degenerate = bt['aggregate']['positive_unavail_examples'] < 5
    out = {
        'generated': date.today().isoformat(),
        'method': ('recency-weighted (half-life %.0f d) unavailability probability, '
                   'blended 60/40 with full-period base rate; walk-forward backtest '
                   'threshold P(unavail)>0.5') % HALF_LIFE_DAYS,
        'data_window_days': D,
        'ac_target': {'backtest_window_days': 30, 'precision_threshold': 0.7},
        'forecasts': forecasts,
        'high_risk_seats': [s for s in forecasts if forecasts[s]['risk_level']=='high'],
        'walk_forward_backtest': bt,
        'degenerate_signal': degenerate,
        'note': ('File-activity presence is the only per-day label available; it is '
                 'near-degenerate (most seat-days are "available"), so precision for '
                 'unreachable predictions has few/no positive examples to score. A real '
                 'per-day reachability time series is required for the AC 30-day test.'
                 if degenerate else ''),
    }
    outp = ROOT/'memory/researcher/unavailability-forecast.json'
    outp.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2))
    print('\nWROTE', outp)

if __name__ == '__main__':
    main()
