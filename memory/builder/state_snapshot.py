"""Fleet State Snapshot Scheduler (Builder Goal #10).

Every 30 min (via schtask), captures full fleet state and appends to
memory/ops/fleet-snapshots.jsonl.

Usage:
  python memory/builder/state_snapshot.py           # take one snapshot
  python memory/builder/state_snapshot.py --register  # register schtask
  python memory/builder/state_snapshot.py --check    # validate JSONL integrity
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SNAPSHOT_FILE = Path("memory/ops/fleet-snapshots.jsonl")
HEALTH_SCORE_FILE = Path("memory/ops/health-score.jsonl")
BLOCKERS_FILE = Path("memory/ops/blockers.md")
GOALS_DIR = Path("memory/goals")
ROSTER_DIR = Path("memory/fleet/roster-snapshots")


def get_agent_statuses() -> list:
    """Get agent statuses from latest roster snapshot."""
    snapshots = sorted(ROSTER_DIR.glob("*.json"))
    if not snapshots:
        return []
    data = json.loads(snapshots[-1].read_text(encoding="utf-8"))
    agents = []
    for a in data.get("agents", []):
        agents.append({
            "id": a.get("id", ""),
            "name": a.get("name", ""),
            "model_id": a.get("model_id", ""),
            "status": "unknown",  # would be live if API available
        })
    return agents


def get_host_resources() -> list:
    """Get host resource info. Falls back to empty if no probes available."""
    hosts = []
    # Try reading from probe files if they exist
    probe_dir = Path("memory/fleet")
    for f in probe_dir.glob("*probe*"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            hosts.append(data)
        except Exception:
            pass
    # If no probes, report known host names with unavailable status
    if not hosts:
        for name in ["White", "Black", "Red", "Blue"]:
            hosts.append({"host": name, "vram_pct": None, "cpu_pct": None, "gpu_temp": None})
    return hosts


def get_goal_progress() -> dict:
    """Parse goal progress from all goal files."""
    progress = {}
    if not GOALS_DIR.exists():
        return progress
    for gf in sorted(GOALS_DIR.glob("*.md")):
        if gf.name.startswith(("closed_", "archive", "INDEX")):
            continue
        text = gf.read_text(encoding="utf-8")
        total = len(re.findall(r"^\d+\.\s+\*\*", text, re.MULTILINE))
        verified = len(re.findall(r"\(verified:", text))
        progress[gf.stem] = {"total": total, "verified": verified}
    return progress


def get_health_score() -> dict:
    """Get latest health score."""
    if not HEALTH_SCORE_FILE.exists():
        return {"score": None, "ts": None}
    lines = HEALTH_SCORE_FILE.read_text(encoding="utf-8").strip().split("\n")
    if not lines:
        return {"score": None, "ts": None}
    try:
        last = json.loads(lines[-1])
        return {"score": last.get("score"), "ts": last.get("ts")}
    except json.JSONDecodeError:
        return {"score": None, "ts": None}


def get_open_blockers() -> list:
    """Count and list open blockers from blockers.md."""
    if not BLOCKERS_FILE.exists():
        return []
    text = BLOCKERS_FILE.read_text(encoding="utf-8")
    # Find OPS-NOTE entries that aren't marked resolved
    notes = re.findall(r"## OPS-NOTE.*?(?=\n## |\Z)", text, re.DOTALL)
    open_notes = [n for n in notes if "RESOLVED" not in n.upper()]
    return [{"snippet": n[:100].strip()} for n in open_notes]


def take_snapshot() -> dict:
    """Capture full fleet state as a single snapshot dict."""
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent_statuses": get_agent_statuses(),
        "host_resources": get_host_resources(),
        "goal_progress": get_goal_progress(),
        "health_score": get_health_score(),
        "open_blockers": get_open_blockers(),
    }


def append_snapshot(snapshot: dict):
    """Append snapshot to JSONL file."""
    SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SNAPSHOT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot) + "\n")


def register_schtask():
    """Register a Windows scheduled task to run every 30 minutes."""
    # Find python path
    py = sys.executable
    script = str(Path(__file__).resolve())
    task_name = "FleetStateSnapshot"
    cmd = f'schtasks /create /tn "{task_name}" /tr "\"{py}\" \"{script}\"" /sc minute /mo 30 /f'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout.strip() or result.stderr.strip())
    return result.returncode == 0


def check_jsonl():
    """Validate the snapshot JSONL file."""
    if not SNAPSHOT_FILE.exists():
        print("No snapshot file yet.")
        return False
    lines = SNAPSHOT_FILE.read_text(encoding="utf-8").strip().split("\n")
    valid = 0
    for i, line in enumerate(lines):
        try:
            entry = json.loads(line)
            # Verify all 5 required fields
            required = ["agent_statuses", "host_resources", "goal_progress", "health_score", "open_blockers"]
            missing = [f for f in required if f not in entry]
            if missing:
                print(f"  Line {i+1}: MISSING fields: {missing}")
            else:
                valid += 1
        except json.JSONDecodeError as e:
            print(f"  Line {i+1}: INVALID JSON: {e}")
    print(f"{valid}/{len(lines)} entries valid.")
    return valid == len(lines)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Fleet State Snapshot")
    ap.add_argument("--register", action="store_true", help="Register schtask for 30-min interval")
    ap.add_argument("--check", action="store_true", help="Validate JSONL integrity")
    args = ap.parse_args()

    if args.register:
        ok = register_schtask()
        print(f"Schtask registered: {ok}")
        sys.exit(0 if ok else 1)
    elif args.check:
        ok = check_jsonl()
        sys.exit(0 if ok else 1)
    else:
        snap = take_snapshot()
        append_snapshot(snap)
        print(f"Snapshot taken: {snap['ts']}")
        print(f"  agents: {len(snap['agent_statuses'])}")
        print(f"  hosts: {len(snap['host_resources'])}")
        print(f"  goal files: {len(snap['goal_progress'])}")
        print(f"  health: {snap['health_score']['score']}")
        print(f"  blockers: {len(snap['open_blockers'])}")


if __name__ == "__main__":
    main()
