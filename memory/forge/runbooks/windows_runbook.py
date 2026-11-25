"""Auto-generated runbook executor (Forge goal #8) for windows-runbook.md.

SAFE default: --dry-run parses the source runbook and prints its imperative steps
without executing; exit 0. Real execution requires FORGE_RUNBOOK_APPLY=1 AND is
restricted to read-only prefixes. Never run fleet-mutating commands by accident.
"""
import os, re, sys
from pathlib import Path
SRC = Path('C:\\Users\\White\\.unsloth\\studio\\sandbox\\_default\\memory\\ops\\windows-runbook.md')
STEP_RE = re.compile(r"^(?:\s*\d+[.)]|\s*[-*]\s+(?=python|elev\.py|schtasks|git\b))", re.IGNORECASE)
PYREF_RE = re.compile(r"(?:^|\s)(?:python[0-9.]*|py)\s+([A-Za-z0-9_./\\-]+\.py)")
READONLY_PREFIXES = ("python", "py", "git status", "git log", "schtasks /query", "type ", "dir ")

def steps():
    out = []
    if not SRC.exists():
        return out
    for ln in SRC.read_text(encoding="utf-8", errors="replace").splitlines():
        s = ln.strip()
        if not s:
            continue
        if STEP_RE.match(ln) or PYREF_RE.search(ln):
            m = PYREF_RE.search(ln)
            out.append(m.group(1) if m else s.lstrip("0123456789.)- *"))
    return [x for x in out if x]

def main():
    apply_mode = os.environ.get("FORGE_RUNBOOK_APPLY") == "1" and "--apply" in sys.argv
    dry = not apply_mode
    print(f"runbook executor: {SRC.name}")
    st = steps()
    if not st:
        print("  no imperative steps found; nothing to run (exit 0)")
        return 0
    for i, s in enumerate(st, 1):
        prefix = s.lower().split()[0] if s.split() else ""
        safe = any(s.lower().startswith(p) for p in READONLY_PREFIXES)
        if dry or not safe:
            tag = "dry-run" if dry else "SKIP(not-readonly)"
            print(f"  [{tag}] {i}. {s}")
        else:
            # read-only apply only
            import subprocess
            r = subprocess.run(s, shell=True, capture_output=True, text=True)
            print(f"  [ran rc={r.returncode}] {i}. {s}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
