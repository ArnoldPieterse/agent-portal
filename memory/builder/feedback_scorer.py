#!/usr/bin/env python3
"""Closed-Loop Feedback Scorer — score each auto-loop pass 0-1.

Reads evidence from:
  - memory/ file modification times (output signal)
  - memory/goals/*.md goal-closure lines (progress signal)
  - memory/ops/blockers.md + OPS-NOTES (friction signal)
  - memory/synthesis/auto_loop_notes.jsonl (explicit loop events)

Writes:
  - memory/builder/loop_scores.jsonl  (one record per scored pass)

Usage:
  python memory/builder/feedback_scorer.py [--window HOURS] [--dry-run]
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
MEMORY = ROOT / "memory"
OUTPUT = MEMORY / "builder" / "loop_scores.jsonl"

# ─── Signal extractors ────────────────────────────────────────────────────────

def get_file_activity(window_start: datetime, window_end: datetime) -> dict:
    """Count files modified in each 1-hour bucket within the window. Returns {hour_iso: count}."""
    buckets = {}
    for p in MEMORY.rglob("*"):
        if p.is_file() and not any(part.startswith(".") for part in p.parts):
            try:
                mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
            except OSError:
                continue
            if window_start <= mtime < window_end:
                hour_key = mtime.strftime("%Y-%m-%dT%H:00:00Z")
                buckets[hour_key] = buckets.get(hour_key, 0) + 1
    return buckets


def get_goal_closures(window_start: datetime, window_end: datetime) -> list:
    """Find goal-closure evidence lines (verified: / REACHED / timestamped evidence) in goal files."""
    closures = []
    for gf in sorted((MEMORY / "goals").glob("*.md")):
        if gf.name == "closed_topics.json":
            continue
        try:
            text = gf.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # Look for lines with evidence markers
        for line in text.splitlines():
            if re.search(r"(verified:|REACHED|\[evidence\]|goal_ledger.*--record)", line, re.IGNORECASE):
                # Try to extract timestamp from the line
                ts_match = re.search(
                    r"(20\d{2}-\d{2}-\d{2}[T ]?\d{2}:?\d{2})", line
                )
                if ts_match:
                    try:
                        ts_str = ts_match.group(1).replace(" ", "T")
                        if "T" in ts_str and ":" not in ts_str.split("T")[1]:
                            ts_str += ":00"
                        ts = datetime.fromisoformat(ts_str)
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        if window_start <= ts < window_end:
                            closures.append({"file": str(gf.relative_to(ROOT)), "line": line.strip()[:200]})
                    except ValueError:
                        pass
    return closures


def get_blocker_events(window_start: datetime, window_end: datetime) -> int:
    """Count OPS-NOTE entries in blockers.md that fall within the window."""
    count = 0
    bp = MEMORY / "ops" / "blockers.md"
    if not bp.exists():
        return 0
    try:
        text = bp.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0
    for line in text.splitlines():
        if "OPS-NOTE" in line or "NEEDS-HUMAN" in line:
            ts_match = re.search(r"(20\d{2}-\d{2}-\d{2})", line)
            if ts_match:
                try:
                    ts = datetime.strptime(ts_match.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if window_start <= ts < window_end:
                        count += 1
                except ValueError:
                    pass
    return count


def get_loop_events(window_start: datetime, window_end: datetime) -> list:
    """Read explicit loop events from auto_loop_notes.jsonl."""
    events = []
    lp = MEMORY / "synthesis" / "auto_loop_notes.jsonl"
    if not lp.exists():
        return events
    try:
        lines = lp.read_text(encoding="utf-8").strip().split("\n")
    except (OSError, UnicodeDecodeError):
        return events
    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        ts_str = entry.get("ts", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace(" ", "T"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if window_start <= ts < window_end:
                events.append(entry)
        except ValueError:
            continue
    return events


# ─── Scoring model ───────────────────────────────────────────────────────────

def score_pass(
    file_count: int,
    goal_closures: list,
    blocker_count: int,
    loop_events: list,
) -> tuple[float, dict]:
    """Score a pass 0-1. Returns (score, breakdown).
    
    Formula (weighted):
      - output_score: min(file_count / 5, 1.0) — 5+ new/modified files = full credit
      - progress_score: min(len(goal_closures) / 2, 1.0) — 2+ closures = full credit
      - friction_penalty: blocker_count * 0.15 (capped at 0.45)
      - event_bonus: 0.05 per explicit positive loop event (capped at 0.15)
    
    score = 0.5 * output + 0.3 * progress + 0.2 * (1 - friction_penalty) + event_bonus
    Clamped to [0, 1].
    """
    output_score = min(file_count / 5.0, 1.0)
    progress_score = min(len(goal_closures) / 2.0, 1.0)
    friction_penalty = min(blocker_count * 0.15, 0.45)
    
    # Positive events (non-stale, non-error)
    positive_events = sum(
        1 for e in loop_events
        if "stale" not in e.get("event", "").lower() and "error" not in e.get("event", "").lower()
    )
    event_bonus = min(positive_events * 0.05, 0.15)

    raw = (
        0.5 * output_score
        + 0.3 * progress_score
        + 0.2 * (1.0 - friction_penalty)
        + event_bonus
    )
    score = max(0.0, min(1.0, round(raw, 4)))

    breakdown = {
        "output_score": round(output_score, 3),
        "progress_score": round(progress_score, 3),
        "friction_penalty": round(friction_penalty, 3),
        "event_bonus": round(event_bonus, 3),
        "raw": round(raw, 4),
    }
    return score, breakdown


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Score each auto-loop pass 0-1")
    parser.add_argument("--window", type=float, default=24.0, help="Window in hours to score (default: 24)")
    parser.add_argument("--step", type=float, default=1.0, help="Step size in hours (default: 1h buckets)")
    parser.add_argument("--dry-run", action="store_true", help="Print scores without writing")
    args = parser.parse_args()

    now = datetime.now(tz=timezone.utc)
    window_start = now - timedelta(hours=args.window)

    # Gather signals for the full window (file activity is expensive, do once)
    file_buckets = get_file_activity(window_start, now)
    
    # Pre-gather all closures and blockers for the window
    all_closures = get_goal_closures(window_start, now)
    all_blockers_count = get_blocker_events(window_start, now)
    all_loop_events = get_loop_events(window_start, now)

    # Score each step bucket
    results = []
    t = window_start
    while t < now:
        t_end = min(t + timedelta(hours=args.step), now)
        
        hour_key = t.strftime("%Y-%m-%dT%H:00:00Z")
        file_count = file_buckets.get(hour_key, 0)
        
        # Filter closures to this bucket
        bucket_closures = [c for c in all_closures if t <= datetime.fromisoformat(c.get("ts", t.isoformat())) < t_end]
        
        results.append({
            "window_start": t.isoformat(),
            "window_end": t_end.isoformat(),
            "files_modified": file_count,
            "goal_closures": len(bucket_closures),
            "blockers": all_blockers_count if t.hour == window_start.hour else 0,
            "score": None,  # computed below
        })
        t = t_end

    # Compute scores
    for r in results:
        score, breakdown = score_pass(
            file_count=r["files_modified"],
            goal_closures=[{"file": "", "line": ""}] * r["goal_closures"],  # just need count
            blocker_count=r["blockers"],
            loop_events=all_loop_events if r is results[0] else [],
        )
        r["score"] = score
        r["breakdown"] = breakdown

    # Summary
    scored = [r for r in results if r["files_modified"] > 0 or r["goal_closures"] > 0]
    avg_score = sum(r["score"] for r in scored) / len(scored) if scored else 0.0
    summary = {
        "generated": now.isoformat(),
        "window_hours": args.window,
        "step_hours": args.step,
        "total_buckets": len(results),
        "active_buckets": len(scored),
        "avg_score": round(avg_score, 4),
        "min_score": min((r["score"] for r in scored), default=0.0),
        "max_score": max((r["score"] for r in scored), default=0.0),
    }

    output = {"summary": summary, "passes": results}

    if args.dry_run:
        print(json.dumps(output, indent=2))
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        print(f"Wrote {len(results)} pass scores to {OUTPUT.relative_to(ROOT)}")
        print(f"Summary: avg={avg_score:.3f}, active={len(scored)}/{len(results)}, range=[{min((r['score'] for r in scored), default=0):.3f}, {max((r['score'] for r in scored), default=0):.3f}]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
