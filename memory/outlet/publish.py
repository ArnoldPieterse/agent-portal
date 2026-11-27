"""Outlet publish script - drains the queue with rate limiting.

Usage:
  python memory/outlet/publish.py --next        # pick oldest ready-for-human entry
  python memory/outlet/publish.py --dry-run     # show what would be posted, don't post
  python memory/outlet/publish.py --status      # show queue + rate-limit state

Requires memory/outlet/platform_credentials.json (connected: true) to actually post.
"""
import json, sys
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent  # project root
QUEUE = BASE / "memory" / "outlet" / "queue"
CREDS = BASE / "memory" / "outlet" / "platform_credentials.json"
RATE_STATE = BASE / "memory" / "outlet" / "rate_state.json"

MAX_PER_HOUR = 3
BURST_MINUTES = 20

def load_json(p, default=None):
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return default

def get_queue_entries():
    """Return sorted list of (path, metadata) for ready-for-human entries."""
    entries = []
    for f in QUEUE.glob("*.md"):
        text = f.read_text(encoding="utf-8")
        # Parse frontmatter
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                fm = {}
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        fm[k.strip()] = v.strip()
                if fm.get("status") == "ready-for-human":
                    entries.append((f, fm))
    # Sort by filename (date-prefixed = chronological)
    entries.sort(key=lambda x: x[0].name)
    return entries

def check_rate_limit():
    """Return (allowed, next_slot_str)."""
    state = load_json(RATE_STATE, {"posts": []})
    now = datetime.now()
    # Remove posts older than 1 hour
    state["posts"] = [p for p in state["posts"] if (now - p) < timedelta(hours=1)]
    if len(state["posts"]) >= MAX_PER_HOUR:
        oldest = min(state["posts"])
        next_slot = oldest + timedelta(hours=1)
        return False, next_slot.strftime("%H:%M")
    # Check burst
    recent = [p for p in state["posts"] if (now - p) < timedelta(minutes=BURST_MINUTES)]
    if len(recent) >= 1:
        last = max(recent)
        wait = last + timedelta(minutes=BURST_MINUTES)
        return False, wait.strftime("%H:%M")
    return True, None

def record_post():
    state = load_json(RATE_STATE, {"posts": []})
    now = datetime.now()
    state["posts"] = [p for p in state["posts"] if (now - p) < timedelta(hours=1)]
    state["posts"].append(now)
    RATE_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")

def mark_status(path, status):
    text = path.read_text(encoding="utf-8")
    text = text.replace("status: ready-for-human", f"status: {status}")
    path.write_text(text, encoding="utf-8")

def main():
    args = sys.argv[1:]
    
    if "--status" in args:
        entries = get_queue_entries()
        print(f"Queue: {len(entries)} ready-for-human entries")
        for f, fm in entries:
            print(f"  {f.name} (trigger: {fm.get('trigger','?')})")
        allowed, next_slot = check_rate_limit()
        print(f"Rate limit: {'OK' if allowed else f'blocked until {next_slot}'}")
        return 0
    
    dry_run = "--dry-run" in args
    
    entries = get_queue_entries()
    if not entries:
        print("Queue empty - nothing to post.")
        return 0
    
    target, fm = entries[0]
    print(f"Next in queue: {target.name}")
    print(f"  trigger: {fm.get('trigger','?')}")
    print(f"  drafted: {fm.get('drafted','?')}")
    
    if dry_run:
        print("[dry-run] Would post this entry. Not posting.")
        return 0
    
    # Check credentials
    creds = load_json(CREDS)
    if not creds or creds.get("connected") != True:
        print("BLOCKED: No connected platform. Run the Platform Connection Runbook first.")
        print(f"  Expected: {CREDS.relative_to(BASE)} with connected: true")
        return 1
    
    # Check rate limit
    allowed, next_slot = check_rate_limit()
    if not allowed:
        print(f"RATE LIMITED: Next slot at {next_slot}. Try again then.")
        return 0
    
    # TODO: actual platform API call (Bluesky/Mastodon/X)
    # For now: simulate success + mark published
    print(f"Posting to {creds.get('handle','?')} on {creds.get('platform','?')}...")
    print("(simulated - real API integration pending platform selection)")
    
    record_post()
    mark_status(target, "published")
    print(f"Marked as published: {target.name}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
