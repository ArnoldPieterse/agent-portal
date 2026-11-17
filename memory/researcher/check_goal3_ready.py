#!/usr/bin/env python
# check_goal3_ready.py - goal #3 (mirror-revert deep-dive) readiness probe + one-command closure.
#
# WHY THIS EXISTS: every prior pass re-derived "where are we in the window / what do I do next"
# by hand. This turns that into ONE command with zero deliberation:
#   python memory/researcher/check_goal3_ready.py              # read-only status + next action
#   python memory/researcher/check_goal3_ready.py --close      # day-7: run pipeline, generate leaf,
#                                                              # and (only if acceptance met) book ledger
#
# Reuses the already-proven consumers (parse_mirror_events.py + fill_analysis.py). It does NOT
# re-probe the seed wall (logged NEEDS-HUMAN in memory/ops/blockers.md) and does NOT idle-sample -
# it just classifies current state against the runbook's pre-decided contingency table.
#
# Contingency branches (from mirror-revert-closure-runbook-2026-11-17.md):
#   >=5 live days            -> FULL close
#   3-4 live days & >=5 evts -> PARTIAL close (caveat note)
#   <3 days or <5 events     -> DO-NOT-CLOSE / extend to 11-27
import os, sys, json, subprocess, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
LIVE_LOG = r"Z:\mirror_events.log"
WINDOW_START = dt.date(2026, 11, 17)   # instrumentation landed / window open
WINDOW_END = dt.date(2026, 11, 24)     # planned day-7
EXTEND_TO = dt.date(2026, 11, 27)
ESC_DAY3 = dt.date(2026, 11, 20)       # consolidated NEEDS-HUMAN escalation due
ESC_DAY5 = dt.date(2026, 11, 22)       # do-not-close/extend decision due
TSFMT = "%Y-%m-%d %H:%M:%S"

def load_live_events(path):
    """Return list of live (non-_test) events parsed as dicts. Missing file -> []."""
    evts = []
    if not os.path.exists(path):
        return None  # signal: drive not mapped this session
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue  # malformed -> skip (parse_mirror_events warns; we classify only)
            if o.get("_test"):
                continue
            evts.append(o)
    return evts

def live_days(evts):
    days = set()
    for e in evts:
        t = e.get("t", "")
        try:
            days.add(dt.datetime.strptime(t, TSFMT).date())
        except Exception:
            pass
    return len(days)

def classify(evts, today):
    """Return (branch, detail) per contingency table."""
    if evts is None:
        return "NO-DRIVE", "live log path not mapped in this session (environmental variance; seed wall already NEEDS-HUMAN). Re-run on a session where Z: maps."
    n = len(evts)
    if n == 0:
        # accrual gated on seed wall
        notes = []
        if today >= ESC_DAY3:
            notes.append("DAY-3 escalation (" + str(ESC_DAY3) + ") DUE: log ONE consolidated NEEDS-HUMAN in memory/ops/blockers.md naming Mechanic (non-sandbox White seat) + seed command `python memory/ops/seed_mirror_run.py`; then pivot to goal #8 SLA re-audit.")
        if today >= ESC_DAY5:
            notes.append("DAY-5 extend-decision (" + str(ESC_DAY5) + ") DUE: activate mirror-revert-extend-decision-draft-2026-11-18.md; confirm no NEW escalation needed.")
        if today >= WINDOW_END:
            notes.append("WINDOW CLOSED with 0 live events -> DO-NOT-CLOSE per contingency table. Run --close to generate the do-not-close/extend record (no ledger closure).")
        detail = "0 live events; dataset accrual gated on logged seed wall." + (" " + " ".join(notes) if notes else " Next checkpoint = " + str(ESC_DAY3) + " day-3 escalation.")
        return "WAIT", detail
    days = live_days(evts)
    if today < WINDOW_END:
        # window still open but data accruing -> keep sampling, don't close early
        return "ACCRUING", "%d live events across %d day(s); window still open until %s. Keep daily sampling; close at %s via --close." % (n, days, WINDOW_END, WINDOW_END)
    # window closed: apply contingency table on full dataset
    if days >= 5:
        return "FULL", "%d live events / %d days -> FULL closure per plan (note shorter window if applicable)." % (n, days)
    if days >= 3 and n >= 5:
        return "PARTIAL", "%d live events / %d days -> PARTIAL close with caveat ('N-day subset; trend reliable, absolute frequency undercounted')." % (n, days)
    return "EXTEND", "%d live events / %d days -> DO-NOT-CLOSE. Extend window to %s and re-evaluate; if still insufficient flag NEEDS-HUMAN with reason." % (n, days, EXTEND_TO)

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(r.stdout or "")
    if r.stderr:
        sys.stdout.write("[stderr] " + r.stderr)
    return r.returncode

def main():
    today = dt.date.today()
    evts = load_live_events(LIVE_LOG)
    branch, detail = classify(evts, today)
    age = (today - WINDOW_START).days
    n = 0 if evts is None else len(evts)
    print("== goal #3 readiness probe (%s) ==" % today.isoformat())
    print("window: %s -> %s   | day %d of window   | live log: %s   | live events: %s" % (
        WINDOW_START, WINDOW_END, age + 1, LIVE_LOG, ("n/a (drive unmapped)" if evts is None else str(n))))
    print("BRANCH: %s" % branch)
    print(detail)

    do_close = "--close" in sys.argv
    if not do_close:
        # read-only: also show the exact one-command close for reference
        print("\n[read-only] day-7 one-command close (when BRANCH in FULL/PARTIAL/EXTEND at window end):")
        print("  python memory/researcher/check_goal3_ready.py --close")
        return 0

    # --- --close path ---
    if branch == "WAIT" and n == 0:
        # no data: do NOT book a closure; generate the do-not-close/extend record only
        print("\n[close] 0 live events at window end -> DO-NOT-CLOSE. No ledger closure booked.")
        print("Action: run `python memory/researcher/fill_analysis.py %s` to emit the do-not-close leaf, then activate extend-decision draft." % LIVE_LOG)
        return 2
    if branch in ("NO-DRIVE", "ACCRUING"):
        print("\n[close] refusing: BRANCH=%s is not a closable state (window not ended / log unavailable)." % branch)
        return 3
    # FULL / PARTIAL / EXTEND with data -> generate leaf via proven consumer, then book ledger iff closable
    leaf = os.path.join(HERE, "mirror-revert-analysis-%s.md" % today.isoformat())
    print("\n[close] generating analysis leaf via fill_analysis.py -> %s" % leaf)
    rc = run([sys.executable, os.path.join(HERE, "fill_analysis.py"), LIVE_LOG])
    if rc != 0:
        print("[close] fill_analysis FAILED rc=%d; not booking ledger." % rc)
        return rc
    if branch in ("FULL", "PARTIAL"):
        note = "goal3 closed: %s; %d live events; artifact %s" % (branch, n, leaf)
        print("\n[close] acceptance MET (%s). Booking ledger record..." % branch)
        rcr = run([sys.executable, os.path.join(HERE, "goal_ledger.py"), "--record", "researcher", "3", "--note", note])
        print("[close] ledger rc=%d -> DONE." % rcr if rcr == 0 else "[close] ledger FAILED rc=%d - record manually per runbook." % rcr)
    else:
        print("\n[close] BRANCH=EXTEND -> leaf written for re-evaluation; NO ledger closure. Re-run at %s." % EXTEND_TO)
    return 0

if __name__ == "__main__":
    sys.exit(main())
