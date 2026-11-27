"""WF3: Appointment / Task Reminder Pipeline

Input : schedule.json  (list of {id, title, client, datetime_iso, lead_hours})
Output: reminders.json (items due for reminder within the next N hours) + stdout
Logic : For each upcoming item, if now >= (event_time - lead_hours), flag as DUE.
        Idempotent: items with "reminded": true are skipped.

Usage:
    python wf3_reminder_pipeline.py --selftest
    python wf3_reminder_pipeline.py --input schedule.json --output reminders.json --window 24
"""
import json, sys, argparse
from datetime import datetime, timedelta
from pathlib import Path

def load_schedule(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))

def find_due(schedule: list[dict], now: datetime, window_hours: int = 24) -> dict:
    due, skipped = [], 0
    horizon = now + timedelta(hours=window_hours)
    for item in schedule:
        if item.get("reminded"):
            skipped += 1
            continue
        event_dt = datetime.fromisoformat(item["datetime_iso"])
        remind_at = event_dt - timedelta(hours=item.get("lead_hours", 2))
        if now >= remind_at and event_dt <= horizon:
            due.append({
                "id": item["id"],
                "title": item["title"],
                "client": item.get("client", ""),
                "event_time": item["datetime_iso"],
                "hours_until": round((event_dt - now).total_seconds() / 3600, 1),
            })
    return {"generated": now.isoformat(), "due_count": len(due), "skipped_already_reminded": skipped, "reminders": due}

def selftest():
    now = datetime(2026, 11, 25, 12, 0, 0)
    schedule = [
        {"id": "A1", "title": "Dentist", "client": "Jane", "datetime_iso": "2026-11-25T14:00:00", "lead_hours": 2},
        {"id": "A2", "title": "Board mtg","client": "Acme", "datetime_iso": "2026-11-25T15:00:00", "lead_hours": 4, "reminded": True},
        {"id": "A3", "title": "Dinner",  "client": "Bob",  "datetime_iso": "2026-11-27T19:00:00", "lead_hours": 1},
    ]
    result = find_due(schedule, now, window_hours=24)
    # A1: remind_at = 12:00, now=12:00 -> DUE
    # A2: reminded=True -> skipped
    # A3: remind_at = Nov27 18:00, now < that -> not due yet
    assert result["due_count"] == 1, f"expected 1 due, got {result['due_count']}"
    assert result["reminders"][0]["id"] == "A1"
    assert result["skipped_already_reminded"] == 1
    print("WF3 selftest PASS: 3/3 assertions")
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--input", type=Path)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--window", type=int, default=24, help="look-ahead window in hours")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(0 if selftest() else 1)
    schedule = load_schedule(args.input)
    result = find_due(schedule, datetime.now(), args.window)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"WF3: {result['due_count']} reminders due, {result['skipped_already_reminded']} skipped -> {args.output}")

if __name__ == "__main__":
    main()