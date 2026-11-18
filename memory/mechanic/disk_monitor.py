#!/usr/bin/env python3
"""
Disk Space Monitor + Auto-Clean
Goal #4 - mechanic lane

Checks disk usage; if >85% auto-cleans (__pycache__, old logs >7d, temp files).
Alerts if still >90% after clean. Never deletes .md or .json in memory/.

Usage:
  python memory/mechanic/disk_monitor.py            # single check
  python memory/mechanic/disk_monitor.py --clean    # force clean regardless of threshold
  python memory/mechanic/disk_monitor.py --schedule # register 30-min schtask
"""
import os, sys, json, shutil, time, logging, argparse, glob
from datetime import datetime, timedelta
from pathlib import Path

LOG_FILE = Path(__file__).parent / "disk_monitor.log"
ALERT_FILE = Path(__file__).parent / "health_alerts.jsonl"
THRESHOLD_CLEAN = 85   # percent
THRESHOLD_ALERT = 90   # percent
LOG_AGE_DAYS = 7

# Safety: NEVER delete these patterns in memory/
PROTECTED_EXT = {'.md', '.json'}
PROTECTED_DIR_PREFIXES = ('memory/',)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [disk_monitor] %(levelname)s: %(message)s',
        handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
    )

def get_disk_pct(drive_letter=None):
    """Return disk usage percentage for the given drive (default: cwd's drive)."""
    if drive_letter is None:
        # Use the drive of the current working directory
        cwd = os.path.abspath('.')
        drive_letter = cwd[0] + ':'
    try:
        usage = shutil.disk_usage(drive_letter)
        return round(usage.used / usage.total * 100, 1)
    except Exception as e:
        # Fallback: check the root of cwd
        try:
            usage = shutil.disk_usage(os.path.abspath('.'))
            return round(usage.used / usage.total * 100, 1)
        except Exception as e2:
            logging.error(f"Failed to check disk: {e} / {e2}")
            return -1

def find_cleanable_files(root=None):
    """Find files/dirs safe to clean. Returns list of (path, reason)."""
    if root is None:
        root = Path(os.getcwd())
    cleanable = []
    cutoff = datetime.now() - timedelta(days=LOG_AGE_DAYS)

    for dirpath, dirnames, filenames in os.walk(root):
        # Skip protected directories entirely
        rel = os.path.relpath(dirpath, root)
        if any(rel.startswith(p) or p.split('/')[0] in rel.split(os.sep) for p in PROTECTED_DIR_PREFIXES):
            # In memory/ we only clean __pycache__ and .log files >7d
            pass
        else:
            # Outside protected: can clean __pycache__ dirs
            if '__pycache__' in dirnames:
                pycache_path = os.path.join(dirpath, '__pycache__')
                cleanable.append((pycache_path, 'pycache_dir'))
                dirnames.remove('__pycache__')  # don't descend

        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            ext = Path(fname).suffix.lower()
            rel = os.path.relpath(fpath, root)

            # NEVER delete .md or .json in memory/
            if 'memory' in rel.split(os.sep) and ext in PROTECTED_EXT:
                continue

            # Clean __pycache__ files (shouldn't reach here due to dir skip, but safety)
            if '__pycache__' in dirpath:
                cleanable.append((fpath, 'pycache_file'))
                continue

            # Old log files >7 days
            if ext == '.log':
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                    if mtime < cutoff:
                        cleanable.append((fpath, f'old_log_{(datetime.now()-mtime).days}d'))
                except OSError:
                    pass

            # Temp files: *.tmp, *.temp, *~ (backup)
            if fname.endswith('.tmp') or fname.endswith('.temp') or fname.endswith('~'):
                cleanable.append((fpath, 'temp_file'))

    return cleanable

def perform_clean(cleanable):
    """Remove identified files/dirs. Returns bytes freed and items removed."""
    freed = 0
    removed = []
    for path, reason in cleanable:
        try:
            if os.path.isdir(path):
                size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fns in os.walk(path) for f in fns)
                shutil.rmtree(path)
                freed += size
                removed.append(f"{path} ({reason})")
            elif os.path.isfile(path):
                size = os.path.getsize(path)
                os.remove(path)
                freed += size
                removed.append(f"{path} ({reason})")
        except Exception as e:
            logging.warning(f"Failed to remove {path}: {e}")
    return freed, removed

def alert(msg):
    """Append alert to health_alerts.jsonl."""
    entry = {
        'ts': datetime.now().isoformat(),
        'source': 'disk_monitor',
        'severity': 'ALERT' if THRESHOLD_ALERT else 'WARN',
        'msg': msg
    }
    with open(ALERT_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')
    logging.warning(f"ALERT: {msg}")

def run_check(force_clean=False):
    """Main check cycle. Returns dict of results."""
    pct = get_disk_pct()
    result = {
        'ts': datetime.now().isoformat(),
        'disk_pct': pct,
        'action': 'none',
        'cleaned_items': 0,
        'bytes_freed': 0,
        'alert': False
    }

    if pct < 0:
        result['action'] = 'error'
        return result

    should_clean = force_clean or (pct >= THRESHOLD_CLEAN)

    if should_clean:
        cleanable = find_cleanable_files()
        if cleanable:
            freed, removed = perform_clean(cleanable)
            result['action'] = 'cleaned'
            result['cleaned_items'] = len(removed)
            result['bytes_freed'] = freed
            logging.info(f"Cleaned {len(removed)} items, freed {freed/1024:.1f} KB")
        else:
            result['action'] = 'no_cleanable'
            logging.info("No cleanable files found")

    # Re-check after clean
    new_pct = get_disk_pct()
    result['disk_pct_after'] = new_pct

    if new_pct >= THRESHOLD_ALERT:
        result['alert'] = True
        alert(f"Disk still at {new_pct}% after auto-clean (threshold {THRESHOLD_ALERT}%)")

    return result

def register_schedule():
    """Register a 30-minute schtask for disk monitoring."""
    import subprocess
    script = os.path.abspath(__file__)
    python = sys.executable
    task_name = 'Mechanic_DiskMonitor'
    cmd = [
        'schtasks', '/create', '/tn', task_name,
        '/tr', f'"{python}" "{script}"',
        '/sc', 'minute', '/mo', '30',
        '/f'
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        logging.info(f"Registered schtask: {task_name} (every 30 min)")
        return True
    else:
        logging.error(f"Failed to register schtask: {r.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Disk Space Monitor + Auto-Clean')
    parser.add_argument('--clean', action='store_true', help='Force clean regardless of threshold')
    parser.add_argument('--schedule', action='store_true', help='Register 30-min schtask')
    args = parser.parse_args()

    setup_logging()

    if args.schedule:
        ok = register_schedule()
        sys.exit(0 if ok else 1)

    result = run_check(force_clean=args.clean)
    print(json.dumps(result, indent=2))
    # Exit code: 0=ok, 1=alert, 2=error
    if result.get('alert'):
        sys.exit(1)
    elif result['action'] == 'error':
        sys.exit(2)
    sys.exit(0)

if __name__ == '__main__':
    main()
