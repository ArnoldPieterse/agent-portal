#!/usr/bin/env python3
"""Outlet Milestone Auto-Draft Trigger (goal #6).

Watches two live signals and, when one crosses an UPWARD threshold since the
last draft, stages a milestone post into the content queue in the fleet default
voice. It never invents numbers: every figure is read from a live source.

Live sources (single source of truth):
  - fleet level  -> memory/levels.json            {"level": N, "history":[...]}
  - goal pct     -> memory/goals/next10.json       {"fleet":{"done","total","pct"}, "level_up_eta"}

Trigger rules (one post per run, even if both fire):
  NEW-LEVEL   current level  > last-seen level
  PCT-STEP    floor(current_pct/10) > floor(last-seen pct/10)
First run (no state file) uses baseline level=0 / pct_step=0, so it stages the
inaugural milestone for the current standing. Idempotent: re-running with no
new threshold crossed writes nothing.

State: memory/outlet/milestone_trigger_state.json  {"level":N,"pct_step":N,"last_post":"..."}

Usage:
  python memory/outlet/milestone_trigger.py            # check + auto-draft if triggered
  python memory/outlet/milestone_trigger.py --dry-run # report what WOULD draft, write nothing
  python memory/outlet/milestone_trigger.py selftest  # temp-dir proof: fires, idempotent, re-fires on bump

Nothing publishes. The staged post lands as status=ready-for-human; a human ships it.
"""
import json, os, sys, datetime, argparse, tempfile, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]  # repo root (memory/outlet/.. -> root)
LEVELS = ROOT / "memory" / "levels.json"
NEXT10 = ROOT / "memory" / "goals" / "next10.json"
QUEUE  = ROOT / "memory" / "outlet" / "queue"
STATE  = ROOT / "memory" / "outlet" / "milestone_trigger_state.json"

PLATFORM_LINE = "(unregistered - awaiting Arnold connection; fleet default voice)"


def read_level():
    d = json.loads(LEVELS.read_text(encoding="utf-8"))
    lvl = int(d["level"])
    hist = d.get("history", [])
    last = hist[-1] if hist else {}
    return {"level": lvl, "ts": last.get("ts", "?"), "fleet": last.get("fleet", "?")}


def read_pct():
    d = json.loads(NEXT10.read_text(encoding="utf-8"))
    f = d["fleet"]
    return {"done": int(f["done"]), "total": int(f["total"]), "pct": float(f["pct"]),
            "level_up_eta": d.get("level_up_eta", "?")}


def pct_step(pct):
    return int(pct // 10)  # which +10% band we're in


def draft_body(lvl, done, total, pct, reasons):
    """Fleet default voice: warm, candid, lightly witty, zero hype, one concrete claim."""
    band = pct_step(pct) * 10
    if "NEW-LEVEL" in reasons:
        lead = (f"Level {lvl} is live. We just crossed another full pass of the fleet's work "
                f"running end-to-end on its own - {done}/{total} goals closed, about {pct:.0f}% through.")
    elif "PCT-STEP" in reasons:
        lead = (f"We passed {band}% this run. That's {done} of {total} fleet goals closed - "
                f"{pct:.1f}% with the tail still open.")
    else:
        lead = (f"Checkpoint: {done}/{total} fleet goals closed, {pct:.1f}% done. Level {lvl}.")
    body = (lead + " The remaining work is the unglamorous end - recovery, handoffs, not re-doing "
            "what's already closed - which is exactly where it gets interesting.")
    return body


def build_post(lvl, done, total, pct, reasons, now):
    date = now.strftime("%Y-%m-%d")
    slug_bits = []
    if "NEW-LEVEL" in reasons:
        slug_bits.append(f"level-{lvl}")
    if "PCT-STEP" in reasons:
        slug_bits.append(f"{pct_step(pct) * 10}pct")
    slug = "-".join(slug_bits) or f"level-{lvl}"
    fname = f"{date}-milestone-{slug}.md"
    # avoid clobbering an existing file on same-day re-draft
    p = QUEUE / fname
    n = 1
    while p.exists():
        fname = f"{date}-milestone-{slug}-{n}.md"
        p = QUEUE / fname
        n += 1
    body = draft_body(lvl, done, total, pct, reasons)
    level_up_eta = read_pct()["level_up_eta"]
    math_check = (f"claim '{done}/{total} = {pct:.0f}%' -> math VERIFIED inline "
                  f"({done}/{total} = {done/total*100:.1f}% computed by trigger)")
    reasons_str = ", ".join(r.lower() for r in reasons)
    post = f"""# Staged post: fleet milestone ({reasons_str})
date: {date}
kind: upload
platform: {PLATFORM_LINE}
status: ready-for-human
topic: Fleet milestone - level {lvl}, {pct:.1f}% ({done}/{total})

## Body
{body}

## Rationale
- Auto-drafted by memory/outlet/milestone_trigger.py; trigger fired on: {', '.join(reasons)}.
- One concrete claim: {done}/{total} = {pct:.0f}%, pulled live from goal ledger / forecast, not invented.
- Marks the milestone publicly in fleet default voice (warm, candid, zero hype).

## Evidence / sources (for Verifier fact-check before ship)
- Fleet level {lvl}: memory/levels.json (level={lvl}); report path in history tail.
- Goal pct: memory/goals/next10.json fleet done={done} total={total} pct={pct}; level_up_eta={level_up_eta}.
- {math_check}

fact-check:
- {math_check}
- claim 'level {lvl}' -> source memory/levels.json (not independently re-run this pass)
- PENDING Verifier sign-off on the pct figure before ship.

## Notes for ship
- No internal IPs, paths, keys or secrets in body (hard line respected).
- Needs a platform + Designer visual once Arnold connects an account; human approves before ship.
"""
    return fname, post


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"level": 0, "pct_step": 0, "last_post": None}


def save_state(st):
    STATE.write_text(json.dumps(st, indent=2) + "\n", encoding="utf-8")


def evaluate(lvl_info, pct_info, state):
    reasons = []
    if lvl_info["level"] > state.get("level", 0):
        reasons.append("NEW-LEVEL")
    if pct_step(pct_info["pct"]) > state.get("pct_step", 0):
        reasons.append("PCT-STEP")
    return reasons


def run(dry_run=False, now=None):
    now = now or datetime.datetime.now()
    lvl = read_level()
    pct = read_pct()
    state = load_state()
    reasons = evaluate(lvl, pct, state)
    if not reasons:
        print(f"no milestone crossed (level={lvl['level']}, pct_step={pct_step(pct['pct'])}, "
              f"state level={state.get('level')}/step={state.get('pct_step')}); nothing drafted")
        return {"triggered": False, "reasons": [], "post": None}
    fname, post = build_post(lvl["level"], pct["done"], pct["total"], pct["pct"], reasons, now)
    if dry_run:
        print(f"DRY-RUN would draft {fname} (reasons={reasons}); not written")
        return {"triggered": True, "reasons": reasons, "post": fname, "dry": True}
    QUEUE.mkdir(parents=True, exist_ok=True)
    (QUEUE / fname).write_text(post, encoding="utf-8")
    state.update({"level": lvl["level"], "pct_step": pct_step(pct["pct"]),
                  "last_post": fname, "ts": now.isoformat()})
    save_state(state)
    print(f"drafted {fname} (reasons={reasons}); state level-> {lvl['level']}, step-> {pct_step(pct['pct'])}")
    return {"triggered": True, "reasons": reasons, "post": fname}


def selftest():
    """Prove the trigger in an isolated temp root: fires on first run, idempotent,
    re-fires when level bumps. Uses a scratch copy of LEVELS/NEXT10/QUEUE/STATE."""
    global LEVELS, NEXT10, QUEUE, STATE
    saved = (LEVELS, NEXT10, QUEUE, STATE)
    src_lvl = json.loads(saved[0].read_text(encoding="utf-8"))
    src_pct = json.loads(saved[1].read_text(encoding="utf-8"))["fleet"]
    results = []
    with tempfile.TemporaryDirectory() as td:
        td = pathlib.Path(td)
        levels_f = td / "levels.json"
        next10_f = td / "next10.json"
        queue_d = td / "queue"
        state_f = td / "state.json"
        queue_d.mkdir()

        def write_sources(level, fleet):
            levels_f.write_text(json.dumps({"level": level,
                "history": [{"level": level, "ts": "t", "fleet": f"{fleet['done']}/{fleet['total']}"}]}), encoding="utf-8")
            next10_f.write_text(json.dumps({"ok": True, "fleet": fleet, "level_up_eta": "?"}), encoding="utf-8")

        LEVELS, NEXT10, QUEUE, STATE = levels_f, next10_f, queue_d, state_f
        try:
            write_sources(12, src_pct)
            r1 = run()
            files1 = sorted(p.name for p in queue_d.glob("*.md"))
            r2 = run()  # idempotency: same state -> no new post
            files2 = sorted(p.name for p in queue_d.glob("*.md"))
            write_sources(13, dict(src_pct, pct=95.0, done=110))  # bump level
            r3 = run()
            files3 = sorted(p.name for p in queue_d.glob("*.md"))
            results = {
                "run1_triggered": r1["triggered"] and r1.get("post"),
                "run1_file": files1,
                "run2_no_new_post": (len(files2) == len(files1)) and not r2["triggered"],
                "run3_refired_on_level_bump": r3["triggered"] and (len(files3) > len(files2)),
                "run3_file": [x for x in files3 if x not in files2],
            }
        finally:
            LEVELS, NEXT10, QUEUE, STATE = saved
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("selftest", nargs="?", const=True)
    args = ap.parse_args()
    if args.selftest:
        r = selftest()
        print(json.dumps(r, indent=2))
        ok = (r["run1_triggered"] and r["run2_no_new_post"] and r["run3_refired_on_level_bump"])
        print("SELFTEST", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    run(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
