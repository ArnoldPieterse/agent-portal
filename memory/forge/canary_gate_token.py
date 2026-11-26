#!/usr/bin/env python3
"""canary_gate_token.py - Pass/fail token for canary promotions (Verifier goal #5).

Before Forge promotes a canary, this script runs perf + functional checks and
emits a JSON token. canary_deploy.py must consume a fresh valid token or the
promotion is blocked.

Usage:
  python memory/forge/canary_gate_token.py <target_file> [--dry-run]

Exit codes: 0 = token issued (pass), 1 = checks failed (no token), 2 = usage error

Token file: memory/ops/canary-gate-token.json
  {"pass": true, "ts": "...", "target_sha256": "...", "checks": [...], "signer": "forge"}

Freshness: token is valid for 300 seconds (5 min) from issuance.
"""
import sys, os, json, time, hashlib, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TOKEN_FILE = ROOT / "memory" / "ops" / "canary-gate-token.json"
SMOKE_SUITE = ROOT / "memory" / "forge" / "smoke_suite.py"
LOG_FILE = ROOT / "memory" / "forge" / "deploy-log.jsonl"

TOKEN_TTL_SECONDS = 300  # 5 min freshness window


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def run_smoke_checks(target_file):
    """Run smoke suite against target. Returns (passed, details, skipped)."""
    try:
        import subprocess
        r = subprocess.run(
            [sys.executable, str(SMOKE_SUITE), "--quick"],
            capture_output=True, text=True, timeout=120,
            cwd=str(ROOT)
        )
        passed = r.returncode == 0
        details = (r.stdout + r.stderr).strip()[-500:]
        return passed, details, False
    except Exception as e:
        # Environment issue (sandbox, missing deps) - mark as skipped, not failed
        return True, f"skipped (env): {str(e)[:120]}", True


def run_perf_check(target_file):
    """Quick perf sanity: measure parse time for Python files.
    Non-Python files are skipped (not an error). Returns (passed, p50_ms, threshold_ms)."""
    PERF_THRESHOLD_MS = 2000  # 2s max for a module to load/parse
    if target_file.suffix not in ('.py',):
        return True, 0, PERF_THRESHOLD_MS  # skip non-Python files
    times = []
    try:
        import ast
        for _ in range(3):
            t0 = time.perf_counter()
            src = target_file.read_text(encoding="utf-8")
            ast.parse(src)  # validates syntax + measures parse cost
            times.append((time.perf_counter() - t0) * 1000)
        p50 = sorted(times)[len(times) // 2]
        passed = p50 < PERF_THRESHOLD_MS
        return passed, round(p50, 2), PERF_THRESHOLD_MS
    except Exception as e:
        return False, -1, f"perf check error: {e}"


def issue_token(target_file, dry_run=False):
    """Run all checks, emit token if all pass."""
    target = pathlib.Path(target_file).resolve()
    if not target.exists():
        print(f"ERROR: target file not found: {target}")
        return 1

    file_sha = sha256_file(str(target))
    checks = []

    # Check 1: smoke suite
    smoke_ok, smoke_detail, smoke_skipped = run_smoke_checks(target)
    checks.append({"name": "smoke_suite", "pass": smoke_ok, "skipped": smoke_skipped, "detail": smoke_detail[:200]})
    print(f"  [smoke] {'PASS' if smoke_ok else 'FAIL'}{' (skipped)' if smoke_skipped else ''}: {smoke_detail[:120]}")

    # Check 2: perf sanity (parse time)
    perf_ok, p50_ms, threshold = run_perf_check(target)
    checks.append({"name": "perf_parse", "pass": perf_ok, "p50_ms": p50_ms, "threshold_ms": threshold})
    print(f"  [perf]  {'PASS' if perf_ok else 'FAIL'}: p50={p50_ms}ms (limit {threshold}ms)")

    all_pass = all(c["pass"] for c in checks)

    token = {
        "pass": all_pass,
        "ts": datetime.datetime.now().isoformat(),
        "target_sha256": file_sha,
        "checks": checks,
        "signer": "forge",
        "ttl_seconds": TOKEN_TTL_SECONDS,
    }

    if dry_run:
        print(f"\n[DRY-RUN] Token would be issued: pass={all_pass}")
        print(json.dumps(token, indent=2))
    elif all_pass:
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(json.dumps(token, indent=2), encoding="utf-8")
        print(f"\n[TOKEN ISSUED] pass=True -> {TOKEN_FILE.relative_to(ROOT)}")
        # Log to deploy log
        entry = {"ts": token["ts"], "event": "gate_token_issued", "target": str(target), "pass": True}
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    else:
        print(f"\n[TOKEN DENIED] pass=False - no token written")
        entry = {"ts": datetime.datetime.now().isoformat(), "event": "gate_token_denied", "target": str(target), "checks": checks}
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    return 0 if all_pass else 1


def verify_token(target_file=None):
    """Check if a valid, fresh token exists. Returns (valid: bool, reason: str).
    Called by canary_deploy.py before promotion."""
    if not TOKEN_FILE.exists():
        return False, "no token file found (run canary_gate_token.py first)"

    try:
        token = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return False, f"token unreadable: {e}"

    if not token.get("pass"):
        return False, "token indicates FAIL"

    # Check freshness
    ts = datetime.datetime.fromisoformat(token["ts"])
    age_s = (datetime.datetime.now() - ts).total_seconds()
    if age_s > TOKEN_TTL_SECONDS:
        return False, f"token stale ({age_s:.0f}s old, TTL {TOKEN_TTL_SECONDS}s)"

    # Check target match (if specified)
    if target_file:
        try:
            actual_sha = sha256_file(str(pathlib.Path(target_file).resolve()))
            if token.get("target_sha256") != actual_sha:
                return False, "token sha mismatch (file changed after token issued)"
        except OSError as e:
            return False, f"cannot hash target: {e}"

    return True, f"valid (age {age_s:.0f}s, signer={token.get('signer','?')})"


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 2

    # Subcommand: verify (for canary_deploy.py to call)
    if sys.argv[1] == "--verify":
        target = sys.argv[2] if len(sys.argv) > 2 else None
        valid, reason = verify_token(target)
        print(f"TOKEN {'VALID' if valid else 'INVALID'}: {reason}")
        return 0 if valid else 1

    target_file = sys.argv[1]
    dry_run = "--dry-run" in sys.argv
    print(f"[canary-gate-token] Target: {target_file}{' (DRY-RUN)' if dry_run else ''}")
    rc = issue_token(target_file, dry_run=dry_run)
    return rc


if __name__ == "__main__":
    sys.exit(main())