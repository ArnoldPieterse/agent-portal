"""SIM updater: append a structured attempt to memory/mechanic/sim.md.

Usage:
  python sim_update.py --problem model-seat-unreachable \
      --action "reloaded catalog JSON" --rationale "bad escape hid Black" \
      --predicted "seat visible after restart" --observed "PASS, portal restarted" \
      --provenance "memory/mechanic/host-idle-investigation-2026-11-26.md"

Stdlib-only. Appends to the matching problem section; creates new section if absent.
"""
import argparse, datetime, pathlib, re, sys

SIM_PATH = pathlib.Path(__file__).parent / "sim.md"

def next_attempt_number(text: str, problem: str) -> int:
    """Find the last aN for this problem section."""
    m = re.search(rf"## Problem: {re.escape(problem)}\n(.*?)(?=^## |^---)", text, re.M | re.S)
    if not m:
        return 1
    nums = [int(n) for n in re.findall(r"- a(\d+) \(", m.group(1))]
    return max(nums) + 1 if nums else 1

def update_sim(problem, action, rationale, predicted, observed, provenance):
    text = SIM_PATH.read_text(encoding="utf-8")
    n = next_attempt_number(text, problem)
    date = datetime.date.today().isoformat()
    entry = f"- a{n} ({date}): {action}\n"
    entry += f"  - rationale: {rationale}\n"
    entry += f"  - predicted: {predicted}\n"
    entry += f"  - observed: {observed}\n"
    entry += f"  - provenance: {provenance}\n"

    pattern = rf"(## Problem: {re.escape(problem)}\n)"
    m = re.search(pattern, text)
    if m:
        # Insert after the section header + any existing content (before next ## or ---)
        section_start = m.end()
        # Find end of this section
        rest = text[section_start:]
        next_sec = re.search(r"^## |^---", rest, re.M)
        insert_at = section_start + (next_sec.start() if next_sec else len(rest))
        # Insert before the "Decision rule" line if present
        dr = re.search(rf"(\*\*Decision rule\*\*:.*?)(?=\n)", text[insert_at-200:insert_at+50], re.S)
        text = text[:insert_at] + entry + "\n" + text[insert_at:]
    else:
        # New problem section — insert before the --- footer
        new_section = f"\n## Problem: {problem}\n{entry}\n- **Decision rule**: TBD\n"
        footer = text.rfind("\n---")
        text = text[:footer] + new_section + text[footer:]

    SIM_PATH.write_text(text, encoding="utf-8")
    print(f"[SIM] Appended a{n} to problem '{problem}' ({len(entry)} chars)")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Append structured attempt to SIM")
    p.add_argument("--problem", required=True)
    p.add_argument("--action", required=True)
    p.add_argument("--rationale", required=True)
    p.add_argument("--predicted", required=True)
    p.add_argument("--observed", required=True)
    p.add_argument("--provenance", required=True)
    a = p.parse_args()
    update_sim(a.problem, a.action, a.rationale, a.predicted, a.observed, a.provenance)
