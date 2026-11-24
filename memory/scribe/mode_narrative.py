"""mode_narrative.py — auto-generate a 3-sentence narrative for each fleet-mode transition.

Reads memory/ops/mode-transitions.jsonl; writes new narratives to memory/ops/mode-narratives.jsonl.
Tracks already-narrated transitions by timestamp so re-runs are idempotent.

Usage: python memory/scribe/mode_narrative.py [--simulate N]
  --simulate N: append N synthetic transitions first (for testing), then narrate all new ones.
"""
import json, sys, datetime, pathlib

TRANSITIONS = pathlib.Path("memory/ops/mode-transitions.jsonl")
NARRATIVES  = pathlib.Path("memory/ops/mode-narratives.jsonl")

def _load_jsonl(path):
    if not path.exists():
        return []
    out = []
    decoder = json.JSONDecoder()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        idx = 0
        while idx < len(line):
            try:
                obj, end = decoder.raw_decode(line, idx)
                out.append(obj)
                idx = end
                while idx < len(line) and line[idx] in ' \t':
                    idx += 1
            except json.JSONDecodeError:
                break
    return out

def _append_jsonl(path, records):
    # Ensure file ends with newline before appending (avoids concatenation bug)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing and not existing.endswith("\n"):
            with open(path, "a", encoding="utf-8") as f:
                f.write("\n")
    with open(path, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

def generate_narrative(t):
    """Return a 3-sentence narrative string for transition dict t."""
    ts   = t.get("ts", "unknown time")
    frm  = t.get("from_mode", "UNKNOWN")
    to   = t.get("to_mode", "UNKNOWN")
    trig = t.get("trigger", "unspecified trigger")
    pct  = t.get("goal_pct", None)
    agent= t.get("agent", "system")

    # Sentence 1: what changed + when
    s1 = f"At {ts}, the fleet transitioned from {frm} to {to}."

    # Sentence 2: why (trigger + goal state)
    if pct is not None:
        s2 = f"The trigger was \'{trig}\' with goal completion at {pct:.0f}%."
    else:
        s2 = f"The trigger was \'{trig}\'."

    # Sentence 3: what it means for agents
    if to == "MAINTENANCE":
        s3 = ("Agents will now receive role-specific maintenance tasks from the idle-rotation table "
              "instead of goal dispatch, keeping the fleet productive during the lull.")
    elif to == "IDLE":
        s3 = ("All agents enter standby; no new tasks are dispatched until the next cycle begins.")
    elif to == "WORK":
        s3 = ("Agents resume normal goal dispatch from next10.json; maintenance tasks are paused.")
    else:
        s3 = f"Agents will adjust their behaviour to match the {to} mode."

    return f"{s1} {s2} {s3}"

def simulate_transitions(n):
    """Append n synthetic transitions for testing."""
    base_ts = datetime.datetime(2026, 11, 24, 14, 0, 0)
    modes   = ["WORK", "MAINTENANCE", "IDLE"]
    triggers= ["goal_pct_threshold", "cycle_closeout", "new_cycle_start"]
    new = []
    for i in range(n):
        t = {
            "ts":      (base_ts + datetime.timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "from_mode": modes[i % len(modes)],
            "to_mode":   modes[(i + 1) % len(modes)],
            "trigger":   triggers[i % len(triggers)],
            "goal_pct":  float(50 + i * 15),
            "agent":     "orchestrator",
        }
        new.append(t)
    _append_jsonl(TRANSITIONS, new)
    return new

def main():
    simulate_n = 0
    if "--simulate" in sys.argv:
        idx = sys.argv.index("--simulate")
        if idx + 1 < len(sys.argv):
            simulate_n = int(sys.argv[idx + 1])

    if simulate_n:
        print(f"[simulate] appending {simulate_n} synthetic transitions …")
        simulate_transitions(simulate_n)

    transitions = _load_jsonl(TRANSITIONS)
    narratives  = _load_jsonl(NARRATIVES)
    done_ts     = {n["ts"] for n in narratives}

    new_narrs = []
    for t in transitions:
        if t["ts"] not in done_ts:
            narr = generate_narrative(t)
            rec  = {"ts": t["ts"], "from_mode": t["from_mode"], "to_mode": t["to_mode"],
                    "narrative": narr}
            new_narrs.append(rec)

    if new_narrs:
        _append_jsonl(NARRATIVES, new_narrs)
        print(f"[mode_narrative] wrote {len(new_narrs)} new narrative(s) to {NARRATIVES}")
    else:
        print("[mode_narrative] no new transitions to narrate")

    # Print all narratives for verification
    all_n = _load_jsonl(NARRATIVES)
    print(f"\nTotal narratives on file: {len(all_n)}")
    for n in all_n:
        print(f"  [{n['ts']}] {n['from_mode']}→{n['to_mode']}: {n['narrative'][:80]}…")

if __name__ == "__main__":
    main()
