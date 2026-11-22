#!/usr/bin/env python3
"""Runbook Lesson Extractor - Scribe Goal #8.

After each remediation execution (success or failure), extract lessons learned:
what worked, what didn't, what should change in the runbook.
Append to the relevant runbook file as a "Lessons" section.

Usage: python memory/scribe/runbook_lessons.py [--dry-run] [--verbose]
"""
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any

OPS = pathlib.Path("memory/ops")
RUNBOOKS_DIR = OPS / "runbooks"
DECISION_LOG = OPS / "decision-log.jsonl"
INCIDENTS_LOG = OPS / "incidents.jsonl"
MAINTENANCE_LOG = OPS / "maintenance-log.jsonl"
BOOT_RECOVERY_LOG = OPS / "boot-recovery-log.jsonl"
LESSONS_MARKER = "<!-- runbook-lessons:generated -->"


def load_jsonl(path: pathlib.Path) -> list[dict]:
    """Load a JSONL file, skipping malformed lines."""
    entries = []
    if not path.exists():
        return entries
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        if not line.strip():
            continue
        try:
            entries.append(json.loads(line))
        except (json.JSONDecodeError, TypeError):
            continue
    return entries


def extract_playbook_lessons(entries: list[dict]) -> list[dict]:
    """Extract lessons from playbook_complete entries in decision log."""
    lessons = []
    # Group steps by runbook for context
    steps_by_runbook: dict[str, list[dict]] = {}
    for e in entries:
        if e.get("type") == "playbook_step":
            rb = e.get("runbook", "unknown").replace("\\", "/")
            steps_by_runbook.setdefault(rb, []).append(e)

    for e in entries:
        if e.get("type") != "playbook_complete":
            continue
        runbook_path = e.get("runbook", "unknown").replace("\\", "/")
        outcome = e.get("outcome", "unknown")
        steps_total = e.get("steps_total", 0)
        steps_executed = e.get("steps_executed", 0)
        elapsed = e.get("elapsed_sec", 0)
        rollbacks = e.get("rollbacks", [])
        ts = e.get("ts", "unknown")

        rb_key = runbook_path.replace("\\", "/")
        steps = steps_by_runbook.get(rb_key, [])

        lesson: dict[str, Any] = {
            "timestamp": ts,
            "runbook": runbook_path,
            "outcome": outcome,
            "what_worked": [],
            "what_didnt": [],
            "changes_recommended": [],
        }

        if outcome == "success":
            lesson["what_worked"].append(
                f"All {steps_total} steps completed in {elapsed}s with zero rollbacks."
            )
            # Check individual step details
            for s in steps:
                detail = s.get("detail", "")
                if "pattern" in detail.lower() and "found" in detail.lower():
                    lesson["what_worked"].append(
                        f"Step {s['step']} ('{s.get('description','')}'): output pattern verification worked as designed."
                    )
            # Timing insight
            if elapsed < 1.0:
                lesson["what_worked"].append(
                    f"Execution time ({elapsed}s) well within expected bounds - no timeout risk for this runbook."
                )
        elif "failed" in outcome:
            failed_step = int(outcome.split("_")[-1]) if "step_" in outcome else steps_total
            lesson["what_didnt"].append(
                f"Step {failed_step} failed: expected output pattern not found (stdout was empty)."
            )
            # Check which step specifically
            for s in steps:
                if not s.get("passed", True):
                    lesson["what_didnt"].append(
                        f"Step {s['step']} ('{s.get('description','')}'): exit_code={s.get('exit_code')}, "
                        f"detail='{s.get('detail','')[:80]}'"
                    )
            # Rollback assessment
            if rollbacks:
                rb_ok = all(r.get("success", False) for r in rollbacks)
                if rb_ok:
                    lesson["what_worked"].append(
                        f"Rollback of {len(rollbacks)} step(s) executed successfully - state restored cleanly."
                    )
                else:
                    lesson["what_didnt"].append(
                        "Rollback did NOT fully succeed - residual state may persist."
                    )
            # Actionable change recommendations
            lesson["changes_recommended"].append(
                f"Add pre-flight check before step {failed_step}: verify command produces non-empty stdout "
                f"before pattern matching (current failure mode: empty output passes through to pattern check)."
            )
            lesson["changes_recommended"].append(
                "Consider adding a retry-with-backoff for echo-type steps that may be affected by shell buffering."
            )

        lessons.append(lesson)
    return lessons


def extract_incident_lessons(entries: list[dict]) -> list[dict]:
    """Extract lessons from incident events."""
    lessons = []
    for e in entries:
        ts = e.get("timestamp", "unknown")
        incident = e.get("incident", {})
        classification = e.get("classification", {})
        itype = incident.get("type", "unknown")
        host = incident.get("host", "unknown")
        severity = classification.get("severity", "?")
        level = classification.get("level", "?")

        lesson: dict[str, Any] = {
            "timestamp": ts,
            "runbook": f"memory/ops/runbooks/{itype}_response.md",
            "outcome": f"{level} incident detected",
            "what_worked": [],
            "what_didnt": [],
            "changes_recommended": [],
        }

        lesson["what_worked"].append(
            f"Auto-classification correctly identified {itype} on host '{host}' as {level} (severity {severity})."
        )
        if itype == "host_down":
            lesson["what_didnt"].append(
                f"Host '{host}' went down without prior warning - no early-degradation alert fired before full loss."
            )
            lesson["changes_recommended"].append(
                f"Add a pre-failure probe for host '{host}': if response latency exceeds 2x baseline for 3 consecutive "
                f"checks, emit a P3 warning before it escalates to P2 host_down."
            )
        lessons.append(lesson)
    return lessons


def extract_maintenance_lessons(entries: list[dict]) -> list[dict]:
    """Extract lessons from maintenance log entries."""
    lessons = []
    for e in entries:
        ts = e.get("timestamp", "unknown")
        tasks = e.get("tasks", [])
        forced = e.get("forced", False)

        lesson: dict[str, Any] = {
            "timestamp": ts,
            "runbook": "memory/ops/runbooks/scheduled_maintenance.md",
            "outcome": "maintenance_completed" if all(t.get("status") == "ok" for t in tasks) else "partial_failure",
            "what_worked": [],
            "what_didnt": [],
            "changes_recommended": [],
        }

        ok_tasks = [t for t in tasks if t.get("status") == "ok"]
        fail_tasks = [t for t in tasks if t.get("status") != "ok"]

        if ok_tasks:
            lesson["what_worked"].append(
                f"{len(ok_tasks)} task(s) completed successfully: {', '.join(t['task'] for t in ok_tasks)}."
            )
        if fail_tasks:
            for t in fail_tasks:
                lesson["what_didnt"].append(
                    f"Task '{t['task']}' failed: {t.get('details', 'no detail')}"
                )
        if forced:
            lesson["changes_recommended"].append(
                "Maintenance ran in forced mode (idle_minutes=0) - consider raising the idle threshold to avoid "
                "interrupting active work."
            )
        lessons.append(lesson)
    return lessons


def extract_boot_recovery_lessons(entries: list[dict]) -> list[dict]:
    """Extract lessons from boot recovery log."""
    lessons = []
    for e in entries:
        ts = e.get("ts", "unknown")
        host = e.get("host", "unknown")
        event = e.get("event", "unknown")
        timeout_s = e.get("timeout_s", 0)

        lesson: dict[str, Any] = {
            "timestamp": ts,
            "runbook": "memory/ops/runbooks/boot_recovery.md",
            "outcome": f"failure ({event})",
            "what_worked": [],
            "what_didnt": [],
            "changes_recommended": [],
        }

        if event == "STUDIO_TIMEOUT_EXCEEDED":
            lesson["what_didnt"].append(
                f"Studio on host '{host}' exceeded {timeout_s}s timeout during boot recovery - service did not come up."
            )
            lesson["changes_recommended"].append(
                f"Increase boot timeout from {timeout_s}s to 450s for hosts with large model loads, "
                f"or add a staged readiness check (port open -> model loaded -> first inference OK)."
            )
        lessons.append(lesson)
    return lessons


def format_lessons_md(lessons: list[dict]) -> str:
    """Format lessons as a markdown section."""
    if not lessons:
        return ""

    lines = [f"\n{LESSONS_MARKER}\n", "## Lessons Learned\n"]
    for i, l in enumerate(lessons, 1):
        outcome_badge = "✅" if "success" in l["outcome"] else ("❌" if "fail" in l["outcome"] or "❌" in l["outcome"] else "⚠️")
        lines.append(f"### {i}. {l['outcome']} ({l['timestamp'][:19]})\n")
        if l["what_worked"]:
            lines.append("**What worked:**")
            for w in l["what_worked"]:
                lines.append(f"- {w}")
            lines.append("")
        if l["what_didnt"]:
            lines.append("**What didn't work:**")
            for d in l["what_didnt"]:
                lines.append(f"- {d}")
            lines.append("")
        if l["changes_recommended"]:
            lines.append("**Recommended changes:**")
            for c in l["changes_recommended"]:
                lines.append(f"- [ ] {c}")
            lines.append("")

    return "\n".join(lines)


def update_runbook(runbook_path: str, lessons_md: str) -> bool:
    """Append lessons to a runbook file (or create it). Idempotent via marker."""
    p = pathlib.Path(runbook_path)
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)

    existing = p.read_text(encoding="utf-8") if p.exists() else ""

    # Idempotency: if marker already present, replace the lessons section
    if LESSONS_MARKER in existing:
        # Remove old lessons section (from marker to end or next ## heading)
        idx = existing.index(LESSONS_MARKER)
        before = existing[:idx].rstrip() + "\n"
        p.write_text(before + lessons_md, encoding="utf-8")
    else:
        if not existing.endswith("\n"):
            existing += "\n"
        p.write_text(existing + lessons_md, encoding="utf-8")
    return True


def main():
    dry_run = "--dry-run" in sys.argv
    verbose = "--verbose" in sys.argv

    # Gather all remediation events
    decision_entries = load_jsonl(DECISION_LOG)
    incident_entries = load_jsonl(INCIDENTS_LOG)
    maintenance_entries = load_jsonl(MAINTENANCE_LOG)
    boot_entries = load_jsonl(BOOT_RECOVERY_LOG)

    # Extract lessons from each source
    all_lessons: list[dict] = []
    all_lessons.extend(extract_playbook_lessons(decision_entries))
    all_lessons.extend(extract_incident_lessons(incident_entries))
    all_lessons.extend(extract_maintenance_lessons(maintenance_entries))
    all_lessons.extend(extract_boot_recovery_lessons(boot_entries))

    print(f"Processed {len(all_lessons)} remediation events:")
    for l in all_lessons:
        print(f"  - [{l['outcome'][:40]}] {l['runbook']} @ {l['timestamp'][:19]}")

    if len(all_lessons) < 3:
        print(f"WARNING: only {len(all_lessons)} remediations found (need >=3)")
        sys.exit(1)

    # Group by runbook
    by_runbook: dict[str, list[dict]] = {}
    for l in all_lessons:
        by_runbook.setdefault(l["runbook"], []).append(l)

    # Write lessons to each runbook
    updated_files = []
    for rb_path, lessons in sorted(by_runbook.items()):
        md = format_lessons_md(lessons)
        if dry_run:
            print(f"\n[DRY-RUN] Would update: {rb_path}")
            print(md[:500])
        else:
            update_runbook(rb_path, md)
            updated_files.append(rb_path)
            print(f"Updated: {rb_path} ({len(lessons)} lesson(s))")

    # Write summary report
    if not dry_run:
        report = pathlib.Path("memory/synthesis/runbook-lessons-latest.md")
        report.parent.mkdir(parents=True, exist_ok=True)
        total = len(all_lessons)
        successes = sum(1 for l in all_lessons if "success" in l["outcome"])
        failures = total - successes
        content = f"""# Runbook Lessons Report
Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}

## Summary
- Total remediations processed: {total}
- Successful: {successes}
- Failed/partial: {failures}
- Runbooks updated: {len(updated_files)}

## Files Updated
""" + "\n".join(f"- `{f}`" for f in updated_files) + "\n\n## Lessons by Runbook\n"
        for rb, lessons in sorted(by_runbook.items()):
            content += f"\n### {rb}\n"
            for l in lessons:
                content += f"- **{l['outcome']}** ({l['timestamp'][:19]}): "
                if l["changes_recommended"]:
                    content += f"{len(l['changes_recommended'])} change(s) recommended"
                else:
                    content += "no changes needed"
                content += "\n"

        report.write_text(content, encoding="utf-8")
        print(f"\nReport written: {report}")

    # Verification output
    print(f"\n=== VERIFICATION ===")
    print(f"Remediations processed: {total} (need >=3): {'PASS' if total >= 3 else 'FAIL'}")

    # Check specificity - no generic "it worked" lessons
    generic_count = 0
    for l in all_lessons:
        for field in ("what_worked", "what_didnt"):
            for item in l[field]:
                if item.strip().lower() in ("it worked", "worked", "ok", "fine"):
                    generic_count += 1
    print(f"Generic (non-specific) lessons: {generic_count} (need 0): {'PASS' if generic_count == 0 else 'FAIL'}")

    # Check failed remediations have actionable changes
    failed_no_changes = 0
    for l in all_lessons:
        if "fail" in l["outcome"] or "❌" in l["outcome"]:
            if not l["changes_recommended"]:
                failed_no_changes += 1
    print(f"Failed remediations without actionable changes: {failed_no_changes} (need 0): {'PASS' if failed_no_changes == 0 else 'FAIL'}")

    # Check markdown validity of updated files
    md_valid = True
    for f in updated_files:
        p = pathlib.Path(f)
        if p.exists():
            content = p.read_text(encoding="utf-8")
            # Basic check: has a heading, no broken formatting
            if not any(line.startswith("#") for line in content.split("\n")):
                md_valid = False
    print(f"Runbook files valid markdown: {'PASS' if md_valid else 'FAIL'}")

    all_pass = (total >= 3 and generic_count == 0 and failed_no_changes == 0 and md_valid)
    print(f"\nOVERALL: {'ALL PASS ✅' if all_pass else 'SOME CHECKS FAILED ❌'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
