"""Verification test for log_rotate.py - exercises all acceptance criteria.
Acceptance: (1) >50MB file rotated, (2) 8-day-old files compressed, (3) no data loss."""
import os, sys, gzip, glob, tempfile, time
from datetime import datetime, timezone, timedelta

# Ensure we can import the module under test
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import log_rotate

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {detail}")

print("=== log_rotate.py acceptance test ===")

# --- Test 1: File >50MB gets rotated ---
print("\nTest 1: File exceeding 50MB is rotated")
tmpdir = tempfile.mkdtemp(prefix="logrot_test_")
test_file = os.path.join(tmpdir, "big.log")
# Write a file just over 50MB (use repeated pattern for speed)
chunk = b"x" * 1024 * 1024  # 1MB chunk
expected_size = 51 * 1024 * 1024  # 51MB
with open(test_file, "wb") as f:
    for _ in range(51):
        f.write(chunk)

size_before = os.path.getsize(test_file)
check("file created at expected size", size_before == expected_size, f"got {size_before}")

# Run rotation
rotated = log_rotate.rotate_file(test_file)
check("rotate_file returns True for >50MB file", rotated)
check("live file truncated to 0 after rotation", os.path.getsize(test_file) == 0)

# Verify the .gz artifact exists and contains original data
gz_files = [f for f in os.listdir(tmpdir) if f.startswith("big.log.") and f.endswith(".gz")]
check("exactly one .gz artifact created", len(gz_files) == 1, f"found {gz_files}")
if gz_files:
    gz_path = os.path.join(tmpdir, gz_files[0])
    with gzip.open(gz_path, "rb") as gf:
        data = gf.read()
    check("compressed data matches original size", len(data) == expected_size, f"got {len(data)}")
    check("no data loss (content identical)", data == chunk * 51)

# --- Test 2: File <=50MB is NOT rotated ---
print("\nTest 2: File under 50MB is not rotated")
small_file = os.path.join(tmpdir, "small.log")
with open(small_file, "wb") as f:
    f.write(b"tiny content")

rotated_small = log_rotate.rotate_file(small_file)
check("rotate_file returns False for small file", not rotated_small)
check("small file unchanged", os.path.getsize(small_file) == 12)

# --- Test 3: 8-day-old file gets compressed by compress_old_files ---
print("\nTest 3: 8-day-old .jsonl file is compressed")
old_file = os.path.join(tmpdir, "old_data.jsonl")
old_content = b'{"ts":"2026-11-14","event":"test"}\n' * 100
with open(old_file, "wb") as f:
    f.write(old_content)

# Set mtime to 8 days ago
eight_days_ago = (datetime.now(timezone.utc) - timedelta(days=8)).timestamp()
os.utime(old_file, (eight_days_ago, eight_days_ago))

# Temporarily narrow the scan to our tmpdir by monkey-patching FLEET_ROOT
orig_root = log_rotate.FLEET_ROOT
log_rotate.FLEET_ROOT = tmpdir
compressed_count = log_rotate.compress_old_files()
log_rotate.FLEET_ROOT = orig_root

check("compress_old_files returned count >= 1", compressed_count >= 1, f"got {compressed_count}")
check("original old file removed", not os.path.exists(old_file))
gz_old = [f for f in os.listdir(tmpdir) if f.startswith("old_data.jsonl.") and f.endswith(".gz")]
check("compressed .gz exists for old file", len(gz_old) == 1, f"found {gz_old}")
if gz_old:
    with gzip.open(os.path.join(tmpdir, gz_old[0]), "rb") as gf:
        check("old file content preserved in .gz", gf.read() == old_content)

# --- Test 4: Recent file (1 day old) is NOT compressed ---
print("\nTest 4: Recent file (1 day old) is not compressed")
recent_file = os.path.join(tmpdir, "recent.log")
with open(recent_file, "wb") as f:
    f.write(b"recent data")
one_day_ago = (datetime.now(timezone.utc) - timedelta(days=1)).timestamp()
os.utime(recent_file, (one_day_ago, one_day_ago))

log_rotate.FLEET_ROOT = tmpdir
compressed_recent = log_rotate.compress_old_files()
log_rotate.FLEET_ROOT = orig_root

check("recent file still exists after compression pass", os.path.exists(recent_file))

# --- Cleanup ---
import shutil
shutil.rmtree(tmpdir, ignore_errors=True)

print(f"\n=== RESULTS: {PASS} passed, {FAIL} failed ===")
sys.exit(0 if FAIL == 0 else 1)
