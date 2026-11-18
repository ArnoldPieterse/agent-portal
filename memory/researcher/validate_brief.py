#!/usr/bin/env python3
"""Validate a Researcher brief against the standard template.

Usage: python memory/researcher/validate_brief.py <brief_file>
Exit: 0 = PASS, 1 = FAIL (reasons printed), 2 = usage/IO error.

Rules (see brief_template.md):
  1. All 5 section headers present.
  2. Claim non-empty.
  3. Evidence lists >=3 distinct numbered sources `[n] ...`.
  4. Confidence line has exactly one of High/Medium/Low + a justification.
  5. Open Questions and Follow-up Actions non-empty (`(none)` counts).
"""
import re
import sys

SECTIONS = ["Claim", "Evidence", "Confidence", "Open Questions", "Follow-up Actions"]
CONFIDENCE = {"high", "medium", "low"}


def split_sections(text):
    """Return {section_name: body_text}. Body runs until next '## ' header or EOF."""
    bodies = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            current = m.group(1).strip()
            bodies[current] = []
        elif current is not None:
            bodies[current].append(line)
    return {k: "\n".join(v) for k, v in bodies.items()}


def nonempty(body):
    # strip markdown list markers and whitespace; treat a bare '(none)' as present
    stripped = body.strip()
    if not stripped:
        return False
    return True


def validate(text):
    errors = []
    secs = split_sections(text)

    # Rule 1: all sections present
    for s in SECTIONS:
        if s not in secs:
            errors.append(f"missing section: ## {s}")
    if errors:  # can't meaningfully check content of absent sections
        return errors

    # Rule 2: Claim non-empty
    if not nonempty(secs["Claim"]):
        errors.append("Claim is empty")

    # Rule 3: Evidence >=3 distinct numbered sources
    evidence = secs["Evidence"]
    nums = re.findall(r"^\s*\[(\d+)\]\s+", evidence, flags=re.M)
    unique_nums = set(nums)
    if len(unique_nums) < 3:
        errors.append(f"Evidence has {len(unique_nums)} distinct numbered source(s); need >=3")
    # detect duplicate references (same url/ref text under different numbers)
    refs = re.findall(r"^\s*\[\d+\]\s+(.+?)\s*$", evidence, flags=re.M)
    seen = {}
    for i, r in enumerate(refs):
        key = r.lower().strip()
        if key in seen:
            errors.append(f"Evidence source {i+1} duplicates source {seen[key]+1}")
        else:
            seen[key] = i

    # Rule 4: Confidence must START with exactly one High/Medium/Low label
    # (label at start of first content line, not buried in prose) + a justification.
    conf_lines = [l for l in secs["Confidence"].splitlines() if l.strip()]
    if not conf_lines:
        errors.append("Confidence section is empty")
    else:
        first = re.sub(r"^[-*\s]+", "", conf_lines[0])  # strip list marker/leading space
        m = re.match(r"^(high|medium|low)\b", first, flags=re.I)
        if not m:
            errors.append("Confidence must start with a High/Medium/Low label")
        else:
            label = m.group(1).lower()
            # no other distinct confidence label may lead another line
            others = set()
            for l in conf_lines[1:]:
                mm = re.match(r"^[-*\s]*(high|medium|low)\b", l, flags=re.I)
                if mm and mm.group(1).lower() != label:
                    others.add(mm.group(1).lower())
            if others:
                errors.append(f"Confidence has conflicting labels: {label} vs {sorted(others)}")
            # justification = text after the label on the first line
            just = first[m.end():].strip(" \t-—:.").strip()
            if len(just) < 5:
                errors.append("Confidence has no justification after the label")

    # Rule 5: Open Questions + Follow-up Actions non-empty ((none) counts)
    for s in ["Open Questions", "Follow-up Actions"]:
        body = secs[s].strip()
        if not body:
            errors.append(f"{s} is empty")

    return errors


def main():
    if len(sys.argv) != 2:
        print("usage: python validate_brief.py <brief_file>")
        return 2
    path = sys.argv[1]
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(f"IO error: {e}")
        return 2
    errors = validate(text)
    if errors:
        print(f"FAIL {path}")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"PASS {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
