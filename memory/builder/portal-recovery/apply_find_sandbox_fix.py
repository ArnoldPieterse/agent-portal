# apply_find_sandbox_fix.py - Builder r77 (2026-11-14)
#
# Hardens _find_sandbox_dir() in agent_portal.py: the C:\Users scan fallback
# runs os.listdir(users) UNGUARDED at import time, so any launch context that
# cannot enumerate C:\Users (agent seats / restricted tokens) crashes the whole
# portal before it binds :8099. After this patch the fallback degrades to an
# empty list instead of dying; normal console launches are unaffected.
#
# Usage (on White):  python memory\builder\portal-recovery\apply_find_sandbox_fix.py [target]
#   target defaults to <workspace-root>\agent_portal.py (3 levels above this file).
# Idempotent: re-running on an already-patched file exits 0 with 'already applied'.
# Exact-guarded: if the expected pre-image is absent AND the post-image is absent,
# it fails loudly and writes NOTHING (file drift => stop, inspect by hand).

import os, sys, py_compile, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TARGET = os.path.normpath(os.path.join(HERE, "..", "..", "..", "agent_portal.py"))
target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TARGET

BEFORE = r'''    users = os.path.join(os.environ.get("SystemDrive", "C:") + "\\", "Users")
    if os.path.isdir(users):
        for u in sorted(os.listdir(users)):
            cand = os.path.join(users, u, ".unsloth", "studio", "sandbox", "_default")
            if os.path.isdir(cand):
                return cand
    return d'''

AFTER = r'''    users = os.path.join(os.environ.get("SystemDrive", "C:") + "\\", "Users")
    try:
        entries = sorted(os.listdir(users)) if os.path.isdir(users) else []
    except OSError:
        # 2026-11-14: restricted launch contexts (agent seats / tokens without
        # C:\Users enumerate rights) made this fallback crash the portal at import.
        entries = []
    for u in entries:
        cand = os.path.join(users, u, ".unsloth", "studio", "sandbox", "_default")
        if os.path.isdir(cand):
            return cand
    return d'''

src = open(target, encoding="utf-8").read()
if AFTER in src:
    print("already applied -", target)
    sys.exit(0)
count = src.count(BEFORE)
if count != 1:
    print(f"ABORT: pre-image found {count}x (need exactly 1) in {target}")
    print("File has drifted from the a3bec6e6 baseline - inspect by hand, nothing written.")
    sys.exit(2)
new = src.replace(BEFORE, AFTER, 1)

# compile-check the candidate BEFORE touching the real file
fd, tmp = tempfile.mkstemp(suffix=".py", dir=os.path.dirname(os.path.abspath(target)))
os.close(fd)
try:
    open(tmp, "w", encoding="utf-8").write(new)
    py_compile.compile(tmp, doraise=True)
finally:
    os.unlink(tmp)

with open(target, "w", encoding="utf-8") as f:
    f.write(new)
print("PATCHED:", target)
print("Note: agent_portal.py hash changes - update the TODO/MEMORY pin after apply.")
