"""Fleet Backup Automation - nightly backup of critical state with 7-day rotation.
Usage: python memory/mechanic/backup.py --run [--restore <date>]
Backs up: agents.json, memory/ dir, TODO.md, agent_portal.py
Output: memory/mechanic/backups/fleet-backup-<YYYY-MM-DD_HHMMSS>.tar.gz
Rotation: keeps 7 most recent; 8th oldest auto-deleted."""
import os, sys, tarfile, json, shutil, glob
from datetime import datetime, timezone
from pathlib import Path

BACKUP_DIR = Path(__file__).parent / "backups"
ROTATION_KEEP = 7  # keep 7 most recent backups

# Files/dirs to back up (relative to project root)
CRITICAL_FILES = [
    "agents.json",
    "TODO.md",
    "agent_portal.py",
    "memory/",
]

def get_project_root():
    """Find the project root (parent of memory/)."""
    return Path(__file__).parent.parent.parent

def create_backup():
    """Create a new backup tar.gz. Returns path to created archive."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    root = get_project_root()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    archive_path = BACKUP_DIR / f"fleet-backup-{ts}.tar.gz"
    
    with tarfile.open(archive_path, "w:gz") as tar:
        for item in CRITICAL_FILES:
            full_path = root / item
            if full_path.exists():
                # Add with arcname relative to project root
                tar.add(str(full_path), arcname=item.rstrip("/"))
    
    return archive_path

def list_backups():
    """List all backups sorted oldest first."""
    files = sorted(BACKUP_DIR.glob("fleet-backup-*.tar.gz"))
    return files

def rotate_backups():
    """Delete backups beyond ROTATION_KEEP. Returns list of deleted paths."""
    backups = list_backups()
    if len(backups) <= ROTATION_KEEP:
        return []
    to_delete = backups[:len(backups) - ROTATION_KEEP]
    for b in to_delete:
        b.unlink()
    return [str(b) for b in to_delete]

def restore(archive_path):
    """Restore from a backup archive. Returns True on success."""
    if not os.path.exists(archive_path):
        # Try to find by date pattern
        root = get_project_root()
        candidates = list(BACKUP_DIR.glob(f"fleet-backup-{archive_path}*.tar.gz"))
        if len(candidates) == 1:
            archive_path = str(candidates[0])
        elif not candidates:
            print(f"ERROR: No backup found matching '{archive_path}'")
            return False
        else:
            archive_path = str(candidates[-1])  # most recent match
    
    with tarfile.open(archive_path, "r:gz") as tar:
        root = get_project_root()
        tar.extractall(path=str(root))
    return True

def main():
    if "--restore" in sys.argv:
        idx = sys.argv.index("--restore")
        if idx + 1 < len(sys.argv):
            date_str = sys.argv[idx + 1]
            # Construct the backup path from date
            archive_path = BACKUP_DIR / f"fleet-backup-{date_str}"
            # Try exact match first, then glob
            if not archive_path.exists():
                candidates = sorted(BACKUP_DIR.glob(f"fleet-backup-*{date_str}*"))
                if candidates:
                    archive_path = candidates[-1]
                else:
                    # Maybe it's a full filename
                    archive_path = Path(date_str)
            ok = restore(str(archive_path))
            print(f"Restore {'SUCCESS' if ok else 'FAILED'}: {archive_path}")
            sys.exit(0 if ok else 1)
        else:
            print("ERROR: --restore requires a date argument (YYYY-MM-DD or YYYY-MM-DD_HHMMSS)")
            sys.exit(1)
    
    elif "--run" in sys.argv:
        archive = create_backup()
        deleted = rotate_backups()
        size_mb = os.path.getsize(archive) / (1024*1024)
        ts = datetime.now(timezone.utc).isoformat()
        print(f"{ts} BACKUP OK: {archive.name} ({size_mb:.2f} MB)")
        if deleted:
            for d in deleted:
                print(f"  rotated out: {os.path.basename(d)}")
        # Write metadata
        meta = {
            "timestamp": ts,
            "archive": str(archive),
            "size_bytes": os.path.getsize(archive),
            "files_included": CRITICAL_FILES,
            "rotation_deleted": deleted,
        }
        meta_path = archive.with_suffix(".json")
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
    
    elif "--list" in sys.argv:
        backups = list_backups()
        if not backups:
            print("No backups found.")
        else:
            for i, b in enumerate(backups):
                size = os.path.getsize(b) / (1024*1024)
                print(f"  [{i+1}] {b.name} ({size:.2f} MB)")
    
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
