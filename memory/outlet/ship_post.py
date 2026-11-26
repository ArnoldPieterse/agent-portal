#!/usr/bin/env python3
"""Outlet ship pipeline: takes an approved queue entry and publishes to a platform.

Companion to platform_connect.py (wiring) and queue_check.py (gate).
This is the final leg: approved -> shipped.

Subcommands:
  ship <queue-file> [--dry-run]    Ship a specific queue entry (must be status=approved)
  timeline                          Print shipment timeline log
  selftest                          Isolated proof: format parsing, gate enforcement, dry-run path

Secrets: reads memory/outlet/.secrets/<platform>.txt for app password (presence + value).
Bluesky API: https://bsky.app/xrpc/app.bsky.feed.post (AT Protocol).
"""
import argparse, json, os, pathlib, re, sys, datetime, urllib.request, urllib.error

HERE = pathlib.Path(__file__).resolve().parent  # memory/outlet
QUEUE = HERE / "queue"
SECRETS = HERE / ".secrets"
SHIP_LOG = HERE / "ship_log.jsonl"
BSKY_ENDPOINT = "https://bsky.app/xrpc/app.bsky.feed.post"


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _read_queue_file(path):
    """Parse a queue entry into a dict. Returns None if malformed."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    meta = {}
    body_match = re.search(r"## Body\s*\n(.+?)(?=\n## |\Z)", text, re.DOTALL)
    if not body_match:
        return None
    meta["body"] = body_match.group(1).strip()
    for line in text.splitlines():
        m = re.match(r"^(date|kind|platform|status|topic):\s*(.+)$", line.strip())
        if m:
            meta[m.group(1)] = m.group(2).strip()
    return meta


def _load_secret(platform):
    """Read app password from .secrets/<platform>.txt. Returns None if absent."""
    p = SECRETS / f"{platform}.txt"
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8").strip()


def _bsky_auth(handle, app_password):
    """Get a Bluesky access token via com.atproto.server.createSession."""
    url = "https://bsky.app/xrpc/com.atproto.server.createSession"
    payload = json.dumps({"identifier": handle, "password": app_password}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return data.get("accessJwt")


def _bsky_post(token, text):
    """Post a text post to Bluesky. Returns the URI of the created post."""
    payload = json.dumps({"text": text}).encode()
    req = urllib.request.Request(
        BSKY_ENDPOINT, data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return data.get("uri")


def ship(queue_file, dry_run=False):
    """Ship a single queue entry. Returns (success: bool, message: str)."""
    qpath = pathlib.Path(queue_file)
    if not qpath.exists():
        return False, f"Queue file not found: {queue_file}"

    meta = _read_queue_file(qpath)
    if meta is None:
        return False, "Malformed queue entry (no '## Body' section)"

    # Gate: must be approved
    status = meta.get("status", "").lower()
    if status != "approved":
        return False, f"Gate BLOCKED: status is '{status}', not 'approved'. Nothing ships without human approval."

    platform_raw = meta.get("platform", "")
    # Extract platform name (may be in parens or prefixed)
    plat_match = re.search(r"\b(bluesky|twitter|x|linkedin)\b", platform_raw, re.I)
    if not plat_match:
        return False, f"No recognized platform in '{platform_raw}'"
    platform = plat_match.group(1).lower()

    handle = meta.get("topic", "")  # fallback; real handle comes from profiles.md
    # Try to get handle from profiles.md for this platform
    profiles_text = (HERE / "profiles.md").read_text(encoding="utf-8") if (HERE / "profiles.md").exists() else ""
    handle_match = re.search(rf"\|[^|]*\|\s*{platform}\s*\|\s*@?([\w.]+)\s*\|", profiles_text, re.I)
    if handle_match:
        handle = f"@{handle_match.group(1)}"

    body = meta["body"]
    t_ship_start = _now()

    if dry_run:
        msg = (f"[DRY-RUN] Would ship to {platform} as {handle}:\n"
               f"  Body ({len(body)} chars): {body[:120]}...\n"
               f"  Status: OK (dry-run, no API call made)")
        _log_ship(qpath.name, platform, handle, body, t_ship_start, "dry-run", None)
        return True, msg

    # Real ship
    secret = _load_secret(platform)
    if not secret:
        return False, f"No secret found at {SECRETS / (platform + '.txt')}. Run platform_connect.py wired-check first."

    try:
        token = _bsky_auth(handle, secret)
        if not token:
            return False, "Authentication failed: no accessJwt returned"
        post_uri = _bsky_post(token, body)
        t_ship_done = _now()
        _log_ship(qpath.name, platform, handle, body, t_ship_start, "shipped", post_uri)

        # Update queue file status
        text = qpath.read_text(encoding="utf-8")
        text = re.sub(r"^status:\s*.+$", f"status: shipped ({t_ship_done})", text, flags=re.MULTILINE)
        qpath.write_text(text, encoding="utf-8")

        return True, f"Shipped to {platform} as {handle}: {post_uri}"
    except urllib.error.HTTPError as e:
        return False, f"API error {e.code}: {e.read().decode()[:200]}"
    except Exception as e:
        return False, f"Ship failed: {type(e).__name__}: {e}"


def _log_ship(queue_name, platform, handle, body, t_start, result, post_uri):
    """Append to ship_log.jsonl."""
    entry = {
        "ts": _now(), "queue": queue_name, "platform": platform,
        "handle": handle, "body_len": len(body), "result": result,
        "t_start": t_start, "post_uri": post_uri
    }
    SHIP_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(SHIP_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def timeline():
    """Print shipment timeline from ship_log.jsonl."""
    if not SHIP_LOG.exists():
        print("No shipments logged yet.")
        return
    lines = SHIP_LOG.read_text(encoding="utf-8").strip().splitlines()
    print(f"{'TIMESTAMP':<28} {'QUEUE FILE':<45} {'PLATFORM':<10} {'RESULT':<10}")
    print("-" * 93)
    for ln in lines:
        try:
            e = json.loads(ln)
            print(f"{e['ts']:<28} {e['queue']:<45} {e['platform']:<10} {e['result']:<10}")
        except (json.JSONDecodeError, KeyError):
            pass
    print(f"\nTotal shipments: {len(lines)}")


def selftest():
    """Isolated proof: format parsing, gate enforcement, dry-run path."""
    import tempfile, shutil
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="ship_test_"))
    results = []
    try:
        # Test 1: parse a valid queue entry
        test_entry = tmp / "test-post.md"
        test_entry.write_text(
            "# Staged post: Test\ndate: 2026-11-27\nkind: upload\n"
            "platform: bluesky\nstatus: approved\ntopic: Test post\n\n"
            "## Body\nThis is a test body for the ship pipeline.\n\n"
            "## Rationale\n- Testing\n",
            encoding="utf-8"
        )
        meta = _read_queue_file(test_entry)
        ok = meta is not None and meta["status"] == "approved" and "test body" in meta["body"]
        results.append(("parse_valid", ok))

        # Test 2: gate blocks non-approved
        blocked_entry = tmp / "blocked.md"
        blocked_entry.write_text(
            "# Staged post: Blocked\ndate: 2026-11-27\nkind: upload\n"
            "platform: bluesky\nstatus: ready-for-human\ntopic: Should not ship\n\n"
            "## Body\nThis should be blocked.\n",
            encoding="utf-8"
        )
        bmeta = _read_queue_file(blocked_entry)
        ok = bmeta is not None and bmeta["status"] != "approved"
        results.append(("gate_blocks_unapproved", ok))

        # Test 3: ship() rejects non-approved (calls the actual gate)
        success, msg = ship(str(blocked_entry), dry_run=True)
        ok = not success and "Gate BLOCKED" in msg
        results.append(("ship_rejects_unapproved", ok))

        # Test 4: ship() dry-run succeeds for approved (no secret needed for dry-run)
        success, msg = ship(str(test_entry), dry_run=True)
        ok = success and "DRY-RUN" in msg
        results.append(("ship_dry_run_ok", ok))

        # Test 5: missing file handled gracefully
        success, msg = ship(str(tmp / "nonexistent.md"), dry_run=True)
        ok = not success and "not found" in msg.lower()
        results.append(("missing_file_graceful", ok))

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


def main():
    ap = argparse.ArgumentParser(description="Outlet ship pipeline")
    sub = ap.add_subparsers(dest="cmd")

    p_ship = sub.add_parser("ship", help="Ship an approved queue entry")
    p_ship.add_argument("queue_file", help="Path to queue .md file")
    p_ship.add_argument("--dry-run", action="store_true", help="Simulate without API call")

    sub.add_parser("timeline", help="Print shipment log")
    sub.add_parser("selftest", help="Isolated test (no network)")

    args = ap.parse_args()
    if args.cmd == "ship":
        ok, msg = ship(args.queue_file, dry_run=args.dry_run)
        print(msg)
        sys.exit(0 if ok else 1)
    elif args.cmd == "timeline":
        timeline()
    elif args.cmd == "selftest":
        ok = selftest()
        sys.exit(0 if ok else 1)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
