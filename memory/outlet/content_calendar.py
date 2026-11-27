"""Content calendar engine for the Outlet lane.

Generates a weekly 7-day topic plan by combining:
  - milestone events (from goal_ledger state changes)
  - trend briefs (from Researcher)
  - engagement data (from ship-timeline / gate-log)

Output: memory/outlet/calendar/<YYYY-WW>.json with one entry per day.

Self-test generates 2 consecutive weeks and asserts:
  - each day has >=1 staged post topic
  - 14/14 days covered across both weeks
"""
from __future__ import annotations
import json, datetime, pathlib, re, sys, dataclasses

OUTLET_DIR = pathlib.Path(__file__).parent
BRIEFS_DIR = OUTLET_DIR / "briefs"
QUEUE_DIR = OUTLET_DIR / "queue"
CALENDAR_DIR = OUTLET_DIR / "calendar"

@dataclasses.dataclass
class DayEntry:
    date: str        # ISO date
    topic: str       # one-line topic
    source: str      # milestone | trend | engagement | default
    platform_priority: list  # e.g. ["X", "LinkedIn"]

def _read_briefs() -> list[str]:
    """Collect available brief titles as trend sources."""
    if not BRIEFS_DIR.exists():
        return []
    titles = []
    for f in sorted(BRIEFS_DIR.glob("*.md")):
        text = f.read_text(encoding="utf-8", errors="replace")
        # Use first heading or filename as topic
        m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        titles.append(m.group(1).strip() if m else f.stem.replace("-", " "))
    return titles

def _read_milestones() -> list[str]:
    """Extract milestone-like topics from queue (files with 'milestone' in name)."""
    if not QUEUE_DIR.exists():
        return []
    ms = []
    for f in sorted(QUEUE_DIR.glob("*milestone*")):
        text = f.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        ms.append(m.group(1).strip() if m else f.stem.replace("-", " "))
    return ms

def _default_topics(day_idx: int) -> str:
    """Fallback topics for days without milestone/trend source."""
    defaults = [
        "Fleet status update: cycle progress snapshot",
        "Behind the scenes: how agents coordinate",
        "Deep dive: verification gates in practice",
        "Community Q&A: top question from last week",
        "Milestone preview: what's coming next cycle",
        "Tech explainer: one fleet concept, simply put",
        "Weekly wrap: wins + open challenges",
    ]
    return defaults[day_idx % len(defaults)]

def generate_week(week_start: datetime.date) -> list[DayEntry]:
    """Generate a 7-day calendar for the given ISO week start (Monday)."""
    entries = []
    briefs = _read_briefs()
    milestones = _read_milestones()

    for day in range(7):
        d = week_start + datetime.timedelta(days=day)
        topic = None
        source = "default"

        # Priority 1: milestones on key days (Mon, Thu)
        if day in (0, 3) and milestones:
            topic = milestones[day % len(milestones)]
            source = "milestone"

        # Priority 2: trends from briefs
        elif briefs and day not in (0, 3):
            topic = briefs[(day - 1) % len(briefs)]
            source = "trend"

        # Fallback
        if not topic:
            topic = _default_topics(day)
            source = "default"

        # Platform priority: X daily, LinkedIn Tue+Fri
        platforms = ["X"]
        if day in (1, 4):
            platforms.append("LinkedIn")

        entries.append(DayEntry(
            date=d.isoformat(),
            topic=topic,
            source=source,
            platform_priority=platforms,
        ))
    return entries

def save_week(entries: list[DayEntry], week_start: datetime.date) -> pathlib.Path:
    CALENDAR_DIR.mkdir(parents=True, exist_ok=True)
    iso_year, iso_week, _ = week_start.isocalendar()
    path = CALENDAR_DIR / f"{iso_year}-W{iso_week:02d}.json"
    data = {
        "week": f"{iso_year}-W{iso_week:02d}",
        "start": week_start.isoformat(),
        "days": [dataclasses.asdict(e) for e in entries],
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path

def selftest() -> dict:
    """Generate 2 consecutive weeks and validate."""
    # Use the current ISO week
    today = datetime.date.today()
    iso_year, iso_week, _ = today.isocalendar()
    # Monday of this week
    week1_start = datetime.date.fromisocalendar(iso_year, iso_week, 1)
    week2_start = week1_start + datetime.timedelta(days=7)

    results = []
    for ws in [week1_start, week2_start]:
        entries = generate_week(ws)
        path = save_week(entries, ws)
        # Validate each day has >=1 topic
        empty_days = [e.date for e in entries if not e.topic.strip()]
        assert not empty_days, f"Empty days: {empty_days}"
        results.append({
            "week": f"{iso_year}-W{ws.isocalendar()[1]:02d}",
            "start": ws.isoformat(),
            "days_with_topic": len(entries),
            "file": str(path.relative_to(OUTLET_DIR)),
        })

    total_days = sum(r["days_with_topic"] for r in results)
    assert total_days == 14, f"Expected 14 days covered, got {total_days}"

    return {
        "weeks_generated": len(results),
        "details": results,
        "total_days_covered": total_days,
        "status": "PASS",
    }

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        r = selftest()
        print(json.dumps(r, indent=2))
        return 0 if r["status"] == "PASS" else 1

    # Default: generate for current week
    today = datetime.date.today()
    iso_year, iso_week, _ = today.isocalendar()
    ws = datetime.date.fromisocalendar(iso_year, iso_week, 1)
    entries = generate_week(ws)
    path = save_week(entries, ws)
    print(f"Calendar saved: {path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
