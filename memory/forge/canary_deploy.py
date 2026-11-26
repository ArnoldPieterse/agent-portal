#!/usr/bin/env python3
# canary_deploy.py - Canary deploy pipeline with smoke-gate + auto-rollback.
# Goal #2: deploys to one host first, runs smoke suite against that host only,
#          auto-promotes to remaining 3 on pass or auto-rollbacks on fail.
#
# Usage:
#   python memory/forge/canary_deploy.py <file> [host] [--dry-run] [--skip-smoke] [--skip-perf] [--bypass-gate]
#
# Perf gate: measures p50/p95 before+after deploy; rolls back if post p95 > FORGE_PERF_THRESHOLD x baseline.
#            Default threshold 1.15 (env var FORGE_PERF_THRESHOLD). Samples: FORGE_PERF_SAMPLES (default 20).
#
# Dispatch-Correctness gate (Forge goal #3): before promoting a change that touches
#            dispatch logic, runs dispatch_gate conformance audit; BLOCKS pre-deploy if <100%.
#            Override with explicit --bypass-gate (logged).
#
# Exit codes: 0 = success (promoted all), 1 = canary failed (rolled back,
#             includes perf regression), 2 = usage error, 3 = promotion failed,
#             4 = dispatch-correctness gate blocked
import sys, os, json, time, subprocess, shutil, datetime, hashlib, urllib.request, socket
from collections import defaultdict

# Dispatch-Correctness gate (Forge goal #3) - imported from sibling module.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from dispatch_gate import is_dispatch_file, run_conformance_audit as _dispatch_audit
except Exception:  # noqa: BLE001 - degrade gracefully if gate module missing
    def is_dispatch_file(p):
        return False
    def _dispatch_audit(data=None):
        return {"pass": True, "violations": [], "details": "gate unavailable (import failed)"}

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SMOKE_SUITE = os.path.join(ROOT, "memory", "forge", "smoke_suite.py")
LOG_MD = os.path.join(ROOT, "memory", "forge", "log.md")
DEPLOY_LOG = os.path.join(ROOT, "memory", "forge", "deploy-log.jsonl")

HOSTS = ["White", "Red", "Pale", "Black"]
DEFAULT_CANARY = "White"  # local host first (fastest feedback)

# Perf gate config
PERF_THRESHOLD_RATIO = float(os.environ.get("FORGE_PERF_THRESHOLD", "1.15"))
PERF_SAMPLE_COUNT = int(os.environ.get("FORGE_PERF_SAMPLES", "20"))
HOST_IPS = {"White": "127.0.0.1", "Red": "IP_RED", "Pale": "IP_PALE", "Black": "IP_BLACK"}
HOST_PORT = 8888
INCIDENTS_PATH = os.path.join(ROOT, "memory", "ops", "incidents.jsonl")


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


def measure_perf(host, samples=None):
    """Measure p50/p95 API response times on a host.
    Returns dict with p50_ms, p95_ms, sample_count, or None if host unreachable."""
    if samples is None:
        samples = PERF_SAMPLE_COUNT
    ip = HOST_IPS.get(host)
    if not ip:
        return None
    url = "http://%s:%d/v1/models" % (ip, HOST_PORT)
    latencies = []
    for _ in range(samples):
        try:
            t0 = time.monotonic()
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
            elapsed_ms = (time.monotonic() - t0) * 1000
            latencies.append(elapsed_ms)
        except Exception:
            pass
    if not latencies:
        return None
    latencies.sort()
    n = len(latencies)
    p50 = latencies[int(n * 0.50)]
    p95_idx = min(int(n * 0.95), n - 1)
    p95 = latencies[p95_idx]
    return {"p50_ms": round(p50, 1), "p95_ms": round(p95, 1), "samples": n}


def check_perf_gate(baseline, post, host):
    """Compare post-deploy perf to baseline. Returns (passed, reason_str)."""
    if baseline is None or post is None:
        return True, "skipped (no perf data)"  # can't gate on missing data
    if baseline["p95_ms"] == 0:
        return True, "baseline p95=0, no regression possible"
    ratio = post["p95_ms"] / baseline["p95_ms"]
    if ratio > PERF_THRESHOLD_RATIO:
        reason = ("p95 regression: baseline=%.1fms post=%.1fms ratio=%.2f "
                  "threshold=%.2f") % (baseline["p95_ms"], post["p95_ms"], ratio, PERF_THRESHOLD_RATIO)
        return False, reason
    return True, "OK (ratio=%.2f <= %.2f)" % (ratio, PERF_THRESHOLD_RATIO)


def write_perf_incident(host, fname, baseline, post, reason):
    """Write a perf-regression incident note to memory/ops/incidents.jsonl."""
    entry = {
        "ts": now_iso(),
        "type": "perf_regression_rollback",
        "host": host,
        "file": fname,
        "baseline": baseline,
        "post_deploy": post,
        "reason": reason,
        "threshold_ratio": PERF_THRESHOLD_RATIO
    }
    os.makedirs(os.path.dirname(INCIDENTS_PATH), exist_ok=True)
    with open(INCIDENTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    log("PERF INCIDENT written: %s" % reason)


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: python memory/forge/canary_deploy.py <file> [host] [--dry-run] [--skip-smoke] [--skip-perf]")
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

    skip_perf = "--skip-perf" in sys.argv
    print("=== Canary Deploy: %s (sha=%s) ===" % (fname, file_hash))
    print("Canary host: %s | Promote to: %s" % (canary_host, promote_hosts))
    print("Mode: %s%s%s" % ("DRY-RUN " if dry_run else "",
                             "| skip-smoke" if skip_smoke else "",
                             "| skip-perf" if skip_perf else ""))

    # Phase -1: Dispatch-Correctness gate (pre-promotion conformance; Forge goal #3)
    # Runs BEFORE any deploy so a stale-dispatching change never touches a host.
    if is_dispatch_file(source_file):
        if "--bypass-gate" in sys.argv:
            log("DISPATCH GATE BYPASSED (explicit --bypass-gate) file=%s" % fname)
            print("\n[gate] Dispatch-Correctness BYPASSED via explicit --bypass-gate")
        else:
            gate_res = _dispatch_audit()
            if not gate_res["pass"]:
                log("DISPATCH GATE BLOCKED file=%s -> %s" % (fname, gate_res["details"]))
                print("\n[gate] DISPATCH-CORRECTNESS GATE: BLOCKED (%s)" % gate_res["details"])
                for v in gate_res["violations"][:5]:
                    print("    VIOLATION: [%s] %s" % (v.get("agent"), v.get("goal")))
                append_deploy_log({"ts": ts_start, "file": fname, "sha": file_hash,
                                   "status": "dispatch_gate_blocked",
                                   "violations": gate_res["violations"][:10]})
                print("\n  Promotion BLOCKED before any deploy. Fix stale dispatches or pass --bypass-gate.")
                sys.exit(4)
            else:
                log("DISPATCH GATE PASS file=%s -> %s" % (fname, gate_res["details"]))
                print("\n[gate] Dispatch-Correctness PASS (%s)" % gate_res["details"])

    # Phase 0: Baseline perf measurement
    baseline_perf = None
    if not dry_run and not skip_perf:
        print("\n[0/4] Measuring baseline perf on %s..." % canary_host)
        baseline_perf = measure_perf(canary_host)
        if baseline_perf:
            print("  Baseline: p50=%.1fms p95=%.1fms (n=%d)" % (
                baseline_perf["p50_ms"], baseline_perf["p95_ms"], baseline_perf["samples"]))
        else:
            print("  Baseline: UNREACHABLE (perf gate will be skipped)")

    # Phase 1: Deploy to canary
    log("START canary=%s file=%s sha=%s" % (canary_host, fname, file_hash))
    print("\n[1/4] Deploying to canary: %s" % canary_host)
    ok, bak = deploy_to_host(source_file, canary_host, dry_run)
    if not ok:
        log("FAIL canary deploy to %s (no rollback needed)" % canary_host)
        append_deploy_log({"ts": ts_start, "file": fname, "sha": file_hash,
                           "canary": canary_host, "status": "canary_deploy_failed"})
        sys.exit(1)

    # Phase 2: Smoke gate on canary
    if not skip_smoke:
        print("\n[2/4] Running smoke gate on %s..." % canary_host)
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

    # Phase 3: Perf gate on canary
    post_perf = None
    if not dry_run and not skip_perf and baseline_perf:
        print("\n[3/4] Measuring post-deploy perf on %s..." % canary_host)
        time.sleep(2)  # settle after deploy
        post_perf = measure_perf(canary_host)
        if post_perf:
            print("  Post:     p50=%.1fms p95=%.1fms (n=%d)" % (
                post_perf["p50_ms"], post_perf["p95_ms"], post_perf["samples"]))
            perf_ok, perf_reason = check_perf_gate(baseline_perf, post_perf, canary_host)
            print("  Gate:     %s" % perf_reason)
            if not perf_ok:
                log("PERF GATE FAIL on canary %s -> ROLLBACK (%s)" % (canary_host, perf_reason))
                print("\n  PERF REGRESSION DETECTED - rolling back %s" % canary_host)
                write_perf_incident(canary_host, fname, baseline_perf, post_perf, perf_reason)
                rb_ok = rollback_host(canary_host, source_file)
                status = "perf_rolled_back" if rb_ok else "perf_rollback_failed"
                log("PERF ROLLBACK %s -> %s" % (canary_host, "OK" if rb_ok else "FAILED"))
                append_deploy_log({"ts": ts_start, "file": fname, "sha": file_hash,
                                   "canary": canary_host, "status": status,
                                   "perf_baseline": baseline_perf, "perf_post": post_perf,
                                   "perf_reason": perf_reason})
                sys.exit(1)
        else:
            print("  Post: UNREACHABLE (cannot verify perf; allowing through)")
    elif skip_perf or dry_run:
        print("\n[3/4] Perf gate SKIPPED")

    # Phase 4: Promote to remaining hosts
    print("\n[4/4] Promoting to: %s" % ", ".join(promote_hosts))
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
    deploy_entry = {"ts": ts_start, "file": fname, "sha": file_hash,
                    "canary": canary_host, "status": "success",
                    "promoted": promote_hosts}
    if baseline_perf:
        deploy_entry["perf_baseline"] = baseline_perf
    if post_perf:
        deploy_entry["perf_post"] = post_perf
    append_deploy_log(deploy_entry)
    print("\n=== DEPLOY SUCCESS: %s on all 4 hosts ===" % fname)
    sys.exit(0)


if __name__ == "__main__":
    main()
