#!/usr/bin/env python3
"""verify_claims.py — anti-phantom evidence guard (Builder, 2026-11-19).

Problem it targets: a goal file can carry a `verified:` marker while the artifact
it cites does not exist on disk. The evidence-gated ledger correctly refuses to
close such goals (archivist showed 2/10 despite 'verified:' text on #2-#9), but
nobody had a tool that *shows* which claims are phantom vs. real.

What it does:
  * scans every seat goal file in memory/goals/*.md
  * for each numbered goal block, detects a `verified:` marker
  * extracts candidate artifact paths (memory/... .py/.md/.json/.jsonl)
  * classifies the claim:
      REAL     - verified + >=1 cited path exists on disk
      PHANTOM  - verified + cited path(s) present but NONE exist  <-- the bug
      UNCITED  - verified + no machine-checkable path cited (manual-only claim)
  * writes a report to memory/ops/claim-phantom-report.md and prints a summary.

Usage:
    python memory/ops/verify_claims.py            # scan + write report
    python memory/ops/verify_claims.py --quiet    # print summary only, no file

Side-effect-free: read-only on goal files; the only write is its own report.
"""
import argparse
import datetime as _dt
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
GOALS_DIR = ROOT / "memory" / "goals"
REPORT = ROOT / "memory" / "ops" / "claim-phantom-report.md"

# Seat goal files only (skip forecasts, INDEX, archives, raw txt).
SEAT_FILES = [
    "orchestrator.md", "researcher.md", "builder.md", "archivist.md",
    "scribe.md", "verifier.md", "designer.md", "mechanic.md",
]

# 2026-11-20 Researcher fix: `jsonl` MUST precede `json`. With the old order
# `(?:py|md|json|jsonl)` a cited `.jsonl` artifact matched only its `.json`
# prefix (trailing 'l' left unmatched), so it extracted a non-existent `.json`
# path and every .jsonl-citing goal was flagged PHANTOM (false positive).
PATH_RE = re.compile(r"memory/[A-Za-z0-9_./\-]+\.(?:py|md|jsonl|json)")
GOAL_HEAD_RE = re.compile(r"^(?P<num>\d+)\. \*\*(?P<title>.*?)\*\*", re.M)

# 2026-11-20 Researcher fix: template placeholder citations (e.g.
# `roster-snapshots/cycle-N.json`, `sla-report-YYYY-MM-DD.md`) are NOT missing
# work - they just need a concrete artifact pointer. Keep them OUT of PHANTOM
# classification so the report only flags genuinely absent artifacts.
def is_template(p):
    base = p.rsplit("/", 1)[-1]
    if "YYYY" in base:
        return True
    if re.fullmatch(r"cycle-[A-Z]\.jsonl?", base):
        return True
    return False


def split_goal_blocks(text):
    """Return list of (num, title, body) for numbered goal blocks."""
    heads = list(GOAL_HEAD_RE.finditer(text))
    out = []
    for i, m in enumerate(heads):
        start = m.start()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[start:end]
        out.append((int(m.group("num")), m.group("title").strip(), body))
    return out


def classify(verified, cited_paths, existing):
    if not verified:
        return None  # not a claim
    if not cited_paths:
        return "UNCITED"
    if any(p in existing for p in cited_paths):
        return "REAL"
    return "PHANTOM"


def scan():
    rows = []  # (seat, num, title, status, cited, missing)
    for fname in SEAT_FILES:
        fp = GOALS_DIR / fname
        if not fp.exists():
            continue
        seat = fname[:-3]
        text = fp.read_text(encoding="utf-8", errors="replace")
        for num, title, body in split_goal_blocks(text):
            verified = "verified:" in body.lower()
            cited_all = sorted(set(PATH_RE.findall(body)))
            templates = [c for c in cited_all if is_template(c)]
            concrete = [c for c in cited_all if not is_template(c)]
            existing = {c for c in concrete if (ROOT / c).exists()}
            # classify on CONCRETE paths only; a goal citing only placeholders
            # becomes UNCITED (needs a concrete pointer), never PHANTOM.
            status = classify(verified, concrete, existing)
            if status is None:
                continue
            missing = [c for c in concrete if c not in existing] + templates
            rows.append((seat, num, title, status, cited_all, missing))
    return rows


def render(rows):
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    phantoms = [r for r in rows if r[3] == "PHANTOM"]
    uncited = [r for r in rows if r[3] == "UNCITED"]
    real = [r for r in rows if r[3] == "REAL"]
    lines = [
        "# Claim-Phantom Report",
        f"Generated: {now} by `memory/ops/verify_claims.py` (Builder).",
        "",
        "Classifies every `verified:` marker in seat goal files against the disk:",
        "  * REAL    - verified + a cited artifact exists on disk",
        "  * PHANTOM - verified + cited path(s) present but NONE exist  (stale/false claim)",
        "  * UNCITED - verified + no machine-checkable path (manual-only; needs a pointer added)",
        "",
        f"**Totals: {len(real)} REAL, {len(phantoms)} PHANTOM, {len(uncited)} UNCITED.**",
        "",
    ]
    if phantoms:
        lines.append("## PHANTOM claims (verified but artifact missing) — owner should re-do or drop the marker")
        for seat, num, title, _, cited, missing in phantoms:
            lines.append(f"- **{seat} #{num}** {title}")
            for c in missing:
                lines.append(f"    - MISSING: `{c}`")
        lines.append("")
    if uncited:
        lines.append("## UNCITED verified claims (no path to check — add an artifact pointer so the ledger can close them)")
        for seat, num, title, _, cited, _ in uncited:
            lines.append(f"- **{seat} #{num}** {title}")
        lines.append("")
    lines.append("## REAL claims (verified + artifact present)")
    for seat, num, title, _, cited, _ in real:
        ok = [c for c in cited if (ROOT / c).exists()]
        lines.append(f"- **{seat} #{num}** {title}  -> `{ok[0]}`")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Anti-phantom evidence guard.")
    ap.add_argument("--quiet", action="store_true", help="print summary only, do not write report")
    args = ap.parse_args()
    rows = scan()
    phantoms = [r for r in rows if r[3] == "PHANTOM"]
    uncited = [r for r in rows if r[3] == "UNCITED"]
    real = [r for r in rows if r[3] == "REAL"]
    print(f"verify_claims: {len(real)} REAL, {len(phantoms)} PHANTOM, {len(uncited)} UNCITED")
    for seat, num, title, _, cited, missing in phantoms:
        print(f"  PHANTOM {seat} #{num}: {title[:40]}  missing={missing}")
    if not args.quiet and rows:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(render(rows), encoding="utf-8")
        print(f"report -> {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
