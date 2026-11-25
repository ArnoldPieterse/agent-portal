"""Self-test for goal_prioritizer.py logic (v2 with autonomy modifier)."""

def lane_urgency(lanes, agent):
    lane = lanes.get(agent, {})
    total = lane.get("total", 10)
    done = lane.get("done", 0)
    if total == 0:
        return 0.0
    return 1.0 - (done / total)

def convergence_score(card, lanes, autonomy=50.0):
    p = card.get("p_reached", 0.5)
    complexity = card.get("complexity", 1)
    hours = max(card.get("hours", 1.0), 0.1)
    urgency = lane_urgency(lanes, card.get("agent", ""))
    base_penalty = (complexity - 1) / 3.0
    autonomy_mod = (autonomy - 50.0) / 100.0 * 0.4
    effective_penalty = max(base_penalty - autonomy_mod, 0.0)
    complexity_factor = max(1.0 - effective_penalty, 0.2)
    return round(p * complexity_factor * urgency / hours, 4)

lanes = {"builder": {"done": 2, "total": 10}, "archivist": {"done": 6, "total": 10}}

# T1: neutral autonomy (50), simple goal
card1 = {"agent": "builder", "p_reached": 0.8, "complexity": 1, "hours": 2.0}
s1 = convergence_score(card1, lanes, 50.0)
assert abs(s1 - round(0.8 * 1.0 * 0.8 / 2.0, 4)) < 0.001, f"T1: {s1}"

# T2: lane done -> urgency 0
lanes2 = {"builder": {"done": 10, "total": 10}}
assert convergence_score(card1, lanes2) == 0.0, "T2 fail"

# T3: high autonomy (90) relaxes complexity penalty vs low autonomy (20)
card_hi = {"agent": "x", "p_reached": 0.8, "complexity": 3, "hours": 1.0}
lanes3 = {"x": {"done": 0, "total": 10}}
s_hi = convergence_score(card_hi, lanes3, 90.0)
s_lo = convergence_score(card_hi, lanes3, 20.0)
assert s_hi > s_lo, f"T3: high={s_hi} low={s_lo}"

# T4: zero hours doesn't crash
card4 = {"agent": "x", "p_reached": 0.5, "complexity": 1, "hours": 0}
assert convergence_score(card4, lanes3) > 0, "T4 fail"

# T5: at autonomy=50, complexity penalty is exactly (c-1)/3
card5 = {"agent": "x", "p_reached": 1.0, "complexity": 2, "hours": 1.0}
s5 = convergence_score(card5, lanes3, 50.0)
expected = round(1.0 * max(1 - (2-1)/3, 0.2) * 1.0 / 1.0, 4)
assert abs(s5 - expected) < 0.001, f"T5: {s5} vs {expected}"

print("selftest 5/5 PASS")
