"""File-modularity linter: enforces fleet size rules.

Rules (configurable via CLI):
  - INDEX files (*INDEX.md): max 1600 chars
  - Leaf files (.md, .py, .js, .css in memory/ or ui/): max 4096 bytes

Exit 0 = clean, Exit 1 = violations found.
CI-gated: wire into pre_commit_gate.py as `python modularity_check.py`.
"""
import sys
import os
from pathlib import Path

# Defaults — override via argparse below
INDEX_MAX_CHARS = 1600
LEAF_MAX_BYTES = 4096

SCAN_DIRS = ["memory", "ui"]
TEXT_EXTS = {".md", ".py", ".js", ".css"}


def is_index_file(path: Path) -> bool:
    return path.name.upper().endswith("INDEX.MD") or path.name == "INDEX.md"


def check_tree(root: Path) -> list[tuple[str, str, int, int]]:
    """Return list of (relpath, kind, size, limit)."""
    violations = []
    for d in SCAN_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if not p.is_file() or p.suffix.lower() not in TEXT_EXTS:
                continue
            size = p.stat().st_size
            rel = str(p.relative_to(root)).replace("\\", "/")
            if is_index_file(p):
                # INDEX limit is character count (not bytes) for CJK tolerance
                try:
                    chars = len(p.read_text(encoding="utf-8"))
                except UnicodeDecodeError:
                    continue
                if chars > INDEX_MAX_CHARS:
                    violations.append((rel, "INDEX", chars, INDEX_MAX_CHARS))
            else:
                if size > LEAF_MAX_BYTES:
                    violations.append((rel, "LEAF", size, LEAF_MAX_BYTES))
    return violations


def main() -> int:
    import argparse
    global INDEX_MAX_CHARS, LEAF_MAX_BYTES
    ap = argparse.ArgumentParser(description="File-modularity linter")
    ap.add_argument("--root", default=".", help="Project root (default: cwd)")
    ap.add_argument("--index-max", type=int, default=INDEX_MAX_CHARS)
    ap.add_argument("--leaf-max", type=int, default=LEAF_MAX_BYTES)
    args = ap.parse_args()

    INDEX_MAX_CHARS = args.index_max
    LEAF_MAX_BYTES = args.leaf_max

    root = Path(args.root).resolve()
    violations = check_tree(root)

    if not violations:
        print(f"[modularity] PASS — all files within limits (index<={INDEX_MAX_CHARS}c, leaf<={LEAF_MAX_BYTES}b)")
        return 0

    print(f"[modularity] FAIL — {len(violations)} violation(s):")
    for rel, kind, size, limit in violations:
        # Find the line number where the file exceeds the limit (for leaf: byte offset -> approx line)
        p = root / rel
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            content = ""
        if kind == "INDEX":
            # Report char position of first overflow
            overflow_at = INDEX_MAX_CHARS
            line_no = content[:overflow_at].count("\n") + 1
            print(f"  {rel} [{kind}] {size} chars > {limit} (overflow near line {line_no})")
        else:
            # Approximate: find line containing byte offset limit
            lines = content.splitlines(keepends=True)
            cumulative = 0
            line_no = len(lines)  # fallback
            for i, ln in enumerate(lines, 1):
                if cumulative + len(ln.encode("utf-8", errors="replace")) > LEAF_MAX_BYTES:
                    line_no = i
                    break
                cumulative += len(ln.encode("utf-8", errors="replace"))
            print(f"  {rel} [{kind}] {size} bytes > {limit} (overflow near line {line_no})")
    return 1


if __name__ == "__main__":
    sys.exit(main())