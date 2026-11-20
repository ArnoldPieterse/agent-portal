#!/usr/bin/env python3
"""blocker_triage.py - Parse memory/ops/blockers.md, classify each entry,
suggest resolution path. Write triage report to memory/ops/blocker-triage-YYYY-MM-DD.md.

Usage:
    python memory/researcher/blocker_triage.py          # run triage + write report
    python memory/researcher/blocker_triage.py --test   # self-test with synthetic entry
"""
import re, sys, json, datetime, pathlib
from collections import Counter

BLOCKERS_PATH = pathlib.Path("memory/ops/blockers.md")
REPORT_DIR  = pathlib.Path("memory/ops")

# ── Known blocker classes (keyword -> class label) ──────────────────────────────
KNOWN_CLASSES = {
    "sandbox-egress": [
        "WinError 10013", "egress block", "egress wall",
        "not a literal the sandbox can check", "network destination is not a literal",
        "cannot reach", "no LAN path",
    ],
    "elev-helper-down": [
        "exit 5", "TASK_CREATE_FAIL", "helper down",
        "Class not registered", "COM unavailable",
        "helper ABSENT", "file-not-found",
    ],
    "file-absent": [
        "0-byte placeholder", "0 bytes in sandbox",
        "canonical lives on White", "st_size.*-> 0",
    ],
    "smb-auth": [
        "SMB AUTH", "Access is denied", "System error 5",
        "net use", "empty SMB password",
    ],
    "browser-unavailable": [
        "no browser binary", "Chrome.*exit 3", "CHROME_EXIT=3",
        "DOM output", "headless browser",
    ],
    "model-unreachable": [
        "model unreachable", "not_loaded",
    ],
}

# ── Resolution path per class ───────────────────────────────────────────────────
RESOLUTION_PATHS = {
    "sandbox-egress": (
        "Run from a non-sandbox seat (White ops terminal / RDP). "
        "The sandbox cannot reach localhost or LAN targets. Do NOT re-probe from sandbox."
    ),
    "elev-helper-down": (
        "Repair the elevation helper service on this host, OR run the target command "
        "directly from a non-sandbox admin seat. Check: python elev.py whoami -> exit 0."
    ),
    "file-absent": (
        "Sync the canonical file to the sandbox (via mirror), OR run the operation "
        "directly on the host where the file exists (White). Do NOT re-probe from sandbox."
    ),
    "smb-auth": (
        "Fix SMB credentials in the mirror config, then confirm net use succeeds from "
        "the persistent White host. Run parse_mirror_events.py per runbook after data accumulates."
    ),
    "browser-unavailable": (
        "Close on static structural verification (per browser-acceptance-workaround.md). "
        "Full browser QA deferred to human's own browser at http://localhost:8099/."
    ),
    "model-unreachable": (
        "Check if the seat is running in auto-loop status. If still open after 2 passes, "
        "escalate to Orchestrator for model reload on that host."
    ),
    "new/unclassified": (
        "NEW BLOCKER - no known class matched. Read the entry manually and determine: "
        "(a) is it a recurring sandbox limitation? (b) is there an unblock step? "
        "Add a new entry to KNOWN_CLASSES in blocker_triage.py once classified."
    ),
}

STATUS_KEYWORDS = ["NEEDS-HUMAN", "RESOLVED", "RECONCILED"]
DATE_RE   = re.compile(r'(\d{4}-\d{2}-\d{2})')
AGENT_RE  = re.compile(r'\b(Orchestrator|Researcher|Builder|Verifier|Designer|Archivist|Mechanic|Scribe)\b', re.I)


def _parse_header(line: str):
    """Extract (status, date, title) from a ## header line.
    Handles all observed formats:
      ## [NEEDS-HUMAN 2026-11-20] Title here
      ## [RECONCILED 2026-11-19 Orchestrator] Title here
      ## [RESOLVED 2026-11-17 ~14:07] Title here
      ## Mirror-revert data collection (Researcher goal #3) [NEEDS-HUMAN]
      ## 2026-11-18 RESOLUTIONS (unsloth-assist, White seat)
      ## NEEDS-HUMAN: Portal auto-restart failed (auto_restart.py)
    """
    # Find status keyword anywhere in the line
    status = None
    for kw in STATUS_KEYWORDS:
        if kw in line.upper():
            status = kw
            break
    if status is None:
        return None  # not a recognised blocker header
    dm = DATE_RE.search(line)
    date = dm.group(1) if dm else ""
    # Title: everything after the first ] or after '## ', whichever is later
    title = line[3:].strip()            # drop '## '
    if ']' in title:
        after = title.split(']', 1)[1].strip()
        if after:                       # normal case: [STATUS ...] Title here
            title = after
        else:                           # [NEEDS-HUMAN] at end: use text before the bracket
            title = title.split('[', 1)[0].strip() or status
    elif ':' in title and status == "NEEDS-HUMAN":
        # e.g. 'NEEDS-HUMAN: Portal auto-restart failed'
        title = title.split(':', 1)[1].strip()
    return status, date, title

# ────────────────────────────────────────────────────────────────────────────────

def parse_entries(text: str):
    """Split blockers.md into individual entries keyed by their ## header."""
    entries = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            parsed = _parse_header(line)
            if parsed:
                status, date, title = parsed
                body_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith("## "):
                    body_lines.append(lines[i])
                    i += 1
                body = "\n".join(body_lines)
                entries.append({"status": status, "date": date, "title": title,
                                "body": body, "full": line + "\n" + body})
                continue
        i += 1
    return entries


def infer_class(entry: dict) -> str:
    """Return the known class label for an entry, or 'new/unclassified'."""
    text = (entry["title"] + "\n" + entry["body"]).lower()
    # Explicit **Class:** line takes priority
    m = re.search(r'\*\*class:\*\*\s*(.+)', text)
    if m:
        explicit = m.group(1).strip().lower()
        for cls, kws in KNOWN_CLASSES.items():
            if any(k.lower() in explicit for k in kws):
                return cls
    # Keyword scan over full entry
    for cls, kws in KNOWN_CLASSES.items():
        if any(k.lower() in text for k in kws):
            return cls
    return "new/unclassified"


def classify_entry(entry: dict) -> str:
    """Return: 'known-class' | 'resolved' | 'escalation-needed'"""
    status = entry["status"].upper()
    if status in ("RESOLVED", "RECONCILED"):
        return "resolved"
    cls = infer_class(entry)
    if cls == "new/unclassified":
        return "escalation-needed"
    return "known-class"


def extract_agent(entry: dict) -> str:
    m = AGENT_RE.search(entry["title"] + " \n" + entry["body"][:200])
    return m.group(1).lower() if m else "unknown"


def triage(entries):
    results = []
    for e in entries:
        cls   = infer_class(e)
        label = classify_entry(e)
        agent = extract_agent(e)
        suggestion = RESOLUTION_PATHS.get(cls, RESOLUTION_PATHS["new/unclassified"])
        results.append({**e, "class": cls, "label": label,
                        "agent": agent, "suggestion": suggestion})
    return results


def write_report(results):
    today = datetime.date.today().isoformat()
    report_path = REPORT_DIR / f"blocker-triage-{today}.md"

    open_n   = [r for r in results if r["label"] != "resolved"]
    resolved = [r for r in results if r["label"] == "resolved"]
    new_     = [r for r in results if r["label"] == "escalation-needed"]

    lines = [
        f"# Blocker Triage Report — {today}",
        f"Generated by `blocker_triage.py` at {datetime.datetime.now().isoformat(timespec='seconds')}",
        f"Source: `{BLOCKERS_PATH}`",
        "",
        "## Summary",
        f"- Total entries parsed: **{len(results)}**",
        f"- Open (NEEDS-HUMAN): **{len(open_n)}**",
        f"  - Known-class: {sum(1 for r in open_n if r['label']=='known-class')}",
        f"  - Escalation-needed (new/unclassified): {len(new_)}",
        f"- Resolved / Reconciled: **{len(resolved)}**",
        "",
    ]

    if new_:
        lines += ["## ⚠️ NEW / ESCALATION NEEDED", ""]
        for r in new_:
            lines += [
                f"### {r['title']}",
                f"- Class: **{r['class']}** (no known class matched)",
                f"- Agent: {r['agent']}",
                f"- Suggestion: {r['suggestion']}",
                "",
            ]

    lines += ["## Open Blockers (NEEDS-HUMAN)", ""]
    for r in open_n:
        lines += [
            f"### {r['title']}",
            f"- Class: **{r['class']}**",
            f"- Agent: {r['agent']}",
            f"- Date: {r['date'] or 'undated'}",
            f"- Suggestion: {r['suggestion']}",
            "",
        ]

    if resolved:
        lines += ["## Resolved / Reconciled (informational)", ""]
        for r in resolved:
            lines += [f"- **{r['title']}** — class: {r['class']}"]
        lines.append("")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


# ── Self-test ───────────────────────────────────────────────────────────────────
TEST_ENTRY = """## [NEEDS-HUMAN 2099-01-01] TestAgent: Synthetic new blocker class XYZ
**Class:** totally novel failure mode not in any known class
**Blocks:** test goal #99.
**Unblock:** do something completely different.
"""

def run_test():
    """Self-test: parse real file + inject synthetic entry; verify both detected."""
    print("[TEST] Parsing blockers.md ...")
    text = BLOCKERS_PATH.read_text(encoding="utf-8", errors="replace")
    entries_real = parse_entries(text)
    print(f"  Found {len(entries_real)} real entries.")

    # Inject synthetic
    entries_all = parse_entries(text + "\n" + TEST_ENTRY)
    print(f"  With synthetic: {len(entries_all)} entries (expected +1).")
    assert len(entries_all) == len(entries_real) + 1, "Synthetic entry not detected!"

    results = triage(entries_all)
    synthetic = [r for r in results if "XYZ" in r["title"]]
    assert len(synthetic) == 1, "Synthetic entry missing from results."
    assert synthetic[0]["label"] == "escalation-needed", \
        f"Expected escalation-needed, got {synthetic[0]['label']}"
    assert synthetic[0]["class"] == "new/unclassified"

    # Verify a known-class entry is classified correctly
    egress = [r for r in results if "egress" in r["title"].lower()
              or "WinError 10013" in r.get("body","")]
    if egress:
        assert all(r["class"] == "sandbox-egress" or r["label"]=="resolved" for r in egress), \
            f"Egress entry misclassified: {[r['class'] for r in egress]}"
        print(f"  Egress entries correctly classified as 'sandbox-egress'.")

    # Write test report (don't overwrite real one)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    test_report = REPORT_DIR / "blocker-triage-test.md"
    lines = [f"# Blocker Triage SELF-TEST — {datetime.date.today().isoformat()}",
             f"Entries parsed: {len(results)} (incl. 1 synthetic)",
             f"Synthetic detected: PASS (escalation-needed / new/unclassified)"]
    if egress:
        lines.append(f"Known-class check (egress): PASS ({len(egress)} entries)")
    test_report.write_text("\n".join(lines), encoding="utf-8")
    print(f"[TEST] All checks passed. Report: {test_report}")
    return True


def main():
    if "--test" in sys.argv:
        ok = run_test()
        sys.exit(0 if ok else 1)

    text = BLOCKERS_PATH.read_text(encoding="utf-8", errors="replace")
    entries = parse_entries(text)
    results = triage(entries)
    report_path = write_report(results)
    open_n   = sum(1 for r in results if r["label"] != "resolved")
    resolved = sum(1 for r in results if r["label"] == "resolved")
    new_     = sum(1 for r in results if r["label"] == "escalation-needed")
    print(f"Triage complete: {len(results)} entries | open={open_n} resolved={resolved} new={new_}")
    print(f"Report written: {report_path}")

if __name__ == "__main__":
    main()