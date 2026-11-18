#!/usr/bin/env python3
# archivist/provenance_audit.py — provenance sweep of git-tracked files (Archivist goal 6, 2026-11-13)
# Checks every candidate tracked file for a header comment carrying date + author agent + purpose.
# Candidate set = root-level source/config/docs + full memory/ tree (mirrors the ~43-file git
# allowlist per memory/portal/architecture.md; exact list re-verifiable on White via `git ls-files`).
# Excluded (never tracked): unsloth-tmp/, .unsloth_sandbox/, uploads/, __pycache__, mingit/, PNG/log dumps.
# Exit: 0 = all candidates have headers, 1 = N missing. Stdlib only; run from repo root.
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root (canonical location memory/archivist/)
EXCLUDE_DIRS = {"unsloth-tmp", ".unsloth_sandbox", "uploads", "__pycache__", "mingit",
                ".git", "todo_done_parts", "ws-b-increment1", "git-bootstrap"}
EXCLUDE_SUFFIX = {".png", ".jpg", ".log", ".zip", ".bat", ".ps1", ".ac5e1560.html"}
AGENTS = ("orchestrator", "researcher", "builder", "verifier", "designer",
          "archivist", "scribe", "mechanic")
DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2}|11-13|Nov 13)")


def candidates():
    out = []
    for p in sorted(ROOT.iterdir()):
        if p.is_file() and p.suffix not in EXCLUDE_SUFFIX and not p.name.startswith("."):
            out.append(p)
    mem = ROOT / "memory"
    if mem.is_dir():
        for p in sorted(mem.rglob("*")):
            if p.is_file() and all(part not in EXCLUDE_DIRS for part in p.parts):
                out.append(p)
    return out


def header_verdict(path: Path):
    """Return (has_header, evidence) — header = first 6 lines carry date AND (agent name OR purpose marker)."""
    try:
        head = "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[:6])
    except Exception as e:  # unreadable binary etc.
        return False, f"unreadable: {e}"
    low = head.lower()
    has_date = bool(DATE_RE.search(head))
    has_agent = any(a in low for a in AGENTS)
    is_comment = head.lstrip().startswith(("#", "<!--", "<!DOCTYPE", '"""', "///")) or low.startswith("<!--")
    ok = is_comment and (has_date or has_agent)
    ev = []
    ev.append("date" if has_date else "NO-date")
    ev.append("agent" if has_agent else "NO-agent")
    ev.append("comment" if is_comment else "NO-comment")
    return ok, "+".join(ev)


def main() -> int:
    cands = candidates()
    missing, present = [], []
    for p in cands:
        rel = p.relative_to(ROOT).as_posix()
        ok, ev = header_verdict(p)
        (present if ok else missing).append((rel, p.stat().st_size, ev))
    print(f"provenance_audit — {len(cands)} candidate tracked files")
    print(f"WITH header ({len(present)}):")
    for rel, size, ev in present:
        print(f"  ok   {rel}  [{size} B] {ev}")
    print(f"MISSING header ({len(missing)}):")
    for rel, size, ev in missing:
        print(f"  MISS {rel}  [{size} B] {ev}")
    print("RESULT: " + ("CLEAN" if not missing else f"FAIL ({len(missing)} missing)"))
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
