#!/usr/bin/env python3
# smoke_suite.py - Autonomous smoke test suite for all 4 fleet hosts.
# Goal #1: probe model loaded? API responding? latency <500ms? Auto-remediate failures.
#
# Usage:
#   python memory/forge/smoke_suite.py [--timeout N] [--no-remediate] [--dry-run] [--elev]
#
# Exit codes: 0 = all hosts green, 1 = one or more unremediated failures.
# Default: direct network (run as SYSTEM via schtask). --elev for sandbox escalation.
import sys, os, json, time, subprocess, tempfile, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_MD = os.path.join(ROOT, "memory", "forge", "log.md")
RESULTS_JSONL = os.path.join(ROOT, "memory", "forge", "smoke-results.jsonl")
ELEV = os.path.join(ROOT, "elev.py")

HOSTS = [
    {"name": "White", "ip": "127.0.0.1",     "port": 8888, "remote": False, "user": "White"},
    {"name": "Red",   "ip": "IP_RED", "port": 8888, "remote": True,  "user": "Red"},
    {"name": "Pale",  "ip": "IP_PALE",  "port": 8888, "remote": True,  "user": "pale"},
    {"name": "Black", "ip": "IP_BLACK",  "port": 8888, "remote": True,  "user": "black"},
]

LATENCY_THRESHOLD_MS = 500
PROBE_TIMEOUT_S = 5
REMEDY_WAIT_S = 30


def now_iso():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_line(msg):
    line = "| " + now_iso() + " | " + msg + " |"
    print(line, flush=True)
    try:
        with open(LOG_MD, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def append_jsonl(entry):
    os.makedirs(os.path.dirname(RESULTS_JSONL), exist_ok=True)
    with open(RESULTS_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def probe_one(host, timeout):
    """Probe a single host: TCP connect + API /v1/models check."""
    import socket, urllib.request
    entry = {"host": host["name"], "ip": host["ip"], "port": host["port"]}
    start = time.monotonic()
    try:
        sock = socket.create_connection((host["ip"], host["port"]), timeout=timeout)
        entry["tcp_ms"] = round((time.monotonic() - start) * 1000, 1)
        sock.close()
    except Exception as e:
        entry["tcp_ms"] = None
        entry["error"] = "TCP: %s: %s" % (type(e).__name__, e)
        return entry
    start = time.monotonic()
    try:
        url = "http://%s:%d/v1/models" % (host["ip"], host["port"])
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            entry["api_ms"] = round((time.monotonic() - start) * 1000, 1)
            models = data.get("data", [])
            entry["model_loaded"] = len(models) > 0
            entry["model_name"] = models[0].get("id", "unknown") if models else None
    except Exception as e:
        entry["api_ms"] = round((time.monotonic() - start) * 1000, 1)
        entry["model_loaded"] = False
        entry["error"] = entry.get("error", "") + " API: %s: %s" % (type(e).__name__, e)
    return entry


def probe_hosts_direct(hosts, timeout):
    """Probe hosts directly (requires network access)."""
    return [probe_one(h, timeout) for h in hosts]


def write_probe_script(hosts, timeout):
    """Write a standalone probe script for elev.py execution."""
    lines = [
        "import socket, time, json, urllib.request",
        "TARGETS = %s" % json.dumps([{"name": h["name"], "ip": h["ip"], "port": h["port"]} for h in hosts]),
        "TIMEOUT = %d" % timeout,
        "results = []",
        "for t in TARGETS:",
        '    entry = {"host": t["name"], "ip": t["ip"], "port": t["port"]}',
        "    start = time.monotonic()",
        "    try:",
        '        sock = socket.create_connection((t["ip"], t["port"]), timeout=TIMEOUT)',
        '        entry["tcp_ms"] = round((time.monotonic() - start) * 1000, 1)',
        "        sock.close()",
        "    except Exception as e:",
        '        entry["tcp_ms"] = None',
        '        entry["error"] = "TCP: %s: %s" % (type(e).__name__, e)',
        "        results.append(entry)",
        "        continue",
        "    start = time.monotonic()",
        "    try:",
        '        url = "http://%s:%d/v1/models" % (t["ip"], t["port"])',
        '        req = urllib.request.Request(url)',
        "        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:",
        "            data = json.loads(resp.read().decode())",
        '            entry["api_ms"] = round((time.monotonic() - start) * 1000, 1)',
        '            models = data.get("data", [])',
        '            entry["model_loaded"] = len(models) > 0',
        '            entry["model_name"] = models[0].get("id", "unknown") if models else None',
        "    except Exception as e:",
        '        entry["api_ms"] = round((time.monotonic() - start) * 1000, 1)',
        '        entry["model_loaded"] = False',
        '        entry["error"] = entry.get("error", "") + " API: %s: %s" % (type(e).__name__, e)',
        "    results.append(entry)",
        'print(json.dumps({"results": results, "ts": time.time()}, indent=2))',
    ]
    tmp = os.path.join(tempfile.gettempdir(), "forge_probe_%d.py" % int(time.time()))
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return tmp


def run_elev(cmd_str):
    """Run a command via elev.py (SYSTEM context). Returns (rc, stdout, stderr)."""
    r = subprocess.run(
        [sys.executable, ELEV, "--shell", cmd_str],
        capture_output=True, text=True, timeout=120
    )
    return r.returncode, r.stdout, r.stderr


def probe_hosts(hosts, timeout, use_elev=False):
    """Probe via direct or elev mode."""
    if not use_elev:
        return probe_hosts_direct(hosts, timeout)
    probe_path = write_probe_script(hosts, timeout)
    cmd = '"%s" "%s"' % (sys.executable, probe_path)
    rc, stdout, stderr = run_elev(cmd)
    if os.path.exists(probe_path):
        os.remove(probe_path)
    if rc != 0:
        print("PROBE FAIL (elev rc=%d): %s" % (rc, stderr[:500]), file=sys.stderr)
        return None
    try:
        data = json.loads(stdout)
        return data["results"]
    except (json.JSONDecodeError, KeyError) as e:
        print("PARSE FAIL: %s stdout=%s" % (e, stdout[:500]), file=sys.stderr)
        return None


def classify(result):
    """Classify a single host result. Returns 'OK', 'WARN', or 'CRIT'."""
    if result.get("error") and result.get("tcp_ms") is None:
        return "CRIT"
    if not result.get("model_loaded", False):
        return "CRIT"
    total_ms = (result.get("tcp_ms") or 0) + (result.get("api_ms") or 0)
    if total_ms > LATENCY_THRESHOLD_MS:
        return "WARN"
    return "OK"


def remediate_host(host, use_elev=False):
    """Attempt to remediate a failed host. Returns True if successful."""
    name = host["name"]
    recover_path = os.path.join(ROOT, "recover_all.py")
    if not host["remote"]:
        # Local: run recover_all.py directly or via elev
        cmd = '"%s" "%s"' % (sys.executable, recover_path)
        if use_elev:
            rc, out, err = run_elev(cmd)
        else:
            r = subprocess.run([sys.executable, recover_path],
                               capture_output=True, text=True, timeout=120)
            rc = r.returncode
        return rc == 0
    else:
        # Remote: WinRM via PowerShell (must run as SYSTEM/elevated)
        ip = host["ip"]
        user = host["user"]
        ps_cmd = (
            'Invoke-Command -ComputerName %s -Credential '
            '$([System.Management.Automation.PSCredential]::new(\'%s\', [System.Security.SecureString]::new())) '
            '-ScriptBlock { python C:\\Projects\\AgentPortal\\recover_all.py }'
        ) % (ip, user)
        cmd = 'powershell -NoProfile -Command "%s"' % ps_cmd
        rc, out, err = run_elev(cmd)
        return rc == 0


def main():
    no_remediate = "--no-remediate" in sys.argv
    dry_run = "--dry-run" in sys.argv
    use_elev = "--elev" in sys.argv
    timeout = PROBE_TIMEOUT_S
    if "--timeout" in sys.argv:
        idx = sys.argv.index("--timeout")
        if idx + 1 < len(sys.argv):
            try:
                timeout = int(sys.argv[idx + 1])
            except ValueError:
                pass

    single_host = None
    if "--host" in sys.argv:
        idx = sys.argv.index("--host")
        if idx + 1 < len(sys.argv):
            single_host = sys.argv[idx + 1].lower()

    hosts_to_test = HOSTS
    if single_host:
        hosts_to_test = [h for h in HOSTS if h["name"].lower() == single_host]
        if not hosts_to_test:
            print("Unknown host: %s" % single_host, file=sys.stderr)
            sys.exit(2)

    if dry_run:
        print("DRY RUN - would probe: %s" % [h["name"] for h in hosts_to_test])
        print("Mode: %s" % ("elev" if use_elev else "direct"))
        print("Remediation: %s" % ("DISABLED" if no_remediate else "ENABLED"))
        sys.exit(0)

    ts_start = now_iso()
    print("=== Forge Smoke Suite: %s ===" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("Targets: %s" % [h["name"] for h in hosts_to_test])

    # Phase 1: Probe
    results = probe_hosts(hosts_to_test, timeout, use_elev)
    if results is None:
        log_line("smoke_suite: PROBE FAILED (network or elev error)")
        append_jsonl({"ts": ts_start, "status": "probe_failed", "hosts": [h["name"] for h in hosts_to_test]})
        sys.exit(1)

    # Phase 2: Classify
    print("\n--- Results ---")
    failures = []
    for r in results:
        status = classify(r)
        r["status"] = status
        latency = (r.get("tcp_ms") or 0) + (r.get("api_ms") or 0)
        model_info = r.get("model_name", "NO MODEL") if r.get("model_loaded") else "NONE"
        print("  %-6s %s  tcp=%sms api=%sms total=%sms model=%s" % (
            r["host"], status,
            r.get("tcp_ms", "-"), r.get("api_ms", "-"),
            int(latency), model_info))
        if status != "OK":
            failures.append(r)

    # Phase 3: Remediate (if enabled and there are failures)
    if failures and not no_remediate:
        print("\n--- Remediating %d failed host(s) ---" % len(failures))
        for f in failures:
            host_def = next(h for h in hosts_to_test if h["name"] == f["host"])
            print("  Attempting remediation: %s (%s)" % (f["host"], f.get("error", "model not loaded")))
            log_line("smoke_suite: REMEDIATING %s - %s" % (f["host"], f.get("error", "no model")))
            ok = remediate_host(host_def, use_elev)
            time.sleep(REMEDY_WAIT_S)
            # Re-probe to verify
            recheck = probe_one(host_def, timeout)
            new_status = classify(recheck)
            if new_status == "OK":
                f["remediated"] = True
                f["final_status"] = "OK"
                print("  %s -> REMEDIATED (now OK)" % f["host"])
                log_line("smoke_suite: %s REMEDIATED successfully" % f["host"])
            else:
                f["remediated"] = ok
                f["final_status"] = new_status
                print("  %s -> FAILED (still %s)" % (f["host"], new_status))
                log_line("smoke_suite: %s REMEDIATION FAILED (status=%s)" % (f["host"], new_status))
    elif failures:
        for f in failures:
            f["remediated"] = False
            f["final_status"] = f["status"]

    # Phase 4: Report + exit
    all_ok = all(r.get("final_status", r["status"]) == "OK" for r in results)
    summary = {"ts": ts_start, "results": results, "all_green": all_ok}
    append_jsonl(summary)
    log_line("smoke_suite: %s (%d hosts, %d issues)" % (
        "ALL GREEN" if all_ok else "FAILURES", len(results), len(failures)))

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()