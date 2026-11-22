"""Log Rotation + Retention - rotates .jsonl/.log files >50MB, keeps 7 days, compresses old.
Usage: python memory/mechanic/log_rotate.py [--once | --schedule]"""
import os, sys, time, glob, gzip, shutil
from datetime import datetime, timezone, timedelta

# Scan the full fleet tree (project root, parent of memory/)
# __file__ = <root>/memory/mechanic/log_rotate.py
# dirname x3 from file: mechanic -> memory -> <root>
FLEET_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAX_SIZE = 50 * 1024 * 1024  # 50MB per goal spec
RETENTION_DAYS = 7
INTERVAL_S = 3600  # hourly when --schedule

def rotate_file(path):
    """Rotate a single log file (>MAX_SIZE). Returns True if rotated."""
    if not os.path.exists(path) or os.path.getsize(path) < MAX_SIZE:
        return False
    ts_tag = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    compressed = path + f".{ts_tag}.gz"
    with open(path, "rb") as f_in:
        with gzip.open(compressed, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    # Truncate the live file (keep it for appenders that hold an open handle)
    open(path, "w").close()
    return True

def compress_old_files():
    """Compress .log/.jsonl files older than RETENTION_DAYS. Returns count."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    compressed = 0
    for pattern in ("**/*.log", "**/*.jsonl"):
        for fpath in glob.glob(os.path.join(FLEET_ROOT, pattern), recursive=True):
            if _is_rotated_artifact(fpath):
                continue
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(fpath), tz=timezone.utc)
            except OSError:
                continue
            if mtime < cutoff and os.path.getsize(fpath) > 0:
                gz_path = fpath + ".gz"
                with open(fpath, "rb") as f_in:
                    with gzip.open(gz_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(fpath)
                compressed += 1
    return compressed

def _is_rotated_artifact(path):
    """True if path is a rotation output (e.g. foo.jsonl.20261122_102305.gz)."""
    name = os.path.basename(path)
    return name.endswith(".gz")

def run_check():
    ts = datetime.now(timezone.utc).isoformat()
    rotated = []
    # Scan all .log and .jsonl files in fleet tree
    patterns = ("**/*.log", "**/*.jsonl")
    for pattern in patterns:
        for lf in glob.glob(os.path.join(FLEET_ROOT, pattern), recursive=True):
            if _is_rotated_artifact(lf):
                continue
            if rotate_file(lf):
                rotated.append(lf)
    compressed = compress_old_files()
    status = f"rotated={len(rotated)} compressed_old={compressed}"
    print(f"{ts} [{status}] max={MAX_SIZE//1024//1024}MB retention={RETENTION_DAYS}d")
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