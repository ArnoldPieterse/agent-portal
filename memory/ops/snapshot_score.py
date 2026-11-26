"""Append current autonomy-score.json to history (run each cycle).

Usage: python memory/ops/snapshot_score.py
Appends one line to memory/ops/autonomy-score-history.jsonl per invocation.
Idempotent: skips if the latest entry has the same computed_at timestamp.
"""
import json, pathlib, sys

SCORE = pathlib.Path("memory/ops/autonomy-score.json")
HISTORY = pathlib.Path("memory/ops/autonomy-score-history.jsonl")

def main():
    if not SCORE.exists():
        print(f"[snapshot_score] SKIP: {SCORE} not found")
        return 0

    current = json.loads(SCORE.read_text(encoding="utf-8"))
    ts = current.get("computed_at", "")

    # Check if already recorded
    if HISTORY.exists():
        lines = HISTORY.read_text(encoding="utf-8").strip().split("\n")
        if lines:
            last = json.loads(lines[-1])
            if last.get("timestamp") == ts:
                print(f"[snapshot_score] SKIP: same timestamp {ts}")
                return 0

    entry = {
        "timestamp": ts,
        "score": current.get("score"),
        "fleet_readiness": current.get("fleet_readiness"),
        "components": current.get("components", {}),
        "fleet_components": current.get("fleet_components", {}),
        "source": "auto-snapshot"
    }

    with open(HISTORY, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    print(f"[snapshot_score] OK: appended score={entry['score']} at {ts}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
