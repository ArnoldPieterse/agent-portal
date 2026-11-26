#!/usr/bin/env python3
"""
regression_dispatcher.py — Convergence Regression Auto-Remediation Dispatcher
(Builder goal #8, cycle 20: Fleet Autonomy Convergence).

Closes the detect -> act loop with NO human. When the convergence FSM is in
REGRESSING (set by the sentinel / a mode writer), this dispatcher AUTOMATICALLY:
  1. picks the correct lane for the regression (deterministic cause -> lane map),
  2. opens EXACTLY ONE remediation goal in that lane's memory/goals/<lane>.md,
  3. tracks it to closure via an append-only tracker (remediation-tracker.jsonl).
On closure (regression remediated) it flips the FSM back toward convergence
(REGRESSING -> RECONVERGING -> CONVERGING, both legal per the FSM table) and stamps
the goal line reached.

IDEMPOTENCY: an open remediation is keyed by its tracker record. Repeated detection
while one is already open opens NO duplicate. Closing twice is a no-op.

Distinct from:
  - convergence_fsm.py      : state machine (detects/persists REGRESSING; this consumes it)
  - cycle_closeout.py       : full-cycle close; this is the single-regression hot path
  - Orchestrator's sentinel : produces the REGRESSING signal + regression_cause; this acts on it

USAGE:
  python regression_dispatcher.py --run            # detect->act on LIVE fleet files (safe no-op if not REGRESSING)
  python regression_dispatcher.py --close          # close the open remediation + flip FSM back to CONVERGING
  python regression_dispatcher.py status           # current state + any open remediation
  python regression_dispatcher.py --lane L --run   # force lane (testing / manual override)
  python regression_dispatcher.py selftest         # full acceptance suite on temp fixtures, exit 0/1
"""
from __future__ import annotations
import argparse, json, os, re, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent            # memory/builder
ROOT = HERE.parent.parent                          # repo root
OPS = HERE.parent / "ops"
GOALS = HERE.parent / "goals"
FLEET_MODE_PATH = OPS / "fleet-mode.json"
TRACKER_DEFAULT = HERE / "remediation-tracker.jsonl"

# Deterministic cause -> lane routing. First matching keyword wins; default is the
# convergence owner (Orchestrator) since it holds the autonomy score + sentinel.
LANE_KEYWORDS = [
    (("oom", "vram", "model", "host", "winrm", "gpu", "reboot", "fleet"), "mechanic"),
    (("dispatch", "routing", "route", "size", "sizing", "ratif", "forecast"), "orchestrator"),
    (("ui", "render", "css", "js", "pixel", "panel", "cockpit", "banner"), "designer"),
    (("test", "gate", "canary", "deploy", "perf", "latency"), "forge"),
    (("evidence", "audit", "ledger", "coverage", "contract"), "verifier"),
    (("kpi", "rollup", "synthes", "digest", "attribution"), "scribe"),
]
DEFAULT_LANE = "orchestrator"

# FSM states that mean "the regression has been remediated" (we may close + flip back).
RECOVERED_STATES = {"RECONVERGING", "CONVERGING", "STEADY_STATE"}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_fsm():
    sys.path.insert(0, str(HERE))
    import convergence_fsm as fsm_mod
    return fsm_mod


def pick_lane(cause: str) -> str:
    """Deterministic cause -> lane. Empty/unknown cause -> DEFAULT_LANE."""
    c = (cause or "").lower()
    for kws, lane in LANE_KEYWORDS:
        if any(k in c for k in kws):
            return lane
    return DEFAULT_LANE


# ---- tracker (append-only SSOT for open/close) -----------------------------------------
def _read_tracker(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def _append_tracker(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def open_remediation_id(records: list[dict]) -> str:
    """Monotonic episode id so a re-open after a close is a fresh, unique goal."""
    n = sum(1 for r in records if r.get("event") == "open")
    return f"REG-{now_iso().replace(':', '').replace('-', '')[:12]}-{n:03d}"


def current_open(records: list[dict]) -> dict | None:
    """The remediation currently open (last 'open' with no later matching 'close')."""
    open_id = None
    for r in records:
        if r.get("event") == "open":
            open_id = r.get("id")
        elif r.get("event") == "close" and r.get("id") == open_id:
            open_id = None
    if not open_id:
        return None
    for r in reversed(records):
        if r.get("event") == "open" and r.get("id") == open_id:
            return r
    return None


# ---- goal-file helpers -----------------------------------------------------------------
def _next_goal_number(path: Path) -> int:
    n = 0
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^\s*(\d+)\.\s+\*\*", line)
            if m:
                n = max(n, int(m.group(1)))
    return n + 1


def open_goal_in_lane(lane: str, goal_id: str, cause: str, goals_dir: Path) -> tuple[int, str]:
    """Append exactly one remediation goal line to memory/goals/<lane>.md.
    Returns (line_number_1based, the_line)."""
    path = goals_dir / f"{lane}.md"
    num = _next_goal_number(path)
    title = f"[REMEDIATION:{goal_id}] {lane}-convergence-remediation"
    line = (f"{num}. **{title}** - Auto-opened by regression_dispatcher on FSM=REGRESSING "
            f"(cause: {cause or 'unspecified'}). Remediate the convergence regression; verified when "
            f"the autonomy signal recovers and the dispatcher closes it. — [OPEN {now_iso()}]")
    if not path.exists():
        path.write_text(f"# {lane.title()} — goals\n\n", encoding="utf-8")
    elif not path.read_text(encoding="utf-8", errors="replace").endswith("\n"):
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n")
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    # 1-based line number of the appended line
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, l in enumerate(lines[::-1], 1):
        if f"[REMEDIATION:{goal_id}]" in l:
            return len(lines) - i + 1, l
    return len(lines), line


def stamp_reached(lane: str, goal_id: str, goals_dir: Path) -> bool:
    """Mark the [REMEDIATION:goal_id] line reached. Returns True if a line was found."""
    path = goals_dir / f"{lane}.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    found = False
    for i, l in enumerate(lines):
        if f"[REMEDIATION:{goal_id}]" in l:
            if "[REACHED" not in l:
                # replace trailing [OPEN ...] with a reached marker
                newl = re.sub(r"\s*—\s*\[OPEN[^\]]*\]", "", l).rstrip()
                lines[i] = f"{newl} — [REACHED {now_iso()} closed-by-regression-dispatcher]"
            found = True
            break
    if found:
        path.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
    return found


# ---- core detect -> act -----------------------------------------------------------------
def dispatch(fleet_mode_path: Path, tracker_path: Path, goals_dir: Path,
             lane_override: str | None = None) -> dict:
    fsm_mod = _load_fsm()
    fsm = fsm_mod.ConvergenceFSM(fleet_mode_path, fleet_mode_path.parent / "fsm-events.jsonl")
    state = fsm.current_state()
    records = _read_tracker(tracker_path)
    open_rec = current_open(records)

    # Read optional regression_cause the sentinel writes into fleet-mode.json.
    fm = {}
    try:
        fm = json.loads(fleet_mode_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    cause = lane_override or fm.get("regression_cause", "")
    if lane_override:
        lane = lane_override
    else:
        lane = pick_lane(fm.get("regression_cause", ""))

    out = {"ts": now_iso(), "fsm_state": state, "open_before": bool(open_rec)}

    if state != "REGRESSING":
        # Not in a regression: if one is open and we've recovered, close + flip back.
        if open_rec and state in RECOVERED_STATES:
            out = _close(fsm, tracker_path, goals_dir, open_rec, out, reason="auto-close on recovery")
        else:
            out["action"] = "idle"
            out["note"] = f"FSM={state}; no open remediation to manage"
        return out

    # state == REGRESSING
    if open_rec:
        out["action"] = "no-op-already-open"
        out["id"] = open_rec.get("id")
        out["note"] = "a remediation is already open; not duplicating (idempotent)"
        return out

    # Open exactly one.
    goal_id = open_remediation_id(records)
    line_no, line = open_goal_in_lane(lane, goal_id, fm.get("regression_cause", ""), goals_dir)
    rec = {"event": "open", "id": goal_id, "lane": lane,
           "cause": fm.get("regression_cause", "") or "unspecified",
           "goals_file": str(goals_dir / f"{lane}.md"), "line": line_no,
           "fsm_state": state}
    _append_tracker(tracker_path, rec)
    out.update({"action": "opened", "id": goal_id, "lane": lane,
                "goals_file": str(goals_dir / f"{lane}.md"), "line": line_no})
    return out


def _close(fsm, tracker_path: Path, goals_dir: Path, open_rec: dict, out: dict,
           reason: str) -> dict:
    goal_id = open_rec.get("id")
    lane = open_rec.get("lane", DEFAULT_LANE)
    stamped = stamp_reached(lane, goal_id, goals_dir)
    # Flip FSM back toward convergence: REGRESSING -> RECONVERGING -> CONVERGING (both legal).
    hops = []
    if fsm.current_state() == "REGRESSING":
        r1 = fsm.transition("RECONVERGING", reason=reason, source="regression_dispatcher")
        hops.append(r1)
        if r1.get("ok"):
            r2 = fsm.transition("CONVERGING", reason=reason + ";recovered", source="regression_dispatcher")
            hops.append(r2)
    _append_tracker(tracker_path, {"event": "close", "id": goal_id, "lane": lane,
                                   "fsm_state_after": fsm.current_state(),
                                   "reason": reason, "stamped": stamped})
    out.update({"action": "closed", "id": goal_id, "lane": lane,
                "fsm_state_after": fsm.current_state(), "stamped_goal_line": stamped,
                "hops": [h.get("to") for h in hops]})
    return out


def close_cmd(fleet_mode_path: Path, tracker_path: Path, goals_dir: Path) -> dict:
    records = _read_tracker(tracker_path)
    open_rec = current_open(records)
    if not open_rec:
        return {"ts": now_iso(), "action": "no-op-nothing-open", "note": "no open remediation"}
    fsm_mod = _load_fsm()
    fsm = fsm_mod.ConvergenceFSM(fleet_mode_path, fleet_mode_path.parent / "fsm-events.jsonl")
    return _close(fsm, tracker_path, goals_dir, open_rec,
                  {"ts": now_iso(), "fsm_state": fsm.current_state()}, reason="manual --close")


def status(fleet_mode_path: Path, tracker_path: Path) -> dict:
    fsm_mod = _load_fsm()
    fsm = fsm_mod.ConvergenceFSM(fleet_mode_path, fleet_mode_path.parent / "fsm-events.jsonl")
    open_rec = current_open(_read_tracker(tracker_path))
    return {"ts": now_iso(), "fsm_state": fsm.current_state(),
            "open_remediation": open_rec}


# ---- selftest: full acceptance suite on temp fixtures ------------------------------------
def selftest() -> int:
    import shutil
    tmp = Path(tempfile.mkdtemp(prefix="regdisp-"))
    fm_path = tmp / "fleet-mode.json"
    ev_path = tmp / "fsm-events.jsonl"
    tracker = tmp / "remediation-tracker.jsonl"
    goals_dir = tmp / "goals"
    goals_dir.mkdir()

    failures: list[str] = []

    def seed_state(state: str, cause: str = ""):
        data = {"mode": "WORK", "fsm_state": state, "fsm_validated": True,
                "timestamp": now_iso(), "goal_pct": 40.0}
        if cause:
            data["regression_cause"] = cause
        fm_path.write_text(json.dumps(data) + "\n", encoding="utf-8")

    def lane_goal_count(lane: str) -> int:
        p = goals_dir / f"{lane}.md"
        if not p.exists():
            return 0
        return sum(1 for l in p.read_text(encoding="utf-8").splitlines()
                   if re.match(r"^\s*\d+\.\s+\*\*", l))

    # Pre-seed a lane file with two existing goals so numbering continues at 3.
    (goals_dir / "mechanic.md").write_text(
        "# Mechanic — fixture\n\n1. **G1** - existing\n2. **G2** - existing\n", encoding="utf-8")

    # 1) SEED A REGRESSION (cause routes to mechanic via 'vram') -> auto-opens exactly ONE goal.
    seed_state("REGRESSING", cause="vram oom on host pale")
    out = dispatch(fm_path, tracker, goals_dir)
    if out.get("action") != "opened":
        failures.append(f"expected opened, got {out}")
    if out.get("lane") != "mechanic":
        failures.append(f"expected lane mechanic (vram cause), got {out.get('lane')}")
    if lane_goal_count("mechanic") != 3:
        failures.append(f"expected 3 goals in mechanic.md, got {lane_goal_count('mechanic')}")
    recs = _read_tracker(tracker)
    opens = [r for r in recs if r.get("event") == "open"]
    if len(opens) != 1:
        failures.append(f"expected exactly 1 open record, got {len(opens)}")

    # 2) REPEATED DETECTION -> NO DUPLICATE.
    out2 = dispatch(fm_path, tracker, goals_dir)
    if out2.get("action") != "no-op-already-open":
        failures.append(f"expected idempotent no-op, got {out2}")
    if lane_goal_count("mechanic") != 3:
        failures.append(f"duplicate goal opened! now {lane_goal_count('mechanic')}")
    opens = [r for r in _read_tracker(tracker) if r.get("event") == "open"]
    if len(opens) != 1:
        failures.append(f"tracker should still have 1 open, got {len(opens)}")

    # 3) CLOSURE -> goal line stamped REACHED + FSM flips back to CONVERGING (not REGRESSING).
    close_out = close_cmd(fm_path, tracker, goals_dir)
    if close_out.get("action") != "closed":
        failures.append(f"expected closed, got {close_out}")
    if close_out.get("fsm_state_after") != "CONVERGING":
        failures.append(f"FSM should flip to CONVERGING, got {close_out.get('fsm_state_after')}")
    mech_text = (goals_dir / "mechanic.md").read_text(encoding="utf-8")
    if not any("[REACHED" in l and "[REMEDIATION:" in l
               for l in mech_text.splitlines()):
        failures.append("remediation goal line not stamped [REACHED]")
    closes = [r for r in _read_tracker(tracker) if r.get("event") == "close"]
    if len(closes) != 1:
        failures.append(f"expected exactly 1 close record, got {len(closes)}")

    # 4) CLOSE AGAIN -> idempotent no-op.
    again = close_cmd(fm_path, tracker, goals_dir)
    if again.get("action") != "no-op-nothing-open":
        failures.append(f"expected no-op on second close, got {again}")

    # 5) NEW regression after recovery -> opens a FRESH (different id) remediation.
    seed_state("REGRESSING", cause="dispatch routing stall")   # routes to orchestrator
    out3 = dispatch(fm_path, tracker, goals_dir)
    if out3.get("action") != "opened":
        failures.append(f"expected a fresh open after recovery, got {out3}")
    if out3.get("lane") != "orchestrator":
        failures.append(f"expected lane orchestrator (dispatch cause), got {out3.get('lane')}")
    if out3.get("id") == opens[0]["id"]:
        failures.append("new episode reused the old remediation id (should be unique)")

    # 6) Non-regression state with NO open remediation -> idle, nothing written.
    #    (Use a fresh tracker so step-5's still-open orchestrator goal does not auto-close here.)
    clean_tracker = tmp / "clean-tracker.jsonl"
    seed_state("CONVERGING")
    out4 = dispatch(fm_path, clean_tracker, goals_dir)
    if out4.get("action") != "idle":
        failures.append(f"expected idle on CONVERGING w/o open, got {out4}")

    # 7) cause -> lane map determinism (pure function).
    for cause, want in [("oom vram", "mechanic"), ("dispatch stall", "orchestrator"),
                        ("ui render crash", "designer"), ("canary deploy gate", "forge"),
                        ("", DEFAULT_LANE)]:
        if pick_lane(cause) != want:
            failures.append(f"pick_lane({cause!r}) = {pick_lane(cause)!r}, want {want!r}")

    shutil.rmtree(tmp, ignore_errors=True)
    if failures:
        print("REGRESSION_DISPATCHER SELFTEST FAIL:")
        for f_ in failures:
            print("  -", f_)
        return 1
    print("REGRESSION_DISPATCHER SELFTEST PASS: seeded regression auto-opens exactly one goal "
          "in the correct lane; repeated detection = no duplicate; closure flips FSM back to "
          "CONVERGING + stamps goal reached; re-open after recovery uses a fresh id; cause->lane map deterministic")
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # Handle the bare-word subcommands before flag parsing (keeps argparse simple).
    if "selftest" in argv:
        return selftest()
    show_status = "status" in argv
    argv = [a for a in argv if a not in ("selftest", "status")]

    ap = argparse.ArgumentParser(description="Convergence Regression Auto-Remediation Dispatcher")
    ap.add_argument("--run", action="store_true", help="detect->act on live fleet files")
    ap.add_argument("--close", action="store_true", help="close the open remediation + flip FSM back")
    ap.add_argument("--lane", default=None, help="force target lane (override cause routing)")
    ap.add_argument("--fleet-mode", default=str(FLEET_MODE_PATH))
    ap.add_argument("--tracker", default=str(TRACKER_DEFAULT))
    ap.add_argument("--goals-dir", default=str(GOALS))
    args = ap.parse_args(argv)

    fm_path = Path(args.fleet_mode)
    tracker = Path(args.tracker)
    goals_dir = Path(args.goals_dir)

    if args.close:
        print(json.dumps(close_cmd(fm_path, tracker, goals_dir), indent=2))
        return 0
    if args.run:
        print(json.dumps(dispatch(fm_path, tracker, goals_dir, lane_override=args.lane), indent=2))
        return 0
    # default (and explicit `status`): print state + open remediation
    _ = show_status
    print(json.dumps(status(fm_path, tracker), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
