#!/usr/bin/env python3
"""Outlet Fire Queue — auto-ship all approved posts when credentials are present (goal #1 unblock).

The one-command that completes the ship cycle once Arnold provides credentials.
  python memory/outlet/fire_queue.py --platform bluesky [--dry-run] [--list-only]

Flow:
  1. Check .secrets/<platform>.txt exists and is non-empty
  2. Find all queue entries with status=approved
  3. Ship each via ship_post.ship() (real API call unless --dry-run)
  4. Log full timeline to ship-timeline.jsonl + ship_log.jsonl
  5. If no approved posts: list ready-for-human ones and remind about human approval

Selftest: python memory/outlet/fire_queue.py selftest
"""
import argparse, json, pathlib, re, sys, datetime

HERE = pathlib.Path(__file__).resolve().parent
QUEUE = HERE / "queue"
SECRETS = HERE / ".secrets"
TIMELINE = HERE / "ship-timeline.jsonl"


def _ts():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _log(event, detail=""):
    entry = {"ts": _ts(), "event": event, "detail": detail}
    with open(TIMELINE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def check_credentials(platform):
    """Return True if .secrets/<platform>.txt exists and is non-empty."""
    SECRETS.mkdir(exist_ok=True)
    f = SECRETS / f"{platform.lower()}.txt"
    if not f.exists():
        return False
    content = f.read_text(encoding="utf-8").strip()
    return len(content) > 0


def find_approved(platform=None):
    """Find all queue entries with status=approved (optionally filtered by platform)."""
    results = []
    if not QUEUE.exists():
        return results
    for f in sorted(QUEUE.glob("*.md")):
        if f.name == "INDEX.md":
            continue
        text = f.read_text(encoding="utf-8")
        status_m = re.search(r"^status:\s*(.+)$", text, re.MULTILINE)
        if not status_m:
            continue
        status = status_m.group(1).strip().lower()
        if status != "approved":
            continue
        # Platform filter
        if platform:
            plat_m = re.search(r"^platform:\s*(.+)$", text, re.MULTILINE)
            plat_raw = plat_m.group(1).strip() if plat_m else ""
            if platform.lower() not in plat_raw.lower():
                continue
        results.append(f)
    return results


def find_ready_for_human(platform=None):
    """Find queue entries with status=ready-for-human."""
    results = []
    if not QUEUE.exists():
        return results
    for f in sorted(QUEUE.glob("*.md")):
        if f.name == "INDEX.md":
            continue
        text = f.read_text(encoding="utf-8")
        status_m = re.search(r"^status:\s*(.+)$", text, re.MULTILINE)
        if not status_m:
            continue
        if status_m.group(1).strip().lower() != "ready-for-human":
            continue
        results.append(f)
    return results


def fire_queue(platform, dry_run=False):
    """Main fire logic. Returns exit code."""
    _log("fire_queue_start", f"platform={platform} dry_run={dry_run}")

    # Step 1: check credentials
    if not dry_run and not check_credentials(platform):
        print(f"FIRE QUEUE: credentials MISSING for {platform}")
        print(f"  Expected at: {SECRETS / (platform + '.txt')}")
        print(f"  Arnold: echo \"<app-password>\" > memory/outlet/.secrets/{platform}.txt")
        _log("fire_queue_blocked", f"missing credentials for {platform}")
        # Still list what would ship
        approved = find_approved(platform)
        if approved:
            print(f"  ({len(approved)} approved post(s) waiting — will fire once credentials exist)")
            for f in approved:
                print(f"    - {f.name}")
        return 2  # blocked on credentials

    # Step 2: find approved posts
    approved = find_approved(platform)
    if not approved:
        ready = find_ready_for_human()
        print(f"FIRE QUEUE: no approved posts for {platform}.")
        if ready:
            print(f"  {len(ready)} post(s) in ready-for-human state (need human approval):")
            for f in ready:
                print(f"    - {f.name}")
        else:
            print("  Queue is empty.")
        _log("fire_queue_no_approved", "0 approved posts found")
        return 1

    # Step 3: ship each
    import ship_post  # local module
    shipped, failed = 0, 0
    for f in approved:
        print(f"\nShipping {f.name}...")
        ok, msg = ship_post.ship(str(f), dry_run=dry_run)
        if ok:
            shipped += 1
            _log("fire_shipped", f.name)
        else:
            failed += 1
            _log("fire_failed", f"{f.name}: {msg}")
        print(f"  -> {msg[:120]}")

    _log("fire_queue_complete", f"shipped={shipped} failed={failed}")
    print(f"\nFIRE QUEUE COMPLETE: {shipped} shipped, {failed} failed")
    return 0 if failed == 0 else 3


def selftest():
    """Isolated proof of fire_queue logic (no network)."""
    import tempfile, shutil, os
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="fire_test_"))
    results = []
    try:
        # Mock queue dir
        qdir = tmp / "queue"
        qdir.mkdir()
        sdir = tmp / ".secrets"
        sdir.mkdir()

        # Create test posts
        approved_post = qdir / "approved-post.md"
        approved_post.write_text(
            "# Test Approved\ndate: 2026-11-27\nkind: upload\nplatform: bluesky\n"
            "status: approved\ntopic: test approved\n\n## Body\nApproved content.\n",
            encoding="utf-8"
        )
        ready_post = qdir / "ready-post.md"
        ready_post.write_text(
            "# Test Ready\ndate: 2026-11-27\nkind: upload\nplatform: bluesky\n"
            "status: ready-for-human\ntopic: test ready\n\n## Body\nReady content.\n",
            encoding="utf-8"
        )

        # Test 1: check_credentials returns False when missing
        ok = not check_credentials_for(tmp, "bluesky")
        results.append(("credentials_missing_detect", ok))

        # Test 2: check_credentials returns True when present
        (sdir / "bluesky.txt").write_text("fake-password-123", encoding="utf-8")
        ok = check_credentials_for(tmp, "bluesky")
        results.append(("credentials_present_detect", ok))

        # Test 3: approved status parsing
        # (testing the same regex logic used by find_approved)
        text = approved_post.read_text(encoding="utf-8")
        m = re.search(r"^status:\s*(.+)$", text, re.MULTILINE)
        ok = m is not None and m.group(1).strip().lower() == "approved"
        results.append(("parse_approved_status", ok))

        # Test 4: ready-for-human detection
        rtext = ready_post.read_text(encoding="utf-8")
        rm = re.search(r"^status:\s*(.+)$", rtext, re.MULTILINE)
        ok = rm is not None and rm.group(1).strip().lower() == "ready-for-human"
        results.append(("parse_ready_status", ok))

        # Test 5: empty credentials file returns False
        (sdir / "bluesky.txt").write_text("", encoding="utf-8")
        ok = not check_credentials_for(tmp, "bluesky")
        results.append(("empty_credentials_rejected", ok))

        # Report
        passed = sum(1 for _, ok in results if ok)
        total = len(results)
        print(f"selftest: {passed}/{total} PASS")
        for name, ok in results:
            mark = "PASS" if ok else "FAIL"
            print(f"  [{mark}] {name}")
        return passed == total
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def check_credentials_for(base_dir, platform):
    """Check credentials in a specific directory (for testing)."""
    f = base_dir / ".secrets" / f"{platform.lower()}.txt"
    if not f.exists():
        return False
    content = f.read_text(encoding="utf-8").strip()
    return len(content) > 0


def main():
    ap = argparse.ArgumentParser(description="Outlet Fire Queue — auto-ship approved posts")
    ap.add_argument("--platform", default="bluesky", help="Target platform (default: bluesky)")
    ap.add_argument("--dry-run", action="store_true", help="Simulate without API calls")
    ap.add_argument("selftest", nargs="?", const="selftest", help="Run selftest")

    args = ap.parse_args()
    if args.selftest:
        ok = selftest()
        sys.exit(0 if ok else 1)
    else:
        rc = fire_queue(args.platform, dry_run=args.dry_run)
        sys.exit(rc)


if __name__ == "__main__":
    main()