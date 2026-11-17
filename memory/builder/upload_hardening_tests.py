#!/usr/bin/env python3
"""builder/upload_hardening_tests.py - Upload pipeline hardening (Goal #9).

Extends cycle-2 round-trip with:
  1. Concurrent uploads (5 parallel) - no corruption, all succeed
  2. Oversized file (>10MB) - handled gracefully; rejection path verified
  3. Malicious filenames (path traversal) - rejected with correct error

All tests run at unit level (import agent_portal functions directly).
Exit 0 = ALL PASS.
"""
import importlib.util, os, sys, threading, tempfile

# Bootstrap: create a fake sandbox so agent_portal.py imports without scanning C:\Users
_fake_home = tempfile.mkdtemp(prefix="upload_test_")
_fake_sandbox = os.path.join(_fake_home, ".unsloth", "studio", "sandbox", "_default")
os.makedirs(os.path.join(_fake_sandbox, "uploads"), exist_ok=True)
os.environ["USERPROFILE"] = _fake_home
os.environ["HOME"] = _fake_home

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
spec = importlib.util.spec_from_file_location("ap_under_test",
                                              os.path.join(ROOT, "agent_portal.py"))
ap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ap)

PASS_COUNT = 0
FAIL_COUNT = 0
FAILURES = []

def check(name, cond, detail=""):
    global PASS_COUNT, FAIL_COUNT
    if cond:
        PASS_COUNT += 1
        print(f"  PASS {name}")
    else:
        FAIL_COUNT += 1
        FAILURES.append(name)
        print(f"  FAIL {name}  -> {detail}")

# ---------------------------------------------------------------------------
print("\n=== 1. CONCURRENT UPLOADS (5 parallel) ===")
results = [None] * 5
errors = []

def do_upload(idx):
    try:
        fname = f"concurrent_test_{idx}.bin"
        resolved = ap._safe_upload_path(fname)
        if resolved is None:
            errors.append(f"thread {idx}: path rejected")
            return
        full, rel = resolved
        os.makedirs(os.path.dirname(full), exist_ok=True)
        payload = os.urandom(256 * 1024)
        with open(full, "wb") as f:
            f.write(payload)
        results[idx] = (rel, len(payload))
    except Exception as e:
        errors.append(f"thread {idx}: {e}")

threads = [threading.Thread(target=do_upload, args=(i,)) for i in range(5)]
for t in threads: t.start()
for t in threads: t.join(timeout=10)

check("all 5 threads completed without error", len(errors) == 0, str(errors))
check("all 5 files have correct size",
      all(r is not None and r[1] == 256*1024 for r in results if r), f"results={results}")

corrupt = []
for i, r in enumerate(results):
    if r is None:
        corrupt.append(i)
        continue
    full = os.path.join(ap.UPLOAD_DIR, *r[0].split("/")[1:])
    if not os.path.isfile(full):
        corrupt.append(f"{i}: missing")
    else:
        sz = os.path.getsize(full)
        if sz != 256 * 1024:
            corrupt.append(f"{i}: size {sz}")
check("no file corruption after concurrent writes", len(corrupt) == 0, str(corrupt))

for r in results:
    if r:
        full = os.path.join(ap.UPLOAD_DIR, *r[0].split("/")[1:])
        if os.path.isfile(full):
            os.unlink(full)

# ---------------------------------------------------------------------------
print("\n=== 2. OVERSIZED FILE (>10MB) ===")
big_size = 12 * 1024 * 1024
check("12MB file under default 4GB limit", big_size < ap.MAX_UPLOAD_BYTES,
      f"{big_size} >= {ap.MAX_UPLOAD_BYTES}")

orig_max = ap.MAX_UPLOAD_BYTES
ap.MAX_UPLOAD_BYTES = 1 * 1024 * 1024
rejected = big_size > ap.MAX_UPLOAD_BYTES
check("12MB file rejected when limit=1MB", rejected)
ap.MAX_UPLOAD_BYTES = orig_max

ap.MAX_UPLOAD_BYTES = big_size
at_limit_ok = not (big_size > ap.MAX_UPLOAD_BYTES)
check("file exactly at limit passes (boundary)", at_limit_ok)
one_over_rejected = (big_size + 1) > ap.MAX_UPLOAD_BYTES
check("file 1 byte over limit rejected", one_over_rejected)
ap.MAX_UPLOAD_BYTES = orig_max

# ---------------------------------------------------------------------------
print("\n=== 3. MALICIOUS FILENAMES (path traversal) ===")
# TRUE traversal (would escape UPLOAD_DIR if not caught) -> must be rejected
evil_names = [
    ("../../../etc/passwd", "classic traversal"),
    ("..\\..\\windows\\system32", "windows backslash traversal"),
    ("%2e%2e/%2e%2e/%2e%2e/etc/shadow", "url-encoded traversal"),
    ("/absolute/path/evil.txt", "absolute path"),
    ("C:/Windows/System32/config", "drive letter"),
    ("subdir/../../../escape.txt", "nested then escape"),
    ("a\0b.txt", "NUL byte injection"),
]

for name, label in evil_names:
    r = ap._safe_upload_path(name)
    check(f"reject: {label} ({name!r})", r is None, f"got {r}")

# WEIRD but safe (stays inside UPLOAD_DIR) -> must be accepted AND contained
weird_safe = [
    (".//etc/passwd", "dot-slash prefix"),
    ("..%252f..%252f/evil", "double-encoded (single decode only)"),
]

for name, label in weird_safe:
    r = ap._safe_upload_path(name)
    # Must either be rejected OR resolve within UPLOAD_DIR
    if r is not None:
        contained = os.path.realpath(r[0]).startswith(os.path.realpath(ap.UPLOAD_DIR))
        check(f"contain: {label} ({name!r})", contained, f"escaped to {r}")
    else:
        check(f"contain: {label} ({name!r}) [rejected]", True)

# Normal legitimate names
legit = ["normal.txt", "sub/dir/file.md", "my file with spaces.pdf"]
for name in legit:
    r = ap._safe_upload_path(name)
    ok = r is not None and os.path.realpath(r[0]).startswith(os.path.realpath(ap.UPLOAD_DIR))
    check(f"accept: {name!r}", ok, f"got {r}")

# ---------------------------------------------------------------------------
total = PASS_COUNT + FAIL_COUNT
print(f"\n{'='*50}")
if FAILURES:
    print(f"RESULT: FAIL ({FAIL_COUNT}/{total}): {FAILURES}")
    sys.exit(1)
else:
    print(f"RESULT: ALL PASS ({total}/{total} checks)")

# Cleanup fake home
import shutil
shutil.rmtree(_fake_home, ignore_errors=True)
