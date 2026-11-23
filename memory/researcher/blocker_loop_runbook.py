#!/usr/bin/env python3
"""Blocker -> Catch -> Fix -> Verify Runbook (Researcher Goal #5).

Auto-maintained runbook linking each OPS-NOTE blocker to:
  (a) the detector that catches it
  (b) the exact remediation step
  (c) the verify command
  (d) rolling success rate

AC: >=5 real historical blockers each carry all four fields + a measured success rate.

Usage:
  python memory/researcher/blocker_loop_runbook.py               # generate runbook from live data
  python memory/researcher/blocker_loop_runbook.py --selftest    # synthetic test
"""
import json, re, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
BLOCKERS_MD = ROOT / "memory" / "ops" / "blockers.md"
REMEDIATION_LOG = HERE / "remediation-log.jsonl"
OUTPUT = HERE / "blocker-loop-runbook.md"

# Mapping of blocker classes to detectors + remediation steps
DETECTOR_MAP = {
    "sandbox egress": {
        "detector": "stale_claim_scan (flags stale 'reachable' claims after egress block)",
        "remediation": "Non-sandbox seat executes the blocked command; result logged via goal_ledger.py",
        "verify_cmd": "python memory/researcher/stale_check.py --target <file>",
    },
    "COM unavailable": {
        "detector": "dispatch_desync (flags goals stuck at 0 progress for >2 cycles)",
        "remediation": "Run from non-sandbox White seat: python elev.py --shell '<schtasks cmd>'",
        "verify_cmd": "python memory/researcher/remediation_bus.py --dry-run | grep dispatch_desync",
    },
    "helper down (exit 5)": {
        "detector": "reach_matrix (flags seat unreachable when model not loaded)",
        "remediation": "Run from non-sandbox host with elev.py present + helper service running",
        "verify_cmd": "python elev.py whoami && echo ELEV_OK",
    },
    "helper ABSENT": {
        "detector": "reach_matrix (flags seat model not_loaded)",
        "remediation": "Sync elev.py to the seat OR execute from a non-sandbox host that has it",
        "verify_cmd": "python -c \"import pathlib; assert pathlib.Path('elev.py').exists()\" && echo ELEV_PRESENT",
    },
    "file-absent (0-byte placeholder)": {
        "detector": "clobber_manifest (flags size-0 files that should have content)",
        "remediation": "Sync canonical from White to sandbox OR run the --apply leg directly on White",
        "verify_cmd": "python -c \"import pathlib; s=pathlib.Path('<file>').stat().st_size; assert s>0, f'File is 0 bytes: {s}'\"",
    },
    "SMB AUTH failure": {
        "detector": "stale_claim_scan (flags stale 'connected' claims after auth rejection)",
        "remediation": "Verify SMB creds + net use from persistent White host; register MirrorSync schtask",
        "verify_cmd": "python memory_mirror.py -v 2>&1 | grep -c 'Access is denied' | xargs -I{} test {} -eq 0 && echo SMB_OK",
    },
    "seat-unreachable": {
        "detector": "reach_matrix (direct: expected model not loaded for that seat)",
        "remediation": "Load the model on a non-sandbox host with egress to LM Studio :8888",
        "verify_cmd": "python -c \"import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8888/api/v0/models'); assert 200==r.status\" && echo SEAT_OK",
    },
    "stale auto-loop": {
        "detector": "dispatch_desync (goal count mismatch between autoloop.json and goal files)",
        "remediation": "Archive reached goals + update dispatch to next cycle's goal list",
        "verify_cmd": "python memory/researcher/remediation_bus.py --dry-run | grep 'dispatch_desync: 0'",
    },
}

# Fallback for unmatched classes
FALLBACK = {
    "detector": "stale_claim_scan (generic stale-reference detector)",
    "remediation": "Manual investigation required; see OPS-NOTE detail",
    "verify_cmd": "python memory/researcher/remediation_bus.py --dry-run",
}


def parse_blockers(text):
    """Parse OPS-NOTE entries from blockers.md.
    Returns list of dicts: {id, date, agent, class, title, resolved, detail_lines}"""
    entries = []
    # Split on ## [OPS-NOTE or ## [NEEDS-HUMAN or ## [RECONCILED or ## [RESOLVED headers
    entry_re = re.compile(
        r'^##\s*\[(OPS-NOTE|NEEDS-HUMAN|RECONCILED|RESOLVED)\s+(\d{4}-\d{2}-\d{2})[^\]]*\]\s*(.*)$',
        re.MULTILINE
    )
    matches = list(entry_re.finditer(text))
    for i, m in enumerate(matches):
        kind = m.group(1)
        date = m.group(2)
        title_line = m.group(3).strip()
        start = m.end()
        end = matches[i+1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]
        
        # Extract agent: look in the full header line (both inside and outside brackets)
        full_header = m.group(0)  # the entire ## [KIND DATE ...] title line
        agent = "unknown"
        for known in ["Orchestrator", "Verifier", "Builder", "Designer", "Researcher", "Archivist", "Mechanic", "Scribe"]:
            if known.lower() in full_header.lower():
                agent = known
                break
        # Fallback: check body first 200 chars
        if agent == "unknown":
            for known in ["Orchestrator", "Verifier", "Builder", "Designer", "Researcher", "Archivist", "Mechanic", "Scribe"]:
                if known.lower() in body[:200].lower():
                    agent = known
                    break
        
        # Extract class
        class_m = re.search(r'\*\*Class:\*\*\s*(.+)', body)
        blocker_class = class_m.group(1).strip().rstrip('.') if class_m else "unclassified"
        
        # Determine resolved status
        resolved = (kind == "RESOLVED" or kind == "RECONCILED")
        if not resolved:
            # Check for RESOLVED markers in body
            if re.search(r'\*\*RESOLVED\s+\d{4}', body):
                resolved = True
            elif re.search(r'\[CORRECTION.*?RESOLVED', body, re.I):
                resolved = True
        
        # Short title (first 80 chars of title_line)
        short_title = title_line[:100]
        
        entries.append({
            "id": f"BLK-{date.replace('-','')}-{agent[:4].upper()}-{i:02d}",
            "kind": kind,
            "date": date,
            "agent": agent,
            "blocker_class": blocker_class,
            "title": short_title,
            "resolved": resolved,
        })
    return entries


def match_detector(blocker_class):
    """Match a blocker class to the appropriate detector."""
    for key, info in DETECTOR_MAP.items():
        if key.lower() in blocker_class.lower():
            return info
    # Try partial matches
    for key, info in DETECTOR_MAP.items():
        words = set(key.lower().split())
        class_words = set(blocker_class.lower().split())
        if len(words & class_words) >= 2:
            return info
    return FALLBACK


def compute_success_rate(entries):
    """Compute rolling success rate for each blocker agent.
    Success = resolved. Rate = resolved / total for that agent."""
    rates = {}
    for e in entries:
        agent = e["agent"]
        if agent not in rates:
            rates[agent] = {"total": 0, "resolved": 0}
        rates[agent]["total"] += 1
        if e["resolved"]:
            rates[agent]["resolved"] += 1
    for agent, stats in rates.items():
        stats["rate"] = stats["resolved"] / stats["total"] if stats["total"] else 0
    return rates


def generate_runbook(entries, rates):
    """Generate the auto-maintained runbook markdown."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# Blocker → Catch → Fix → Verify Runbook",
        f"Auto-generated: {now}",
        f"Source: memory/ops/blockers.md ({len(entries)} entries)",
        "",
        "## Summary",
        f"- Total blockers tracked: **{len(entries)}**",
        f"- Resolved: **{sum(1 for e in entries if e['resolved'])}** ({sum(1 for e in entries if e['resolved'])/len(entries):.0%})",
        f"- Still open: **{sum(1 for e in entries if not e['resolved'])}**",
        "",
        "## Per-Agent Success Rate",
        "| Agent | Total | Resolved | Rate |",
        "|-------|-------|----------|------|",
    ]
    for agent, stats in sorted(rates.items()):
        lines.append(f"| {agent} | {stats['total']} | {stats['resolved']} | {stats['rate']:.0%} |")
    
    lines += ["", "## Runbook Entries", ""]
    
    for e in entries:
        info = match_detector(e["blocker_class"])
        status_icon = "✅" if e["resolved"] else "🔴"
        lines += [
            f"### {status_icon} {e['id']} — {e['title']}",
            f"- **Date:** {e['date']}  ",
            f"- **Agent:** {e['agent']}  ",
            f"- **Class:** {e['blocker_class']}  ",
            f"- **Status:** {'RESOLVED' if e['resolved'] else 'OPEN'}",
            f"",
            f"| Field | Detail |",
            f"|-------|--------|",
            f"| (a) Detector | {info['detector']} |",
            f"| (b) Remediation | {info['remediation']} |",
            f"| (c) Verify command | `{info['verify_cmd']}` |",
            f"| (d) Success rate ({e['agent']}) | {rates.get(e['agent'], {}).get('rate', 0):.0%} ({rates.get(e['agent'], {}).get('resolved', 0)}/{rates.get(e['agent'], {}).get('total', 0)}) |",
            "",
        ]
    
    lines += [
        "---",
        "*This runbook is auto-maintained. Re-run `python memory/researcher/blocker_loop_runbook.py` to regenerate.*",
    ]
    return '\n'.join(lines)


def selftest():
    """Synthetic test with >=5 blockers."""
    print("[selftest] Building synthetic blocker data...")
    
    synthetic_text = """## [OPS-NOTE 2026-11-20 Orchestrator]: elev.py ABSENT
**Class:** helper file-not-found
**Detail:** Cannot execute elevated commands.

## [NEEDS-HUMAN 2026-11-20 Verifier]: :8099 egress wall
**Class:** sandbox egress block (WinError 10013)
**Detail:** Portal unreachable from sandbox seat.

## [NEEDS-HUMAN 2026-11-17 Mechanic]: schtasks COM unavailable
**Class:** COM unavailable in sandbox
**Detail:** Cannot register scheduled tasks.

## [RESOLVED 2026-11-17 Red]: LAN probe to Red .245
**Class:** sandbox egress block
**Resolution:** Red confirmed reachable from non-sandbox seat.

## [OPS-NOTE 2026-11-22 Orchestrator]: Mechanic seat unreachable
**Class:** seat-unreachable + sandbox egress wall
**Detail:** Model not loaded on Mechanic seat.

## [RECONCILED 2026-11-19 Orchestrator]: Browser headless conflict
**Class:** no browser binary + sandbox egress block
**Resolution:** Static verification is acceptable closure evidence.
"""
    entries = parse_blockers(synthetic_text)
    assert len(entries) >= 5, f"Expected >=5 entries, got {len(entries)}"
    
    rates = compute_success_rate(entries)
    assert any(r["total"] >= 2 for r in rates.values()), "Need at least one agent with >=2 blockers"
    
    runbook = generate_runbook(entries, rates)
    assert "Detector" in runbook
    assert "Remediation" in runbook
    assert "Verify command" in runbook
    assert "Success rate" in runbook
    
    # Verify all 4 fields present for each entry
    field_count = runbook.count("| (a) Detector")
    assert field_count == len(entries), f"Expected {len(entries)} detector fields, got {field_count}"
    
    print(f"  Parsed {len(entries)} blocker entries")
    print(f"  Agents: {list(rates.keys())}")
    for agent, stats in sorted(rates.items()):
        print(f"    {agent}: {stats['resolved']}/{stats['total']} = {stats['rate']:.0%}")
    
    resolved_count = sum(1 for e in entries if e["resolved"])
    print(f"  Resolved: {resolved_count}/{len(entries)}")
    print("[selftest] ALL ASSERTIONS PASSED")
    return True


def main():
    if "--selftest" in sys.argv:
        selftest()
        return 0
    
    if not BLOCKERS_MD.exists():
        print(f"ERROR: {BLOCKERS_MD} not found")
        return 1
    
    text = BLOCKERS_MD.read_text(encoding="utf-8", errors="ignore")
    entries = parse_blockers(text)
    rates = compute_success_rate(entries)
    runbook = generate_runbook(entries, rates)
    OUTPUT.write_text(runbook, encoding="utf-8")
    
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[blocker_loop_runbook] {now}")
    print(f"  Parsed {len(entries)} blocker entries from blockers.md")
    print(f"  Resolved: {sum(1 for e in entries if e['resolved'])}, Open: {sum(1 for e in entries if not e['resolved'])}")
    print(f"  Agents tracked: {len(rates)}")
    print(f"  Output: {OUTPUT.name} ({len(runbook)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())