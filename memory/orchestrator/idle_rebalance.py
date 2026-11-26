#!/usr/bin/env python3
"""
Idle-to-Work Mode Rebalancer (Orchestrator, Cycle 19 goal #4).

Couples pillar-1 (mode SSOT) to pillar-3 (idle productivity):
read per-role productive-pass rate from memory/ops/autoloop.jsonl; when a role's
idle pass is NOT productive for K consecutive passes, flip its next-pass mode
MAINTENANCE -> WORK and log the flip. A productive pass resets the run.

Definitions:
  idle_pass(record) = (task_type != 'WORK') OR (task_type == 'WORK' AND not productive)
      i.e. any pass that yielded no productive work. A productive WORK pass is NOT idle.
  A role starts in mode 'MAINTENANCE'. When its trailing run of consecutive
  idle_passes reaches K, emit exactly one flip {role, ts, from, to, reason, k}
  and set that role's next-pass mode to 'WORK' (monotonic: MAINTENANCE -> WORK).

Idempotency: state file memory/ops/idle-rebalance-state.json stores, per role,
the last processed timestamp + trailing idle run length. Re-running over the same
data produces 0 new flips.

CLI:
  python memory/orchestrator/idle_rebalance.py --selftest   # hermetic synthetic tests
  python memory/orchestrator/idle_rebalance.py [--k K]      # real run (append flips, update state)
"""
import argparse
import json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
AUTOLOOP = ROOT / "memory" / "ops" / "autoloop.jsonl"
FLIPS_OUT = ROOT / "memory" / "ops" / "idle-rebalance-flips.jsonl"
STATE_FILE = ROOT / "memory" / "ops" / "idle-rebalance-state.json"

DEFAULT_K = 3


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_idle_pass(rec):
    """A pass that yielded no productive work."""
    if rec.get("task_type") != "WORK":
        return True
    return not bool(rec.get("productive", False))


def load_records(path=AUTOLOOP):
    out = []
    p = pathlib.Path(path)
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        if "agent" in o:
            out.append(o)
    return out


def _load_state(path=STATE_FILE):
    p = pathlib.Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def _save_state(state, path=STATE_FILE):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(path).write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def detect_flips(records, K=DEFAULT_K, state=None):
    """
    Pure: given ordered pass records + prior per-role state, return (flips, new_state).
    Each role's next-pass mode is tracked. A run of K consecutive idle passes in
    MAINTENANCE mode triggers exactly one flip to WORK.
    state shape: {role: {"last_ts": str|None, "run": int, "mode": "MAINTENANCE"|"WORK"}}
    """
    if state is None:
        state = {}
    new_state = {r: dict(v) for r, v in state.items()}
    flips = []

    # order by timestamp (stable; fall back to input order)
    def key(r):
        return r.get("timestamp") or ""
    ordered = sorted(records, key=key)

    for rec in ordered:
        role = rec.get("agent")
        if not role:
            continue
        ts = rec.get("timestamp") or ""
        st = new_state.setdefault(role, {"last_ts": None, "run": 0, "mode": "MAINTENANCE"})

        # idempotency guard: skip records already processed (same-or-earlier ts than last)
        if st["last_ts"] is not None and ts and ts <= st["last_ts"]:
            continue

        if is_idle_pass(rec):
            st["run"] += 1
            # flip only when stuck in MAINTENANCE and run reaches K; one flip per crossing
            if st["mode"] == "MAINTENANCE" and st["run"] >= K:
                flips.append({
                    "ts": _now(),
                    "role": role,
                    "from": "MAINTENANCE",
                    "to": "WORK",
                    "reason": f"{K} consecutive non-productive idle passes; escalating next-pass mode to WORK",
                    "k": K,
                    "trigger_pass_ts": ts,
                })
                st["mode"] = "WORK"
                st["run"] = 0  # reset after flip so the same crossing doesn't re-fire
        else:
            # productive pass resets the idle run (mode persists)
            st["run"] = 0

        if ts:
            st["last_ts"] = ts

    return flips, new_state


def real_run(K=DEFAULT_K):
    records = load_records(AUTOLOOP)
    state = _load_state(STATE_FILE)
    flips, new_state = detect_flips(records, K=K, state=state)
    if flips:
        FLIPS_OUT.parent.mkdir(parents=True, exist_ok=True)
        with open(FLIPS_OUT, "a", encoding="utf-8") as f:
            for fl in flips:
                f.write(json.dumps(fl) + "\n")
    _save_state(new_state, STATE_FILE)
    summary = {
        "ts": _now(),
        "k": K,
        "records_scanned": len(records),
        "flips_emitted_this_run": len(flips),
        "roles_in_WORK_mode": sorted([r for r, v in new_state.items() if v["mode"] == "WORK"]),
        "flips_out": str(FLIPS_OUT.relative_to(ROOT)),
    }
    return summary


def selftest():
    ok = 0
    total = 4

    # T1: synthetic unproductive-idle sequence -> exactly one flip per threshold crossing
    K = 3
    recs = []
    base_ts = "2026-11-26T00:00:00Z"
    for i in range(5):  # 5 consecutive idle passes, K=3 -> one flip at the 3rd
        recs.append({"timestamp": f"{base_ts[:-1]}:{i:02d}Z", "agent": "R1",
                     "task_type": "WORK", "productive": False})
    flips, _ = detect_flips(recs, K=K)
    assert len(flips) == 1, f"T1 expected 1 flip, got {len(flips)}"
    assert flips[0]["role"] == "R1" and flips[0]["to"] == "WORK", "T1 flip shape wrong"
    ok += 1

    # T2: productive idle (productive WORK passes) does NOT flip
    recs2 = [{"timestamp": f"{base_ts[:-1]}:{i:02d}Z", "agent": "R2",
              "task_type": "WORK", "productive": True} for i in range(6)]
    flips2, _ = detect_flips(recs2, K=K)
    assert len(flips2) == 0, f"T2 expected 0 flips, got {len(flips2)}"
    ok += 1

    # T3: flips logged with role + ts + reason
    recs3 = [{"timestamp": f"{base_ts[:-1]}:{i:02d}Z", "agent": "R3",
              "task_type": "MAINTENANCE", "productive": False} for i in range(K)]
    flips3, _ = detect_flips(recs3, K=K)
    assert len(flips3) == 1
    f = flips3[0]
    assert f.get("role") == "R3" and f.get("ts") and f.get("reason"), "T3 missing role/ts/reason"
    ok += 1

    # T4: idempotent on re-run (second run over same records -> 0 new flips)
    recs4 = [{"timestamp": f"{base_ts[:-1]}:{i:02d}Z", "agent": "R4",
              "task_type": "WORK", "productive": False} for i in range(K + 2)]
    flips_a, state_a = detect_flips(recs4, K=K)
    assert len(flips_a) == 1
    flips_b, _ = detect_flips(recs4, K=K, state=state_a)  # re-run with prior state
    assert len(flips_b) == 0, f"T4 expected 0 on re-run, got {len(flips_b)}"
    ok += 1

    print(f"idle_rebalance selftest: {ok}/{total} PASS")
    return ok == total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--k", type=int, default=DEFAULT_K)
    a = ap.parse_args()
    if a.selftest:
        ok = selftest()
        raise SystemExit(0 if ok else 1)
    summary = real_run(K=a.k)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
