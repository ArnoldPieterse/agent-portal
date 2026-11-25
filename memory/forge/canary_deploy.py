#!/usr/bin/env python3
# canary_deploy.py - Canary deploy pipeline with smoke-gate + auto-rollback.
# Goal #2: deploys to one host first, runs smoke suite against that host only,
#          auto-promotes to remaining 3 on pass or auto-rollbacks on fail.
#
# Usage:
#   python memory/forge/canary_deploy.py <file> [host] [--dry-run] [--skip-smoke]
#
# Exit codes: 0 = success (promoted all), 1 = canary failed (rolled back),
#             2 = usage error, 3 = promotion failed (partial state)
import sys, os, json, time, subprocess, shutil, datetime, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SMOKE_SUITE = os.path.join(ROOT, "memory", "forge", "smoke_suite.py")
LOG_MD = os.path.join(ROOT, "memory", "forge", "log.md")
DEPLOY_LOG = os.path.join(ROOT, "memory", "forge", "deploy-log.jsonl")

HOSTS = ["White", "Red", "Pale", "Black"]
DEFAULT_CANARY = "White"  # local host first (fastest feedback)


def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg):
    line = "| " + now_iso() + " | canary_deploy: " + msg + " |"
    print(line, flush=True)
    try:
        with open(LOG_MD, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def append_deploy_log(entry):
    os.makedirs(os.path.dirname(DEPLOY_LOG), exist_ok=True)
    with open(DEPLOY_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def get_deploy_path(host, filename):
    """Return the target path on the given host."""
    if host == "White":
        # Local: deploy to the project root
        return os.path.join(ROOT, os.path.basename(filename))
    else:
        # Remote: standard deployment path on each host
        return r"C:\Projects\AgentPortal\\" + os.path.basename(filename)


def backup_file(host, target_path):
    """Create a .bak of the target file before overwriting. Returns backup path or None."""
    if not os.path.exists(target_path):
        return None
    bak = target_path + ".pre-canary.bak"
    shutil.copy2(target_path, bak)
    return bak


def deploy_to_host(source_file, host, dry_run=False):
    """Deploy a single file to one host. Returns (success, backup_path)."""
    target = get_deploy_path(host, source_file)
    if dry_run:
        print("  [DRY] Would copy %s -> %s (host=%s)" % (source_file, target, host))
        return True, None
    try:
        bak = backup_file(host, target)
        shutil.copy2(source_file, target)
        return True, bak
    except Exception as e:
        log("DEPLOY FAIL to %s: %s" % (host, e))
        return False, None


def rollback_host(host, source_file):
    """Restore .pre-canary.bak for a host. Returns True if rollback succeeded."""
    target = get_deploy_path(host, source_file)
    bak = target + ".pre-canary.bak"
    if not os.path.exists(bak):
        # No backup means file didn't exist before; delete it
        if os.path.exists(target):
            os.remove(target)
        return True
    try:
        shutil.copy2(bak, target)
        os.remove(bak)
        return True
    except Exception as e:
        log("ROLLBACK FAIL %s: %s" % (host, e))
        return False


def run_smoke_for_host(host, dry_run=False):
    """Run smoke suite against a single host. Returns True if pass."""
    cmd = [sys.executable, SMOKE_SUITE, "--host", host.lower(), "--no-remediate"]
    if dry_run:
        print("  [DRY] Would run: %s" % " ".join(cmd))
        return True
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    output = (r.stdout or "") + (r.stderr or "")
    if r.returncode == 0:
        print("  Smoke PASS for %s" % host)
        return True
    else:
        print("  Smoke FAIL for %s (rc=%d): %s" % (host, r.returncode, output[-300:]))
        return False


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: python memory/forge/canary_deploy.py <file> [host] [--dry-run] [--skip-smoke]")
        sys.exit(2)

    source_file = os.path.abspath(sys.argv[1])
    canary_host = DEFAULT_CANARY
    dry_run = "--dry-run" in sys.argv
    skip_smoke = "--skip-smoke" in sys.argv

    # Parse optional host arg
    for i, a in enumerate(sys.argv):
        if a not in ("--dry-run", "--skip-smoke") and i > 1:
            canary_host = a.capitalize()
            break

    if canary_host not in HOSTS:
        print("Unknown host: %s (valid: %s)" % (canary_host, ", ".join(HOSTS)))
        sys.exit(2)

    if not os.path.isfile(source_file):
        print("File not found: %s" % source_file)
        sys.exit(2)

    file_hash = sha256_file(source_file)
    fname = os.path.basename(source_file)
    ts_start = now_iso()
    promote_hosts = [h for h in HOSTS if h != canary_host]

    print("=== Canary Deploy: %s (sha=%s) ===" % (fname, file_hash))
    print("Canary host: %s | Promote to: %s" % (canary_host, promote_hosts))
    print("Mode: %s%s" % ("DRY-RUN " if dry_run else "", "| skip-smoke" if skip_smoke else ""))

    # Phase 1: Deploy to canary
    log("START canary=%s file=%s sha=%s" % (canary_host, fname, file_hash))
    print("\n[1/3] Deploying to canary: %s" % canary_host)
    ok, bak = deploy_to_host(source_file, canary_host, dry_run)
    if not ok:
        log("FAIL canary deploy to %s (no rollback needed)" % canary_host)
        append_deploy_log({"ts": ts_start, "file": fname, "sha": file_hash,
                           "canary": canary_host, "status": "canary_deploy_failed"})
        sys.exit(1)

    # Phase 2: Smoke gate on canary
    if not skip_smoke:
        print("\n[2/3] Running smoke gate on %s..." % canary_host)
        time.sleep(2)  # brief settle
        smoke_ok = run_smoke_for_host(canary_host, dry_run)
        if not smoke_ok:
            log("SMOKE FAIL on canary %s -> ROLLBACK" % canary_host)
            print("\n  SMOKE GATE FAILED - rolling back %s" % canary_host)
            rb_ok = rollback_host(canary_host, source_file)
            status = "canary_rolled_back" if rb_ok else "canary_rollback_failed"
            log("ROLLBACK %s -> %s" % (canary_host, "OK" if rb_ok else "FAILED"))
            append_deploy_log({"ts": ts_start, "file": fname, "sha": file_hash,
                               "canary": canary_host, "status": status})
            sys.exit(1)

    # Phase 3: Promote to remaining hosts
    print("\n[3/3] Promoting to: %s" % ", ".join(promote_hosts))
    promoted = []
    failed = []
    for h in promote_hosts:
        ok, _ = deploy_to_host(source_file, h, dry_run)
        if ok:
            promoted.append(h)
            print("  %s -> OK" % h)
        else:
            failed.append(h)
            print("  %s -> FAIL" % h)

    # If any promotion failed, rollback those that succeeded (keep atomicity)
    if failed and not dry_run:
        log("PROMOTION PARTIAL: ok=%s fail=%s -> rolling back promoted hosts" % (promoted, failed))
        print("\n  Partial failure detected. Rolling back promoted hosts...")
        for h in promoted:
            rollback_host(h, source_file)
        # Also rollback canary
        rollback_host(canary_host, source_file)
        append_deploy_log({"ts": ts_start, "file": fname, "sha": file_hash,
                           "canary": canary_host, "status": "promotion_partial_rollback",
                           "promoted": promoted, "failed": failed})
        sys.exit(3)

    # All good
    log("SUCCESS: %s deployed to all 4 hosts (canary=%s)" % (fname, canary_host))
    append_deploy_log({"ts": ts_start, "file": fname, "sha": file_hash,
                       "canary": canary_host, "status": "success",
                       "promoted": promote_hosts})
    print("\n=== DEPLOY SUCCESS: %s on all 4 hosts ===" % fname)
    sys.exit(0)


if __name__ == "__main__":
    main()
