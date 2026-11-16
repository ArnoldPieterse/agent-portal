"""G1 proof: start regression_daemon in watch mode, touch agent_portal.py (mtime-only),
confirm the daemon auto-runs and logs a mtime_change trigger. Content of agent_portal.py
is NOT modified (os.utime only) so the live portal is unaffected."""
import os, subprocess, time, json, sys

BASE = "memory/verifier"
LOG = os.path.join(BASE, "regression-daemon-log.jsonl")
TARGET = "agent_portal.py"
DAEMON = os.path.join(BASE, "regression_daemon.py")

def log_lines():
    with open(LOG, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

before = log_lines()
print(f"log lines before: {len(before)}", flush=True)

proc = subprocess.Popen([sys.executable, DAEMON], stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT, text=True)
try:
    time.sleep(5)  # let daemon baseline
    print("baselined; touching target (mtime-only via os.utime)...", flush=True)
    t = time.time() + 1.0
    os.utime(TARGET, (t, t))
    detected = None
    for i in range(6):
        time.sleep(2)
        cur = log_lines()
        if len(cur) > len(before):
            try:
                last = json.loads(cur[-1])
            except json.JSONDecodeError:
                continue
            if "mtime_change" in last.get("trigger", ""):
                detected = last
                break
    print(f"auto-trigger detected: {bool(detected)}", flush=True)
    if detected:
        keep = {k: detected.get(k) for k in ("ts", "trigger", "sha1", "result")}
        print(json.dumps(keep, indent=1), flush=True)
finally:
    proc.terminate()
    try:
        out, _ = proc.communicate(timeout=4)
        print("--- daemon stdout tail ---", flush=True)
        print("\n".join(out.splitlines()[-6:]), flush=True)
    except subprocess.TimeoutExpired:
        proc.kill()
        print("daemon forced kill after timeout", flush=True)

print(f"log lines after: {len(log_lines())}", flush=True)
