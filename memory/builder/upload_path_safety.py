#!/usr/bin/env python3
"""builder/upload_path_safety.py - path-safety suite for _safe_upload_path (Builder goal).

Covers: drive letters, ../ traversal (raw + URL-encoded), POSIX absolute,
bare 'uploads' prefix, NUL bytes, plus valid inputs (flat, nested, encoded space).
Re-run on every portal edit; must stay green. Exit 0 = all PASS.
Usage:  python memory/builder/upload_path_safety.py
"""
import importlib.util, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
spec = importlib.util.spec_from_file_location("ap_under_test",
                                              os.path.join(ROOT, "agent_portal.py"))
ap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ap)

fails = []
def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  -> {detail}" if detail and not cond else ""))
    if not cond: fails.append(name)

base = os.path.realpath(ap.UPLOAD_DIR)

# REJECT cases
for label, evil in [
    ("drive-letter C:/", "C:/evil.txt"),
    ("drive-letter lower c:\\\\", "c:\\windows\\system32"),
    ("traversal ../", "../secret.txt"),
    ("traversal nested uploads/../../..", "uploads/../../etc/passwd"),
    ("traversal url-encoded %2e%2e", "%2e%2e/%2e%2e/evil"),
    ("posix absolute /etc", "/etc/passwd"),
    ("bare 'uploads' prefix", "uploads"),
    ("NUL byte", "a\0b.txt"),
]:
    r = ap._safe_upload_path(evil)
    check(f"reject {label}", r is None, f"got {r}")

# ACCEPT cases
r = ap._safe_upload_path("report.pdf")
check("accept flat name", r is not None and r[0] == os.path.realpath(os.path.join(base, "report.pdf")) and r[1] == "uploads/report.pdf", str(r))
r = ap._safe_upload_path("uploads/sub/dir/file.md")
check("accept explicit uploads/ nested", r is not None and r[1] == "uploads/sub/dir/file.md", str(r))
r = ap._safe_upload_path("my%20file.txt")
check("accept url-encoded space", r is not None and r[1] == "uploads/my file.txt", str(r))
r = ap._safe_upload_path("sub/.." )
check("reject dotdot collapsing to base", r is None, str(r))

print()
if fails:
    print(f"RESULT: FAIL ({len(fails)}): {fails}"); sys.exit(1)
print(f"RESULT: ALL PASS ({12 - len(fails)}/12 checks)")
