"""hotpatch.py - Hot-patch agent_portal.py with auto-rollback.

Usage:
  python memory/builder/hotpatch.py <diff_file> [--dry-run]

Applies a single-hunk unified diff to agent_portal.py, runs smoke checks,
auto-restores on failure. No process restart required (portal re-reads file).

Acceptance test: apply deliberately broken patch -> rollback fires, original restored.
"""
import sys, os, shutil, subprocess, time, json, difflib

PORTAL = "agent_portal.py"
EVENTS = os.path.join("memory", "ops", "hotpatch-events.jsonl")
BACKUP_DIR = os.path.join("memory", "builder", "backups")
SMOKE_TIMEOUT = 30  # seconds max for rollback


def parse_unified_diff(diff_text):
    """Parse a minimal unified diff into (old_lines, new_lines, start_line)."""
    lines = diff_text.strip().split("\n")
    # Find the hunk header: @@ -a,b +c,d @@
    hunk_start = None
    for i, line in enumerate(lines):
        if line.startswith("@@"):
            hunk_start = i
            break
    if hunk_start is None:
        raise ValueError("No @@ hunk found in diff")

    # Parse old start from header (e.g., @@ -5,3 +5,4 @@)
    import re
    m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", lines[hunk_start])
    if not m:
        raise ValueError(f"Bad hunk header: {lines[hunk_start]}")
    old_start = int(m.group(1))  # 1-based

    old_lines = []
    new_lines = []
    for line in lines[hunk_start + 1:]:
        if line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("-"):
            old_lines.append(line[1:])
        elif line.startswith("+"):
            new_lines.append(line[1:])
        elif line.startswith(" "):
            old_lines.append(line[1:])
            new_lines.append(line[1:])
        elif "\\" in line:  # No-newline marker
            continue
        else:
            break  # end of hunk

    return old_start, old_lines, new_lines


def apply_patch(target_path, diff_text):
    """Apply a single-hunk unified diff. Returns (success, error_msg)."""
    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.split("\n")

    old_start, old_lines, new_lines = parse_unified_diff(diff_text)
    # Convert to 0-based
    idx = old_start - 1

    # Verify the old lines match at the expected position
    actual_old = lines[idx:idx + len(old_lines)]
    if actual_old != old_lines:
        return False, (f"Mismatch at line {old_start}:\n"
                       f"Expected: {old_lines[:3]}...\n"
                       f"Got:      {actual_old[:3]}...")

    # Replace
    lines[idx:idx + len(old_lines)] = new_lines
    with open(target_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return True, None


def run_smoke():
    """Quick smoke: syntax check the patched file. Returns (pass, detail)."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import py_compile; py_compile.compile('{PORTAL}', doraise=True)"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return True, "syntax OK"
        return False, f"syntax error: {result.stderr.strip()[:200]}"
    except subprocess.TimeoutExpired:
        return False, "smoke test timed out"


def rollback(backup_path, target_path):
    """Restore from backup. Returns elapsed seconds."""
    t0 = time.time()
    shutil.copy2(backup_path, target_path)
    return time.time() - t0


def log_event(event_type, detail, target=PORTAL):
    os.makedirs(os.path.dirname(EVENTS), exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "type": event_type,
        "target": target,
        "detail": detail
    }
    with open(EVENTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python hotpatch.py <diff_file> [--dry-run]")
        sys.exit(1)

    diff_file = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    with open(diff_file, "r", encoding="utf-8") as f:
        diff_text = f.read()

    if dry_run:
        print(f"[DRY-RUN] Would patch {PORTAL} with hunk from {diff_file}")
        old_start, old_lines, new_lines = parse_unified_diff(diff_text)
        print(f"  Hunk at line {old_start}: removing {len(old_lines)} lines, adding {len(new_lines)}")
        sys.exit(0)

    # Backup
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_path = os.path.join(BACKUP_DIR, f"{os.path.basename(PORTAL)}.{int(time.time())}.bak")
    shutil.copy2(PORTAL, backup_path)

    # Apply
    ok, err = apply_patch(PORTAL, diff_text)
    if not ok:
        log_event("patch-fail", err)
        print(f"PATCH FAILED (no change made): {err}")
        sys.exit(1)

    print(f"Patched {PORTAL} (backup: {os.path.relpath(backup_path)})")

    # Smoke test
    smoke_ok, smoke_detail = run_smoke()
    if smoke_ok:
        log_event("patch-ok", smoke_detail)
        print(f"SMOKE PASS: {smoke_detail}")
        sys.exit(0)
    else:
        # Auto-rollback
        elapsed = rollback(backup_path, PORTAL)
        log_event("patch-rollback", f"{smoke_detail} | restored in {elapsed:.1f}s")
        print(f"SMOKE FAIL: {smoke_detail}")
        print(f"ROLLBACK: original restored in {elapsed:.1f}s (< {SMOKE_TIMEOUT}s)")
        sys.exit(2)


if __name__ == "__main__":
    main()
