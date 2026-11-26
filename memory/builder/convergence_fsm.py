#!/usr/bin/env python3
"""convergence_fsm.py - Single Source of Truth for the Fleet Convergence lifecycle.

Builder goal 1 (Cycle 20): one authoritative FSM for the convergence lifecycle
(DISCOVERING -> CONVERGING -> STEADY-STATE <-> REGRESSING -> RECONVERGING) with a
legal-transition table. Every mode writer / sentinel / closeout must emit through
this module; illegal transitions are REJECTED and logged to memory/ops/fsm-events.jsonl.

Distinct from fleet_mode_writer.py, which only atomically writes the operational
mode (WORK/MAINTENANCE/IDLE) with no lifecycle state validation. This module adds
the missing state-machine layer on top of it: it persists `fsm_state` +
`fsm_validated:true` into memory/ops/fleet-mode.json via the existing atomic writer.

States:
  DISCOVERING    - scouting / defining goals for a new cycle
  CONVERGING     - actively working toward convergence (score rising)
  STEADY_STATE   - converged plateau (100% or asymptote reached)
  REGRESSING     - autonomy score dropped beyond threshold (regression detected)
  RECONVERGING   - recovering from a regression back toward steady state

CLI:
  python convergence_fsm.py selftest                 # run unit assertions, exit 0/1
  python convergence_fsm.py get                      # print current fsm_state
  python convergence_fsm.py transition TO [--reason R] [--source S]
  python convergence_fsm.py legal FROM               # list legal targets from state
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent            # memory/builder
OPS = HERE.parent / "ops"
FLEET_MODE_PATH = OPS / "fleet-mode.json"
EVENTS_PATH = OPS / "fsm-events.jsonl"

# Canonical state names (single spelling; aliases map to these).
STATES = ("DISCOVERING", "CONVERGING", "STEADY_STATE", "REGRESSING", "RECONVERGING")
STATE_ALIASES = {
    "STEADY-STATE": "STEADY_STATE",
    "STEADY": "STEADY_STATE",
    "SS": "STEADY_STATE",
}

# Legal transition table: state -> set of states you may move to next.
# Self-loops are legal (re-emitting the same state is a no-op refresh).
LEGAL = {
    "DISCOVERING":   {"CONVERGING", "DISCOVERING"},
    "CONVERGING":    {"STEADY_STATE", "REGRESSING", "CONVERGING"},
    "STEADY_STATE":  {"REGRESSING", "CONVERGING", "STEADY_STATE"},
    "REGRESSING":    {"RECONVERGING", "REGRESSING", "CONVERGING"},
    "RECONVERGING":  {"STEADY_STATE", "CONVERGING", "REGRESSING", "RECONVERGING"},
}

# The initial state for a fresh fleet-mode.json with no fsm_state yet.
INITIAL_STATE = "DISCOVERING"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(state: str) -> str | None:
    """Map an alias/raw string to a canonical state, or None if unknown."""
    if not isinstance(state, str):
        return None
    s = state.strip().upper()
    s = STATE_ALIASES.get(s, s)
    return s if s in STATES else None


def legal_targets(state: str) -> set[str]:
    """Return the set of states reachable from `state` (normalized)."""
    s = normalize(state)
    return set(LEGAL[s]) if s else set()


def is_legal(src: str, dst: str) -> bool:
    """True iff src -> dst is a legal transition."""
    n_dst = normalize(dst)
    return n_dst in legal_targets(src)


class ConvergenceFSM:
    """Authoritative convergence-lifecycle state machine.

    Persists current state as `fsm_state` + `fsm_validated:true` inside
    memory/ops/fleet-mode.json (via the atomic writer) and appends every
    transition attempt to memory/ops/fsm-events.jsonl.
    """

    def __init__(self, fleet_mode_path: Path | str = FLEET_MODE_PATH,
                 events_path: Path | str = EVENTS_PATH):
        self.fleet_mode_path = Path(fleet_mode_path)
        self.events_path = Path(events_path)

    # ---- persistence ---------------------------------------------------
    def _read_fleet_mode(self) -> dict:
        try:
            data = json.loads(self.fleet_mode_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def current_state(self) -> str:
        """Current FSM state. If fleet-mode.json has no valid fsm_state yet,
        returns INITIAL_STATE (does not write)."""
        fm = self._read_fleet_mode()
        s = normalize(fm.get("fsm_state"))
        return s if s else INITIAL_STATE

    def _write_fleet_mode(self, new_state: str) -> bool:
        """Stamp fsm_state + fsm_validated into fleet-mode.json atomically.
        Delegates to the existing atomic writer when available (no bypass),
        otherwise falls back to a temp+os.replace write."""
        fm = self._read_fleet_mode()
        fm["fsm_state"] = new_state
        fm["fsm_validated"] = True
        fm.setdefault("timestamp", _now())
        try:
            sys.path.insert(0, str(HERE))
            import fleet_mode_writer as _w  # atomic + schema-validated write
            return _w.write_mode(fm, self.fleet_mode_path)
        except Exception:
            # Fallback: atomic temp+replace so a missing writer never loses state.
            import os, tempfile
            try:
                fd, tmp = tempfile.mkstemp(prefix=".fsm-", suffix=".tmp",
                                           dir=str(self.fleet_mode_path.parent))
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(fm, f, indent=2)
                    f.write("\n")
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp, str(self.fleet_mode_path))
                return True
            except OSError:
                return False

    def _log_event(self, src: str, dst: str, legal: bool, reason: str, source: str) -> None:
        rec = {"ts": _now(), "from": src, "to": dst, "legal": legal,
               "reason": reason or "", "source": source or "unknown"}
        try:
            self.events_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.events_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
        except OSError:
            pass  # never let logging break the transition path

    # ---- core API ------------------------------------------------------
    def can_transition(self, dst: str) -> bool:
        return is_legal(self.current_state(), dst)

    def transition(self, dst: str, reason: str = "", source: str = "convergence_fsm") -> dict:
        """Attempt a transition to `dst`.

        Legal  -> persisted + logged (legal=true), returns {ok:True,...}
        Illegal-> REJECTED (state unchanged) + logged (legal=false),
                 returns {ok:False, error:...}. Never raises for an illegal move.
        """
        src = self.current_state()
        n_dst = normalize(dst)
        if n_dst is None:
            self._log_event(src, str(dst), False, reason or f"unknown state {dst!r}", source)
            return {"ok": False, "from": src, "to": str(dst),
                    "error": f"unknown state {dst!r} (valid: {list(STATES)})"}
        if not is_legal(src, n_dst):
            self._log_event(src, n_dst, False, reason or f"illegal {src}->{n_dst}", source)
            return {"ok": False, "from": src, "to": n_dst,
                    "error": f"illegal transition {src}->{n_dst}; legal: {sorted(legal_targets(src))}"}
        self._write_fleet_mode(n_dst)
        self._log_event(src, n_dst, True, reason, source)
        return {"ok": True, "from": src, "to": n_dst, "state": n_dst}


def _selftest() -> int:
    """Unit assertions: every legal transition accepted; a seeded illegal one
    rejected + logged. Uses throwaway temp files so the live fleet-mode.json is
    never mutated by the test."""
    import tempfile
    tmpdir = Path(tempfile.mkdtemp(prefix="fsm-selftest-"))
    fm_path = tmpdir / "fleet-mode.json"
    ev_path = tmpdir / "fsm-events.jsonl"
    fm_path.write_text(json.dumps({"mode": "WORK", "timestamp": _now(), "goal_pct": 100.0}) + "\n",
                       encoding="utf-8")
    fsm = ConvergenceFSM(fm_path, ev_path)

    failures: list[str] = []
    # 1) Initial state resolves (no fsm_state yet -> INITIAL_STATE).
    if fsm.current_state() != INITIAL_STATE:
        failures.append(f"initial state expected {INITIAL_STATE}, got {fsm.current_state()}")

    # 2) Every legal transition is accepted and persisted.
    for src in STATES:
        for dst in sorted(LEGAL[src]):
            # force the machine into `src` by seeding fsm_state directly (test harness).
            data = json.loads(fm_path.read_text(encoding="utf-8"))
            data["fsm_state"] = src
            fm_path.write_text(json.dumps(data) + "\n", encoding="utf-8")
            res = fsm.transition(dst, reason="selftest", source="selftest")
            if not res.get("ok"):
                failures.append(f"legal {src}->{dst} rejected: {res.get('error')}")
            elif ConvergenceFSM(fm_path, ev_path).current_state() != dst:
                failures.append(f"legal {src}->{dst} not persisted")

    # 3) A seeded ILLEGAL transition is rejected and logged.
    data = json.loads(fm_path.read_text(encoding="utf-8"))
    data["fsm_state"] = "STEADY_STATE"
    fm_path.write_text(json.dumps(data) + "\n", encoding="utf-8")
    before = ConvergenceFSM(fm_path, ev_path).current_state()
    res = fsm.transition("DISCOVERING", reason="selftest-illegal", source="selftest")
    after = ConvergenceFSM(fm_path, ev_path).current_state()
    if res.get("ok"):
        failures.append(f"illegal STEADY_STATE->DISCOVERING was accepted (should reject)")
    if before != after:
        failures.append(f"illegal transition mutated state: {before} -> {after}")
    ev = [json.loads(l) for l in ev_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    illegal_logged = any(e["to"] == "DISCOVERING" and e["from"] == "STEADY_STATE"
                         and e["legal"] is False for e in ev)
    if not illegal_logged:
        failures.append("illegal transition not logged to fsm-events.jsonl")

    # 4) fleet-mode.json carries fsm_state + fsm_validated:true after a legal move.
    data = json.loads(fm_path.read_text(encoding="utf-8"))
    if not (data.get("fsm_validated") is True and data.get("fsm_state") in STATES):
        failures.append(f"fleet-mode.json missing fsm_state/fsm_validated: {data.get('fsm_state')}/{data.get('fsm_validated')}")

    if failures:
        print("FSM SELFTEST FAIL:")
        for f_ in failures:
            print("  -", f_)
        return 1
    n_legal = sum(len(v) for v in LEGAL.values())
    print(f"FSM SELFTEST PASS: {n_legal} legal transitions accepted, illegal rejected+logged, "
          f"fleet-mode.json stamped fsm_state+fsm_validated")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[1] == "selftest":
        return _selftest()
    fsm = ConvergenceFSM()
    if len(argv) >= 2 and argv[1] == "get":
        print(json.dumps({"fsm_state": fsm.current_state(),
                          "legal_targets": sorted(legal_targets(fsm.current_state()))}))
        return 0
    if len(argv) >= 3 and argv[1] == "transition":
        dst = argv[2]
        reason = source = ""
        i = 3
        while i < len(argv):
            if argv[i] == "--reason" and i + 1 < len(argv):
                reason = argv[i + 1]; i += 2
            elif argv[i] == "--source" and i + 1 < len(argv):
                source = argv[i + 1]; i += 2
            else:
                i += 1
        res = fsm.transition(dst, reason=reason, source=source or "cli")
        print(json.dumps(res))
        return 0 if res.get("ok") else 1
    if len(argv) >= 3 and argv[1] == "legal":
        print(json.dumps({"from": normalize(argv[2]) or argv[2],
                          "targets": sorted(legal_targets(argv[2]))}))
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
