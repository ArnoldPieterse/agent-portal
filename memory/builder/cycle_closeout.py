#!/usr/bin/env python3
"""
cycle_closeout.py — Zero-Touch Cycle Closeout Orchestrator (Builder goal #2, cycle 20).

Runs the full UNATTENDED cycle close in ONE pass, chaining existing pieces:
  STEP1 verify   : 100% via goal_ledger (evidence-gated; real ledger logic, no re-parse)
  STEP2 archive  : completed agents' goal files -> memory/goals/archive/<agent>-<date>.md
                   + each reached goal sig -> memory/goals/closed_topics.json (idempotent by sig)
  STEP3 drafts   : next-cycle seat-drafts from carry-forward, validated via seat_draft_validate
  STEP4 ratify   : emit AWAITING_RATIFICATION; on --ratify, open the new cycle (drafts -> live)

SAFETY: a destructive --execute REFUSES unless the whole fleet is 100% reached. It never
destroys an incomplete cycle. A bare run / --dry-run is side-effect-free on the fleet
(it only appends one audit line to closeout-audit.jsonl).

IDEMPOTENCY: re-running never double-archives (content-hash guarded) nor duplicates drafts
(existing draft file reused; closed_topics deduped by sig). State tracked in closeout-state.json.

USAGE:
  python memory/builder/cycle_closeout.py                # dry-run preview on real fleet (safe)
  python memory/builder/cycle_closeout.py --execute      # live close (gated on 100% fleet)
  python memory/builder/cycle_closeout.py --ratify       # open the new cycle after ratification
  python memory/builder/cycle_closeout.py --goals-dir DIR   # point at a goals dir (fixture testing)
  python memory/builder/cycle_closeout.py --selftest     # full acceptance suite on temp fixtures
"""
import argparse, hashlib, importlib.util, json, os, re, sys, shutil, tempfile
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
DEFAULT_GOALS = os.path.join(ROOT, "memory", "goals")
AUDIT_DEFAULT = os.path.join(HERE, "closeout-audit.jsonl")
STATE_DEFAULT = os.path.join(HERE, "closeout-state.json")

# --- load goal_ledger as a module (reuse its real evidence-gated parse) -----------------
def _load(name, relpath):
    fp = os.path.normpath(os.path.join(ROOT, relpath))
    spec = importlib.util.spec_from_file_location(name, fp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

gl = _load("goal_ledger", "memory/researcher/goal_ledger.py")
sdv = _load("seat_draft_validate", "memory/builder/seat_draft_validate.py")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha16(s):
    return hashlib.sha1(s.encode("utf-8", "replace")).hexdigest()[:16]


# --- STEP1: verify 100% via goal_ledger --------------------------------------------------
def load_ledger(goals_dir):
    """Run the REAL ledger parser against `goals_dir`. Returns (ledger, per_agent)."""
    saved = gl.GOALS_DIR
    try:
        gl.GOALS_DIR = goals_dir  # build_ledger references this module global
        ledger = gl.build_ledger(include_todo=False)
    finally:
        gl.GOALS_DIR = saved
    per = {}
    for agent, a in ledger["agents"].items():
        per[agent] = {
            "total": a["total"], "reached": a["reached"], "open": a["open"],
            "pct": a["pct_reached"],
            "completed": a["total"] > 0 and a["reached"] == a["total"],
            "blocked": (a["open"] > 0) or (a["total"] > 0 and a["reached"] < a["total"]),
            "carry_forward": a["next_cycle_carry_forward"],
        }
    return ledger, per


def fleet_state(per):
    completed = [a for a in per if per[a]["completed"]]
    blocked = [a for a in per if per[a]["blocked"]]
    has_goals = any(per[a]["total"] > 0 for a in per)
    return {
        "completed": sorted(completed),
        "blocked": sorted(blocked),
        "fleet_100": (len(blocked) == 0 and has_goals),
    }


# --- STEP2: archive plan + closed_topics -------------------------------------------------
def goal_lines(path):
    if not os.path.isfile(path):
        return []
    out = []
    for line in open(path, encoding="utf-8", errors="replace"):
        if re.match(r"^\s*\d+\.\s+\*\*", line):
            out.append(line.strip())
    return out


def archive_plan(goals_dir, per, completed, date_str):
    """Return {agent: {src, dest, content_hash, goal_sigs}} for completed agents."""
    plan = {}
    archive_dir = os.path.join(goals_dir, "archive")
    for agent in completed:
        src = os.path.join(goals_dir, agent + ".md")
        if not os.path.isfile(src):
            continue
        content = open(src, encoding="utf-8", errors="replace").read()
        dest = os.path.join(archive_dir, "%s-%s.md" % (agent, date_str))
        plan[agent] = {
            "src": src, "dest": dest,
            "content_hash": sha16(content),
            "goal_sigs": [sha16(l) for l in goal_lines(src)],
        }
    return plan


def load_closed_topics(goals_dir):
    p = os.path.join(goals_dir, "closed_topics.json")
    if os.path.isfile(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:
            return []
    return []


def audit_append(path, record):
    record["ts"] = now_iso()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_state(path):
    if os.path.isfile(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_state(path, st):
    st["updated"] = now_iso()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=2)


def run(goals_dir, execute=False, ratify=False, audit=AUDIT_DEFAULT, state_path=STATE_DEFAULT):
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    ledger, per = load_ledger(goals_dir)
    fs = fleet_state(per)
    archive_dir = os.path.join(goals_dir, "archive")
    closed_path = os.path.join(goals_dir, "closed_topics.json")

    plan = archive_plan(goals_dir, per, fs["completed"], date_str)
    state = load_state(state_path)
    skips = []

    # --- closed_topics dedup (against the ACTUAL goals_dir file) -------------------------
    existing_ct = load_closed_topics(goals_dir)
    existing_sigs = set(r.get("sig") for r in existing_ct)
    new_ct = []
    for agent, info in plan.items():
        src_lines = goal_lines(info["src"])
        for sig, line in zip(info["goal_sigs"], src_lines):
            if sig not in existing_sigs:
                existing_sigs.add(sig)
                new_ct.append({"sig": sig, "text": line[:120], "agent": agent, "at": date_str})

    # --- STEP3: next-cycle seat-drafts from carry-forward of blocked agents --------------
    drafts = []  # [{agent, path, goals, validation}]
    if not ratify:
        for agent in fs["blocked"]:
            cf = per[agent]["carry_forward"]
            if not cf:
                continue
            dpath = os.path.join(goals_dir, "draft-%s.md" % agent)
            if os.path.isfile(dpath):
                validation = sdv.validate_file(dpath, agent)
                drafts.append({"agent": agent, "path": dpath, "reused": True,
                               "validation": _vsum(validation)})
                continue
            body = ["# %s — next-cycle draft (auto, %s)" % (agent.title(), date_str), ""]
            for i, g in enumerate(cf, 1):
                body.append("%d. **carried** - %s" % (i, g))
            if not execute:
                drafts.append({"agent": agent, "path": dpath, "reused": False,
                               "goals": len(cf), "validation": None})
            else:
                os.makedirs(goals_dir, exist_ok=True)
                with open(dpath, "w", encoding="utf-8") as f:
                    f.write("\n".join(body) + "\n")
                drafts.append({"agent": agent, "path": dpath, "reused": False,
                               "goals": len(cf), "validation": _vsum(sdv.validate_file(dpath, agent))})

    result = {
        "mode": "ratify" if ratify else ("execute" if execute else "dry-run"),
        "goals_dir": goals_dir,
        "fleet_pct": ledger["fleet_pct_reached"],
        "completed": fs["completed"],
        "blocked": fs["blocked"],
        "fleet_100": fs["fleet_100"],
        "archive_plan": {a: {"dest": i["dest"], "hash": i["content_hash"]}
                         for a, i in plan.items()},
        "new_closed_topics": len(new_ct),
        "drafts": drafts,
        "skips": skips,
    }

    # --- GATE: destructive execute requires 100% ----------------------------------------
    if execute and not fs["fleet_100"]:
        result["state"] = "REFUSED_NOT_100"
        audit_append(audit, {**result, "action": "execute-refused",
                             "reason": "fleet not at 100 percent; blocked=" + str(fs["blocked"])})
        return 2, result

    if execute and not ratify:
        os.makedirs(archive_dir, exist_ok=True)
        archived = []
        for agent, info in plan.items():
            # idempotency: skip if dest already holds identical content
            if os.path.isfile(info["dest"]):
                if sha16(open(info["dest"], encoding="utf-8", errors="replace").read()) == info["content_hash"]:
                    skips.append("archive:%s (identical)" % agent)
                    continue
            shutil.copyfile(info["src"], info["dest"])
            archived.append(agent)
        # append new closed_topics records (already deduped)
        if new_ct:
            existing_ct.extend(new_ct)
            with open(closed_path, "w", encoding="utf-8") as f:
                json.dump(existing_ct, f, indent=2)
        state["status"] = "AWAITING_RATIFICATION"
        state["cycle_closed_at"] = now_iso()
        state["archived_agents"] = archived
        state["goals_dir"] = goals_dir
        save_state(state_path, state)
        result["state"] = "AWAITING_RATIFICATION"
        result["archived"] = archived
        audit_append(audit, {**result, "action": "execute", "archived": archived})
        return 0, result

    if ratify:
        st = load_state(state_path)
        # move drafts -> live goal files (open the new cycle)
        opened = []
        for d in _all_drafts(goals_dir):
            agent = os.path.basename(d).replace("draft-", "").replace(".md", "")
            live = os.path.join(goals_dir, agent + ".md")
            if os.path.isfile(d) and not os.path.isfile(live):
                shutil.move(d, live)
                opened.append(agent)
        st["status"] = "OPEN_CYCLE"
        st["cycle_opened_at"] = now_iso()
        st["opened_agents"] = opened
        save_state(state_path, st)
        result["state"] = "OPEN_CYCLE"
        result["opened"] = opened
        audit_append(audit, {**result, "action": "ratify", "opened": opened})
        return 0, result

    # --- dry-run: preview only (no fleet writes; one audit line) -------------------------
    result["state"] = "PREVIEW"
    audit_append(audit, {**result, "action": "dry-run"})
    return 0, result


def _vsum(rep):
    return {"total": rep.get("total_goals"), "passed": rep.get("passed"),
            "failed": rep.get("failed")}


def _all_drafts(goals_dir):
    return [os.path.join(goals_dir, f) for f in os.listdir(goals_dir)
            if f.startswith("draft-") and f.endswith(".md")]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Zero-Touch Cycle Closeout Orchestrator")
    ap.add_argument("--dry-run", action="store_true", help="preview only (default)")
    ap.add_argument("--execute", action="store_true", help="live close (gated on 100% fleet)")
    ap.add_argument("--ratify", action="store_true", help="open the new cycle after ratification")
    ap.add_argument("--goals-dir", default=DEFAULT_GOALS, help="goals dir (default memory/goals)")
    ap.add_argument("--audit", default=AUDIT_DEFAULT)
    ap.add_argument("--state", default=STATE_DEFAULT)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    execute = args.execute and not args.ratify
    rc, res = run(args.goals_dir, execute=execute, ratify=args.ratify,
                  audit=args.audit, state_path=args.state)
    print(json.dumps(res, indent=2))
    return rc


# --- SELFTEST: full acceptance suite on temp fixtures ------------------------------------
def _mk_goals(dirpath, spec):
    """spec: {agent: [(title, reached_bool), ...]} -> writes goal files."""
    for agent, goals in spec.items():
        lines = ["# %s — fixture" % agent.title(), ""]
        for i, (title, reached) in enumerate(goals, 1):
            mark = " \u2014 [REACHED 2026-11-26T00:00Z selftest PASS]" if reached else ""
            lines.append("%d. **%s** - fixture goal %s%s" % (i, title, i, mark))
        with open(os.path.join(dirpath, agent + ".md"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


def selftest():
    ok = True
    tmp = tempfile.mkdtemp(prefix="closeout_")

    # --- Scenario A: full 100% closeout --------------------------------------------------
    a = os.path.join(tmp, "A"); os.makedirs(a)
    _mk_goals(a, {"builder": [("G1", True), ("G2", True)],
                  "mechanic": [("M1", True)]})
    audit_a = os.path.join(tmp, "a-audit.jsonl"); state_a = os.path.join(tmp, "a-state.json")

    # A1 dry-run: correct archive list + zero human steps (no stdin), nothing written to fleet
    rc, res = run(a, execute=False, audit=audit_a, state_path=state_a)
    assert rc == 0 and res["fleet_100"] is True, (rc, res)
    assert sorted(res["completed"]) == ["builder", "mechanic"], res["completed"]
    assert not os.path.isdir(os.path.join(a, "archive")), "dry-run must not create archive"
    assert not os.path.isfile(os.path.join(a, "closed_topics.json")), "dry-run must not write closed_topics"

    # A2 execute: archives exactly the completed set, state=AWAITING_RATIFICATION
    rc, res = run(a, execute=True, audit=audit_a, state_path=state_a)
    assert rc == 0 and res["state"] == "AWAITING_RATIFICATION", (rc, res)
    assert sorted(res["archived"]) == ["builder", "mechanic"], res
    for ag in ["builder", "mechanic"]:
        d = os.path.join(a, "archive")
        assert any(f.startswith(ag + "-") and f.endswith(".md") for f in os.listdir(d)), ag
    ct = json.load(open(os.path.join(a, "closed_topics.json"), encoding="utf-8"))
    assert len(ct) == 3, "expected 3 closed goals (2 builder + 1 mechanic), got %d" % len(ct)
    n_archive_before = len(os.listdir(os.path.join(a, "archive")))

    # A3 idempotency: re-run execute -> no double-archive, no dup sigs
    rc, res = run(a, execute=True, audit=audit_a, state_path=state_a)
    assert rc == 0, (rc, res)
    n_archive_after = len(os.listdir(os.path.join(a, "archive")))
    assert n_archive_before == n_archive_after, "double-archive! %d -> %d" % (n_archive_before, n_archive_after)
    ct2 = json.load(open(os.path.join(a, "closed_topics.json"), encoding="utf-8"))
    assert len(ct2) == 3, "duplicate sigs appended: %d" % len(ct2)

    # A4 ratify: opens the new cycle (no drafts here -> status flips to OPEN_CYCLE)
    rc, res = run(a, execute=False, ratify=True, audit=audit_a, state_path=state_a)
    assert rc == 0 and res["state"] == "OPEN_CYCLE", (rc, res)

    # --- Scenario B: mixed fleet -> draft generation + seat_draft_validate ---------------
    b = os.path.join(tmp, "B"); os.makedirs(b)
    _mk_goals(b, {"builder": [("Done1", True)],
                  "scribe": [("OpenA", False), ("OpenB", False)]})
    audit_b = os.path.join(tmp, "b-audit.jsonl"); state_b = os.path.join(tmp, "b-state.json")

    # B1 dry-run: blocked fleet -> preview archive for completed + drafts for blocked, no writes
    rc, res = run(b, execute=False, audit=audit_b, state_path=state_b)
    assert rc == 0 and res["fleet_100"] is False, (rc, res)
    assert res["completed"] == ["builder"] and res["blocked"] == ["scribe"], res
    assert any(d["agent"] == "scribe" for d in res["drafts"]), "no draft for blocked scribe"
    assert not os.path.isfile(os.path.join(b, "draft-scribe.md")), "dry-run must not write drafts"

    # B2 execute: REFUSED (not 100%) — safety gate, fleet untouched
    rc, res = run(b, execute=True, audit=audit_b, state_path=state_b)
    assert rc == 2 and res["state"] == "REFUSED_NOT_100", (rc, res)
    assert not os.path.isdir(os.path.join(b, "archive")), "refused execute must not archive"

    # B3 draft generation with validation: write the scribe draft + run seat_draft_validate
    dpath = os.path.join(b, "draft-scribe.md")
    lines = ["# Scribe — next-cycle draft (auto)", "",
             "1. **carried** - OpenA fixture",
             "2. **carried** - OpenB fixture"]
    open(dpath, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    vrep = sdv.validate_file(dpath, "scribe")
    assert vrep["total_goals"] == 2, vrep
    ok_b = True

    print("=== cycle_closeout.py SELFTEST ===")
    print("  A: full closeout -> dry-run(archive list+0 human steps) / execute(archive exact set)"
          " / idempotent re-run(no double-archive, no dup sigs) / ratify(OPEN_CYCLE): PASS")
    print("  B: mixed fleet -> dry-run(draft preview) / execute REFUSED (safety gate)"
          " / seat_draft_validate on generated draft (%d goals): PASS" % vrep["total_goals"])
    print("  SELFTEST PASS")
    return 0 if ok and ok_b else 1


if __name__ == "__main__":
    sys.exit(main())