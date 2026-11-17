# Validation harness for check_goal3_ready.classify() branch decisions.
import sys, os, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_goal3_ready as c

def ev(day, n=2):
    return [{'t': day + ' 12:00:00', 'kind': 'write', 'path': 'x', 'reason': 'new'} for _ in range(n)]

cases = [
    ('NO-DRIVE',   (None, dt.date(2026, 11, 24)), 'NO-DRIVE'),
    ('WAIT@day7',  ([],      dt.date(2026, 11, 24)), 'WAIT'),
    ('WAIT@esc3',  ([],      dt.date(2026, 11, 20)), 'WAIT'),   # must mention escalation due
    ('ACCRUING',   (ev('2026-11-18')+ev('2026-11-19'), dt.date(2026, 11, 21)), 'ACCRUING'),
    ('FULL',       (sum((ev(d) for d in ['2026-11-17','2026-11-18','2026-11-19','2026-11-20','2026-11-21']), []), dt.date(2026, 11, 24)), 'FULL'),
    ('PARTIAL',    (sum((ev(d) for d in ['2026-11-20','2026-11-21','2026-11-22']), []), dt.date(2026, 11, 24)), 'PARTIAL'),
    ('EXTEND',     (ev('2026-11-23'), dt.date(2026, 11, 24)), 'EXTEND'),
]
ok = True
for name, (evs, today), want in cases:
    branch, detail = c.classify(evs, today)
    flag = 'PASS' if branch == want else 'FAIL'
    if branch != want:
        ok = False
    print('%-10s %-4s (want %-9s) | %s' % (name, flag, want, detail[:80]))

# escalation message assertion: WAIT on day>=ESC_DAY3 must mention day-3 escalation due
b, d = c.classify([], dt.date(2026, 11, 21))
assert 'DAY-3 escalation' in d and 'seed_mirror_run.py' in d, 'escalation msg missing: %r' % d
print('PASS   esc-msg | day-4 WAIT detail names consolidated NEEDS-HUMAN + seed cmd')
print('\nRESULT:', 'ALL PASS' if ok else 'FAILURES PRESENT')
sys.exit(0 if ok else 1)
