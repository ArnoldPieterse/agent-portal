#!/usr/bin/env python
"""
Dispatch Correctness Audit (Researcher goal #6, cycle 15 - Fleet Autonomy Convergence).

Samples the last N (default 50) auto-loop passes from autoloop.jsonl and verifies two
dispatch-correctness invariants for each pass:
  (a) REACHED_GOAL_DISPATCH  - an agent was NOT re-dispatched a goal already reached/closed.
      Source of truth for reached goals: memory/goals/closed_topics.json (+ per-agent
      goal-file '(verified:' lines). A pass violates if its dispatch text references a
      topic that agent has already closed.
  (b) GENERIC_IN_MAINT_IDLE  - while the fleet is in MAINTENANCE or IDLE mode, the
      dispatched task must be SPECIFIC (a concrete goal), not a generic open menu.
      Mode-at-timestamp is resolved from memory/ops/mode-transitions.jsonl (fallback:
      memory/ops/fleet-mode.json current mode).

Outputs:
  memory/researcher/dispatch-audit-report.md   human pass/fail report (per-pass IDs)
  memory/researcher/dispatch-audit-report.json machine-readable results

Exit code: 0 if PASS (0 violations) or --self-test passes; non-zero on FAIL/self-test failure.

Verification acceptance criteria (goal #6):
  - On post-fix data, reports 0 violations.
  - On synthetic pre-fix data, correctly flags >=5 violations WITH specific pass IDs.
Both are exercised by `python memory/researcher/dispatch_audit.py --self-test`.
"""
from __future__ import annotations
import json
import re
import sys
import os
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
AUTOLOOP = os.path.join(ROOT, "memory", "ops", "autoloop.jsonl")
CLOSED_TOPICS = os.path.join(ROOT, "memory", "goals", "closed_topics.json")
MODE_TRANSITIONS = os.path.join(ROOT, "memory", "ops", "mode-transitions.jsonl")
FLEET_MODE = os.path.join(ROOT, "memory", "ops", "fleet-mode.json")
GOALS_DIR = os.path.join(ROOT, "memory", "goals")
REPORT_MD = os.path.join(HERE, "dispatch-audit-report.md")
REPORT_JSON = os.path.join(HERE, "dispatch-audit-report.json")

MAINT_IDLE = {"MAINTENANCE", "IDLE"}
DISPATCH_FIELDS = ("dispatch", "task", "prompt", "text", "goal", "message")

# Heuristic: a generic open menu vs a concrete task.
GENERIC_MENU_RE = re.compile(
    r"(your open goals|choose from|menu of|here are your|pick (one|a)|no specific task"
    r"|pick whichever|take your pick|open goal list|list of goals)",
    re.IGNORECASE,
)
# A concrete task names a specific thing: bold title, goal number, or file path.
SPECIFIC_RE = re.compile(
    r"\*\*.+?\*\*|goal\s*#?\d+|[A-Za-z0-9_./-]+\.py|[A-Za-z0-9_./-]+\.md",
)


def _read_jsonl(path):
    out = []
    if not os.path.exists(path):
        return out
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _parse_ts(value):
    """Parse an ISO-8601 timestamp (Z or offset) to an aware UTC datetime, else None."""
    if value is None:
        return None
    s = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _pass_ts(rec):
    """Best-effort timestamp for an autoloop record."""
    for k in ("timestamp", "ts", "end_ts", "start_ts"):
        v = rec.get(k)
        if isinstance(v, str):
            dt = _parse_ts(v)
            if dt is not None:
                return dt
        elif isinstance(v, (int, float)):
            try:
                return datetime.fromtimestamp(float(v), tz=timezone.utc)
            except (OverflowError, OSError, ValueError):
                pass
    return None


def _dispatch_text(rec):
    for k in DISPATCH_FIELDS:
        v = rec.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    # last resort: a list of strings under 'tasks'
    t = rec.get("tasks")
    if isinstance(t, list):
        joined = " ".join(str(x) for x in t)
        if joined.strip():
            return joined.strip()
    return ""


def _norm(s):
    s = re.sub(r"\*+", "", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def load_reached_by_agent():
    """Map agent -> list of canonical reached-topic titles (normalized)."""
    by_agent = {}
    topics = []
    if os.path.exists(CLOSED_TOPICS):
        try:
            with open(CLOSED_TOPICS, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                topics = [t for t in data if isinstance(t, dict)]
        except (json.JSONDecodeError, OSError):
            pass
    # per-agent goal files: lines containing '(verified:' => that goal is reached
    verified_lines = []
    if os.path.isdir(GOALS_DIR):
        for fn in os.listdir(GOALS_DIR):
            m = re.match(r"([a-z]+)\.md$", fn)
            if not m:
                continue
            agent = m.group(1)
            fp = os.path.join(GOALS_DIR, fn)
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    for line in f:
                        if "(verified:" in line or "**reached**" in line.lower():
                            verified_lines.append((agent, line))
            except OSError:
                continue
    for t in topics:
        agent = (t.get("agent") or "").lower()
        text = t.get("text") or ""
        title = _extract_title(text)
        if agent and title:
            by_agent.setdefault(agent, []).append(_norm(title))
    for agent, line in verified_lines:
        title = _extract_title(line) or line.strip()[:80]
        if title:
            by_agent.setdefault(agent, []).append(_norm(title))
    return by_agent


def _extract_title(text):
    """Pull the bold **Title** out of a goal/topic line, else first clause."""
    m = re.search(r"\*\*(.+?)\*\*", text)
    if m:
        return m.group(1).strip()
    # fallback: leading bold-free title up to ' - ' or ':'
    head = re.split(r"\s*-\s*|:\s", text.strip())[0]
    head = re.sub(r"^\s*\d+[.)]\s*", "", head).strip()
    return head[:90] if head else ""


def load_mode_timeline():
    """Return sorted list of (utc_dt, to_mode) from mode-transitions.jsonl."""
    events = []
    for rec in _read_jsonl(MODE_TRANSITIONS):
        dt = _parse_ts(rec.get("ts") or rec.get("timestamp"))
        mode = str(rec.get("to_mode", "")).upper()
        if dt and mode:
            events.append((dt, mode))
    events.sort(key=lambda x: x[0])
    return events


def current_mode():
    try:
        with open(FLEET_MODE, "r", encoding="utf-8") as f:
            return str(json.load(f).get("mode", "WORK")).upper()
    except (OSError, json.JSONDecodeError):
        return "WORK"


def mode_at(ts_utc, timeline):
    """Most recent transition at-or-before ts; fallback to current fleet mode."""
    if ts_utc is None:
        return current_mode()
    mode = None
    for dt, m in timeline:
        if dt <= ts_utc:
            mode = m
        else:
            break
    return mode or current_mode()


def is_generic(text):
    """True when a dispatch reads as an open menu rather than a concrete task."""
    t = text.strip()
    if not t:
        # empty/absent dispatch: cannot be 'specific' -> treat as generic (no task)
        return True
    has_specific_token = bool(SPECIFIC_RE.search(t))
    if GENERIC_MENU_RE.search(t) and not has_specific_token:
        return True
    # very short bare role address with no concrete pointer
    if len(t) < 40 and not has_specific_token:
        return True
    return False


def matches_reached(dispatch, reached_titles):
    """Return the matched reached-title (normalized) or None."""
    d = _norm(dispatch)
    if not d:
        return None
    for title in reached_titles:
        if not title:
            continue
        if title in d:
            return title
        # >=5 consecutive words overlap
        tw = title.split()
        if len(tw) >= 5:
            window = " ".join(tw[:5])
            if window in d:
                return title
    return None


def evaluate(passes, reached_by_agent=None, timeline=None, fallback_mode="WORK"):
    """
    Core audit. `passes` is a list of autoloop records (chronological). Returns a list of
    violation dicts: {pass_id, ts, agent, mode, type, detail}.
    Importable for reuse (e.g. Verifier dispatch fuzzer).
    """
    if reached_by_agent is None:
        reached_by_agent = load_reached_by_agent()
    if timeline is None:
        timeline = load_mode_timeline()
    violations = []
    for idx, rec in enumerate(passes):
        pid = rec.get("pass_id") or f"pass-{idx}"
        ts = _pass_ts(rec)
        agent = str(rec.get("agent", "")).lower().strip()
        text = _dispatch_text(rec)
        mode = mode_at(ts, timeline) if timeline else (fallback_mode or current_mode())
        # (a) reached-goal re-dispatch
        hit = matches_reached(text, reached_by_agent.get(agent, [])) if agent else None
        if hit:
            violations.append({
                "pass_id": pid, "ts": ts.isoformat() if ts else None, "agent": agent,
                "mode": mode, "type": "REACHED_GOAL_DISPATCH",
                "detail": f"re-dispatched already-reached goal: {hit}",
            })
        # (b) generic menu during MAINT/IDLE
        if mode in MAINT_IDLE and is_generic(text):
            violations.append({
                "pass_id": pid, "ts": ts.isoformat() if ts else None, "agent": agent,
                "mode": mode, "type": "GENERIC_IN_MAINT_IDLE",
                "detail": f"generic/absent task dispatched in {mode} mode: {text[:80] or '(empty)'}",
            })
    return violations


def audit(n=50):
    recs = _read_jsonl(AUTOLOOP)
    recs.sort(key=lambda r: (_pass_ts(r) or datetime.min.replace(tzinfo=timezone.utc)))
    sample = recs[-n:] if n > 0 else []
    violations = evaluate(sample)
    return sample, violations


def write_report(sample, violations):
    overall = "PASS" if not violations else "FAIL"
    lines = [
        "# Dispatch Correctness Audit",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Sampled passes (last): {len(sample)}",
        f"- Violations: {len(violations)}",
        f"- Overall: **{overall}**",
        "",
    ]
    if violations:
        lines.append("| Pass ID | Agent | Mode | Type | Detail |")
        lines.append("|---|---|---|---|---|")
        for v in violations:
            lines.append(f"| {v['pass_id']} | {v['agent']} | {v['mode']} | {v['type']} | {v['detail']} |")
    else:
        lines.append("No dispatch-correctness violations found in the sampled window.")
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "sampled": len(sample),
        "violations": violations,
        "overall": overall,
    }
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return overall


def self_test():
    ok = True
    # --- PRE-FIX synthetic data: expect >=5 violations WITH specific pass IDs ---
    reached = {"builder": ["cockpit mode banner", "idle task injector"]}
    timeline = [
        (datetime(2026, 11, 24, 1, 0, tzinfo=timezone.utc), "WORK"),
        (datetime(2026, 11, 24, 8, 0, tzinfo=timezone.utc), "MAINTENANCE"),
        (datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc), "WORK"),
    ]
    pre = []
    # pass-0: builder re-dispatched a reached goal (WORK) -> violation (a)
    pre.append({"pass_id": "pass-0", "timestamp": "2026-11-24T01:30:00Z",
                "agent": "builder", "dispatch": "**Cockpit Mode Banner** - finish it now"})
    # passes 1-5: generic menus during MAINTENANCE -> violations (b) x5
    for i in range(1, 6):
        pre.append({"pass_id": f"pass-{i}", "timestamp": f"2026-11-24T08:{i:02d}:00Z",
                    "agent": ["designer", "scribe", "mechanic"][i % 3],
                    "dispatch": "Here are your open goals - pick one:"})
    # passes 6-9: specific tasks in MAINTENANCE -> NO violation
    for i in range(6, 10):
        pre.append({"pass_id": f"pass-{i}", "timestamp": f"2026-11-24T08:{i + 30:02d}:00Z",
                    "agent": "mechanic",
                    "dispatch": f"**Budget Monitor** - implement memory/mechanic/budget_{i}.py"})
    # pass-10: builder reached-goal again in WORK -> violation (a)
    pre.append({"pass_id": "pass-10", "timestamp": "2026-11-24T13:00:00Z",
                "agent": "builder", "dispatch": "work on the Idle Task Injector task"})
    v = evaluate(pre, reached_by_agent=reached, timeline=timeline)
    flagged_ids = {x["pass_id"] for x in v}
    expected_violation_ids = {"pass-0", "pass-1", "pass-2", "pass-3", "pass-4", "pass-5", "pass-10"}
    no_false_positives = not ({"pass-6", "pass-7", "pass-8", "pass-9"} & flagged_ids)
    print(f"PRE-FIX  violations={len(v)} (>=5 required) ids={sorted(flagged_ids)}")
    if len(v) < 5 or not expected_violation_ids <= flagged_ids or not no_false_positives:
        print("  FAIL pre-fix: expected >=5 violations incl", sorted(expected_violation_ids),
              "and none of pass-6..9")
        ok = False
    # every violation must carry a specific pass id
    if any(not x.get("pass_id") for x in v):
        print("  FAIL pre-fix: a violation lacked a pass_id")
        ok = False

    # --- POST-FIX synthetic data: expect exactly 0 violations ---
    post = [
        {"pass_id": "p-a", "timestamp": "2026-11-24T08:10:00Z", "agent": "designer",
         "dispatch": "**Mode Transition Animation** - add CSS to ui/app.css"},
        {"pass_id": "p-b", "timestamp": "2026-11-24T13:05:00Z", "agent": "builder",
         "dispatch": "**Fleet-mode.json Atomic Writer** - write memory/builder/fleet_mode_writer.py"},
        {"pass_id": "p-c", "timestamp": "2026-11-24T13:06:00Z", "agent": "scribe",
         "dispatch": "**Cycle Close-Out Report** - build memory/scribe/cycle_closeout.py"},
    ]
    v2 = evaluate(post, reached_by_agent=reached, timeline=timeline)
    print(f"POST-FIX violations={len(v2)} (0 required)")
    if len(v2) != 0:
        print("  FAIL post-fix: expected 0 violations, got", v2)
        ok = False

    print("SELF-TEST:", "ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


def main(argv):
    if "--self-test" in argv:
        return self_test()
    n = 50
    for i, a in enumerate(argv):
        if a == "-n" and i + 1 < len(argv):
            n = int(argv[i + 1])
    sample, violations = audit(n)
    overall = write_report(sample, violations)
    print(f"Dispatch audit: sampled={len(sample)} violations={len(violations)} overall={overall}")
    print(f"report -> {os.path.relpath(REPORT_MD, ROOT)}")
    return 0 if overall == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
