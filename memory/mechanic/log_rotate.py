"""Log Rotation + Retention - rotates .log files >10MB, keeps 5, compresses old.
Usage: python memory/mechanic/log_rotate.py [--once | --schedule]"""
import os, sys, time, glob, gzip, shutil
from datetime import datetime, timezone

LOG_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_SIZE = 10 * 1024 * 1024  # 10MB
KEEP_ROTATIONS = 5
INTERVAL_S = 1800  # 30 min

def rotate_file(path):
    """Rotate a single log file. Returns True if rotated."""
    if not os.path.exists(path) or os.path.getsize(path) < MAX_SIZE:
        return False
    base, ext = os.path.splitext(path)
    # Shift existing rotations: .log.4 -> .log.5 (delete if >KEEP), .log.3 -> .log.4, etc.
    for i in range(KEEP_ROTATIONS - 1, 0, -1):
        src = f"{base}{ext}.{i}"
        dst = f"{base}{ext}.{i+1}"
        if os.path.exists(src):
            # Clear the target first: Windows os.rename() raises WinError 183
            # if dst already exists (e.g. a prior run crashed mid-rotation).
            if os.path.exists(dst):
                os.remove(dst)
            os.rename(src, dst)
    # Compress the oldest rotation
    oldest = f"{base}{ext}.{KEEP_ROTATIONS}"
    if os.path.exists(oldest) and not oldest.endswith(".gz"):
        with open(oldest, "rb") as f_in:
            with gzip.open(oldest + ".gz", "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(oldest)
    # Current -> .log.1
    os.rename(path, f"{base}{ext}.1")
    # Create fresh empty file
    open(path, "w").close()
    return True

def run_check():
    ts = datetime.now(timezone.utc).isoformat()
    rotated = []
    # Scan all .log files in memory/ tree
    log_files = glob.glob(os.path.join(LOG_DIR, "**", "*.log"), recursive=True)
    for lf in log_files:
        if rotate_file(lf):
            rotated.append(lf)
    status = f"rotated {len(rotated)} files" if rotated else "all logs under 10MB"
    print(f"{ts} [{status}]")
    for r in rotated:
        print(f"  rotated: {r}")
    return rotated

def main():
    mode = "--schedule" if "--schedule" in sys.argv else "--once"
    if mode == "--schedule":
        print(f"Log rotation scheduling every {INTERVAL_S}s...")
        while True:
            run_check()
            time.sleep(INTERVAL_S)
    else:
        run_check()

if __name__ == "__main__":
    main()