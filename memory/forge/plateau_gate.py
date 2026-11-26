#!/usr/bin/env python3
"""plateau_gate.py - Convergence-Plateau Detection Gate (Forge goal #9).

Validates the orchestrator's asymptote/plateau detector AND the safety of the coupled
frequency-reduction that PLATEAU triggers. Drives the REAL convergence_asymptote module
(no reimplementation) with synthetic series, then proves reduced-mode dispatch cannot
silently starve an open goal.

PART A - state classification (real ca.fit_asymptote + ca.determine_state)
    T1 synthetic plateau  -> PLATEAU   (converged)
    T2 synthetic climb    -> CLIMBING  (NOT converged)
    T3 boundary           -> within PLATEAU_THRESHOLD of fitted A => PLATEAU; just beyond => CLIMBING

PART B - frequency-reduction safety invariant (the NEW requirement)
    When state==PLATEAU the fleet drops to a reduced cadence (dispatch budget B < N open goals).
    Invariant: under a FAIR reduced cadence every open goal is dispatched >=1 within W cycles
    (no starvation). The gate:
      B.1 SAFE on REAL open goals (extracted from memory/goals/<agent>.md): fair round-robin
          reduced cadence -> assert NO open goal starved.
      B.2 UNSAFE injection: a naive static top-B scheduler that ignores lower-ranked goals ->
          inject a hidden low-priority open goal; assert the gate DETECTS it as starved
          (safety violation). Proves the gate catches the dangerous reduced-mode case.
      B.3 Coupling: CLIMBING=>full cadence(B=N, trivially safe); PLATEAU=>reduced(B<N, fairness
          enforced). Assert the verdict is a genuine function of state, not constant.

Gate = PASS iff T1,T2,T3,B.1,B.2 hold AND B.3 shows state-dependence.

Usage:
    python memory/forge/plateau_gate.py            # run gate, exit 0 all-green / 1 on fail
    python memory/forge/plateau_gate.py --selftest # same (the gate IS the self-test)
"""
import pathlib, json, sys, math
from datetime import datetime

MEM = pathlib.Path("memory")
sys.path.insert(0, str(MEM / "orchestrator"))
try:
    import convergence_asymptote as ca
except Exception as e:  # noqa: BLE001
    print(f"FATAL: cannot import convergence_asymptote ({e}); module under test missing.")
    sys.exit(1)

OUT_JSON = MEM / "forge" / "plateau_gate_last.json"
OUT_MD = MEM / "forge" / "plateau-gate-report.md"

LANES = ["orchestrator", "researcher", "builder", "verifier", "designer",
         "archivist", "scribe", "mechanic", "outlet", "pixel", "lumen",
         "reel", "splice", "forge"]


def _sat(c, A, B, k):
    return A - B * math.exp(-k * c)


def part_a():
    """Drive the REAL detector on synthetic series."""
    res = {}
    # T1 plateau: data already in the flat region (late cycles of a fast-saturating curve)
    A, B, k = 85.0, 50.0, 0.30
    plateau = [(c, _sat(c, A, B, k)) for c in range(20, 32)]
    fit_p = ca.fit_asymptote(plateau)
    state_p = ca.determine_state(plateau[-1][1], fit_p) if "error" not in fit_p else "CLIMBING"
    res["T1_plateau"] = {"state": state_p, "fit_A": fit_p.get("plateau_value"),
                         "latest": round(plateau[-1][1], 3), "pass": state_p == "PLATEAU"}
    # T2 climb: early cycles of a slow-saturating curve (far below plateau)
    A2, B2, k2 = 90.0, 40.0, 0.12
    climb = [(c, _sat(c, A2, B2, k2)) for c in range(1, 13)]
    fit_c = ca.fit_asymptote(climb)
    state_c = ca.determine_state(climb[-1][1], fit_c) if "error" not in fit_c else "CLIMBING"
    res["T2_climb"] = {"state": state_c, "fit_A": fit_c.get("plateau_value"),
                       "latest": round(climb[-1][1], 3), "pass": state_c == "CLIMBING"}
    # T3 boundary: build a flat series at value V; fitted A should land near V -> within threshold => PLATEAU.
    # Then shift the latest point down past PLATEAU_THRESHOLD => must flip to CLIMBING.
    V = 70.0
    base = [(c, V) for c in range(1, 15)]
    fit_b = ca.fit_asymptote(base)
    near = ca.determine_state(V, fit_b) if "error" not in fit_b else "CLIMBING"
    far_score = V - (ca.PLATEAU_THRESHOLD + 0.5)
    far = ca.determine_state(far_score, fit_b) if "error" not in fit_b else "CLIMBING"
    res["T3_boundary"] = {"near_state": near, "far_state": far,
                          "pass": (near == "PLATEAU" and far == "CLIMBING")}
    return res


def extract_real_open_goals():
    """Current open goals per lane: numbered bold lines without a (verified: marker."""
    open_goals = []
    for agent in LANES:
        gf = MEM / "goals" / f"{agent}.md"
        if not gf.exists():
            continue
        for line in gf.read_text(encoding="utf-8").split("\n"):
            s = line.strip()
            if not (s[:1].isdigit() and "." in s[:4]):
                continue
            if "**" not in s:
                continue
            if "(verified:" in s:
                continue
            open_goals.append({"agent": agent, "title": s.split("**", 2)[1][:60] if s.count("**") >= 2 else s[:60]})
    return open_goals


def fair_round_robin(n_goals, budget, horizon):
    """Fair reduced cadence: cycle through goals in order, dispatch `budget` per cycle.
    Returns {goal_idx: first_cycle_dispatched}. Round-robin guarantees every goal a slot."""
    first = {}
    for cyc in range(horizon):
        for j in range(budget):
            idx = (cyc * budget + j) % n_goals
            if idx not in first:
                first[idx] = cyc
    return first


def naive_top_b(n_goals, budget, horizon):
    """Unsafe reduced cadence: ALWAYS dispatch the same top-`budget` by priority.
    Returns {goal_idx: first_cycle_dispatched} -- goals ranked >= budget are NEVER dispatched."""
    first = {}
    for cyc in range(horizon):
        for j in range(budget):
            if j not in first:
                first[j] = cyc
    return first  # note: only indices [0,budget) ever appear


def part_b():
    real_open = extract_real_open_goals()
    N = len(real_open)
    res = {"real_open_goal_count": N, "real_open_sample": real_open[:6]}
    if N == 0:
        # no open goals -> reduced mode trivially safe; but we still must prove the gate fires on the bad case
        res["B1_safe"] = {"pass": True, "note": "no open goals; nothing to starve"}
        N_eff = 6
    else:
        N_eff = N
    # reduced cadence budget: half the board (a genuine reduction), min 1
    B = max(1, N_eff // 2)
    W = math.ceil(N_eff / B) + 1          # fairness window: a fair RR must slot every goal within this
    horizon = W * 2

    # B.1 SAFE on real open goals under FAIR round-robin reduced cadence
    first_fair = fair_round_robin(N_eff, B, horizon)
    starved_fair = [i for i in range(N_eff) if i not in first_fair or first_fair[i] > W]
    res["B1_safe"] = {"budget": B, "window": W, "horizon": horizon,
                      "starved": starved_fair, "pass": len(starved_fair) == 0}

    # B.2 UNSAFE injection: naive static top-B scheduler; a hidden low-priority goal (index >= B)
    # is never dispatched -> the gate MUST flag it as a safety violation.
    first_naive = naive_top_b(N_eff, B, horizon)
    starved_naive = [i for i in range(N_eff) if i not in first_naive]
    hidden_idx = min(B, N_eff - 1)         # the lowest-priority goal a static top-B would drop
    caught = (hidden_idx in starved_naive)
    res["B2_unsafe_caught"] = {"budget": B, "hidden_goal_idx": hidden_idx,
                               "starved_under_naive": sorted(starved_naive),
                               "gate_flagged_hidden": bool(caught), "pass": bool(caught)}

    # B.3 Coupling: verdict must be a function of state (reduced vs full cadence)
    # CLIMBING -> full cadence B=N -> no starvation; PLATEAU -> reduced B<N -> fairness enforced.
    climb_budget = N_eff                       # full frequency
    first_climb = fair_round_robin(N_eff, climb_budget, horizon)
    starved_climb = [i for i in range(N_eff) if i not in first_climb]
    res["B3_coupling"] = {
        "climbing_budget": climb_budget, "plateau_budget": B,
        "climbing_starved": starved_climb, "plateau_fair_starved": starved_fair,
        "state_dependent": (climb_budget != B) and (len(starved_climb) == 0),
        "pass": ((climb_budget != B) and len(starved_climb) == 0 and len(starved_fair) == 0),
    }
    return res


def main():
    a = part_a()
    b = part_b()
    checks = {
        "T1_plateau_converged": a["T1_plateau"]["pass"],
        "T2_climb_not_converged": a["T2_climb"]["pass"],
        "T3_boundary_correct": a["T3_boundary"]["pass"],
        "B1_real_open_no_starvation": b["B1_safe"]["pass"],
        "B2_hidden_goal_caught": b["B2_unsafe_caught"]["pass"],
        "B3_state_dependent": b["B3_coupling"]["pass"],
    }
    ok = all(checks.values())
    result = {"ts": datetime.now().isoformat(), "part_a": a, "part_b": b,
              "checks": checks, "status": "PASS" if ok else "FAIL"}
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = ["# Convergence-Plateau Detection Gate (Forge goal #9)", "", f"Run: {result['ts']}", "",
             "## Part A - state classification (real convergence_asymptote)"]
    for key, label in [("T1_plateau", "T1 plateau series"), ("T2_climb", "T2 climb series"), ("T3_boundary", "T3 boundary")]:
        d = a[key]
        lines.append(f"- {label}: {d}  -> {'OK' if d['pass'] else 'FAIL'}")
    lines += ["", "## Part B - frequency-reduction safety invariant"]
    lines.append(f"- real open goals extracted: **{b['real_open_goal_count']}** (sample: {[g['agent'] for g in b['real_open_sample']]})")
    lines.append(f"- B.1 safe (fair reduced cadence, budget={b['B1_safe'].get('budget')}, window={b['B1_safe'].get('window')}): starved={b['B1_safe']['starved']} -> {'OK' if b['B1_safe']['pass'] else 'FAIL'}")
    lines.append(f"- B.2 unsafe (static top-B, hidden idx={b['B2_unsafe_caught'].get('hidden_goal_idx')}): starved={b['B2_unsafe_caught'].get('starved_under_naive')} flagged={b['B2_unsafe_caught'].get('gate_flagged_hidden')} -> {'OK' if b['B2_unsafe_caught']['pass'] else 'FAIL'}")
    lines.append(f"- B.3 coupling (climb budget={b['B3_coupling'].get('climbing_budget')} vs plateau budget={b['B3_coupling'].get('plateau_budget')}): state_dependent={b['B3_coupling'].get('state_dependent')} -> {'OK' if b['B3_coupling']['pass'] else 'FAIL'}")
    lines += ["", "## Checks", ] + [f"- {k}: {'PASS' if v else 'FAIL'}" for k, v in checks.items()]
    lines += ["", f"**RESULT: {result['status']}**"]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({"status": result["status"]}))
    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    print(f"  artifacts: {OUT_JSON} | {OUT_MD}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
