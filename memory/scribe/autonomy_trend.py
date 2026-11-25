"""autonomy_trend.py - Append cycle autonomy scores to memory/scribe/autonomy-trend.jsonl.

Usage: python memory/scribe/autonomy_trend.py [--cycle N] [--score S] [--components JSON]
Without args, reads current score from memory/ops/autonomy-score.json and appends.
Flags 3-cycle rolling trend reversal.
"""
import json, pathlib, sys
from datetime import datetime, timezone

TREND_FILE = pathlib.Path("memory/scribe/autonomy-trend.jsonl")
SOURCE_FILE = pathlib.Path("memory/ops/autonomy-score.json")

def load_trend():
    if TREND_FILE.exists():
        return [json.loads(line) for line in TREND_FILE.read_text(encoding="utf-8").strip().splitlines() if line.strip()]
    return []

def save_trend(entries):
    TREND_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TREND_FILE, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

def check_reversal(entries):
    """Flag when 3-cycle rolling trend reverses direction."""
    if len(entries) < 3:
        return None
    last3 = [e["score"] for e in entries[-3:]]
    # Trend is the direction of (last - first) over the window
    prev_trend = last3[1] - last3[0]
    curr_trend = last3[2] - last3[1]
    if prev_trend * curr_trend < 0:  # sign change = reversal
        return {"reversal": True, "prev_direction": "up" if prev_trend > 0 else "down",
                "curr_direction": "up" if curr_trend > 0 else "down"}
    return None

def append_entry(cycle, score, components, timestamp=None):
    entries = load_trend()
    delta = None
    if entries:
        delta = round(score - entries[-1]["score"], 2)
    entry = {
        "ts": timestamp or datetime.now(timezone.utc).isoformat(),
        "cycle": cycle,
        "score": score,
        "delta_from_prev": delta,
        "component_breakdown": components,
        "reversal_flag": check_reversal(entries + [{"score": score}]) if len(entries) >= 2 else None
    }
    entries.append(entry)
    save_trend(entries)
    return entry

def main():
    # Read current score from source
    if SOURCE_FILE.exists():
        src = json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
        score = src["score"]
        components = src.get("components", {})
        ts = src.get("computed_at", datetime.now(timezone.utc).isoformat())
    else:
        print("ERROR: No source file at", SOURCE_FILE)
        sys.exit(1)

    # Determine cycle from fleet-mode.json or default
    cycle = None
    mode_file = pathlib.Path("memory/ops/fleet-mode.json")
    if mode_file.exists():
        mode = json.loads(mode_file.read_text(encoding="utf-8"))
        # Infer cycle from timestamp (approximate: cycles ~daily)
        cycle = 17  # current known cycle

    entry = append_entry(cycle, score, components, ts)
    print(json.dumps(entry, indent=2))

if __name__ == "__main__":
    main()
