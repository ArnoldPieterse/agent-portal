"""canary_deploy.py - Canary deploy pipeline for portal changes.

Stages a patch to Red first, runs smoke suite there, promotes to Black/Pale
only if green. Bad change caught at Red never reaches the others.

Usage:
  python memory/builder/canary_deploy.py <diff_file> [--simulate]

Hosts are simulated as directories under memory/builder/canary/<host>/.
Each host has its own copy of agent_portal.py.

Acceptance: good change -> Red passes -> Black/Pale promoted;
            bad change  -> Red fails  -> Black/Pale untouched.
"""
import sys, os, shutil, subprocess, time, json

BASE = os.path.join(os.path.dirname(__file__), "canary")
HOSTS = ["red", "black", "pale"]  # deploy order: canary first
SOURCE = "agent_portal.py"       # the "production" source (shared root)
EVENTS = os.path.join("memory", "ops", "canary-events.jsonl")


def init_hosts():
    """Initialize host directories from the production source."""
    for host in HOSTS:
        hdir = os.path.join(BASE, host)
        os.makedirs(hdir, exist_ok=True)
        dest = os.path.join(hdir, "agent_portal.py")
        if not os.path.exists(dest):
            shutil.copy2(SOURCE, dest)


def apply_patch_to_file(target_path, diff_text):
    """Apply a single-hunk unified diff to target_path."""
    import re
    with open(target_path, "r", encoding="utf-8") as f:
        lines = f.read().split("\n")

    diff_lines = diff_text.strip().split("\n")
    hunk_start = None
    for i, line in enumerate(diff_lines):
        if line.startswith("@@"):
            hunk_start = i
            break
    if hunk_start is None:
        return False, "No @@ hunk found"

    m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", diff_lines[hunk_start])
    if not m:
        return False, f"Bad hunk header"
    old_start = int(m.group(1)) - 1  # 0-based

    old_lines = []
    new_lines = []
    for line in diff_lines[hunk_start + 1:]:
        if line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("-"):
            old_lines.append(line[1:])
        elif line.startswith("+"):
            new_lines.append(line[1:])
        elif line.startswith(" "):
            old_lines.append(line[1:])
            new_lines.append(line[1:])
        else:
            break

    idx = old_start
    actual_old = lines[idx:idx + len(old_lines)]
    if actual_old != old_lines:
        return False, f"Mismatch at line {old_start + 1}"

    lines[idx:idx + len(old_lines)] = new_lines
    with open(target_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return True, None


def smoke_test(host):
    """Run py_compile on the host's portal copy. Returns (pass, detail)."""
    target = os.path.join(BASE, host, "agent_portal.py")
    try:
        result = subprocess.run(
            [sys.executable, "-c",
             f"import py_compile; py_compile.compile(r'{target}', doraise=True)"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return True, "syntax OK"
        return False, f"syntax error: {result.stderr.strip()[:200]}"
    except subprocess.TimeoutExpired:
        return False, "timeout"


def promote(host_from, host_to):
    """Copy the file from one host to another."""
    src = os.path.join(BASE, host_from, "agent_portal.py")
    dst = os.path.join(BASE, host_to, "agent_portal.py")
    shutil.copy2(src, dst)


def log_event(event_type, detail, hosts_affected=None):
    os.makedirs(os.path.dirname(EVENTS), exist_ok=True)
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "type": event_type,
        "detail": detail,
        "hosts": hosts_affected or []
    }
    with open(EVENTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python canary_deploy.py <diff_file> [--simulate]")
        sys.exit(1)

    diff_file = sys.argv[1]
    simulate = "--simulate" in sys.argv

    with open(diff_file, "r", encoding="utf-8") as f:
        diff_text = f.read()

    init_hosts()

    # Phase 1: Deploy to Red (canary)
    red_target = os.path.join(BASE, "red", "agent_portal.py")
    ok, err = apply_patch_to_file(red_target, diff_text)
    if not ok:
        log_event("canary-fail-apply", err, ["red"])
        print(f"FAIL [Red/apply]: {err}")
        sys.exit(1)

    # Phase 2: Smoke test on Red
    smoke_ok, smoke_detail = smoke_test("red")
    if not smoke_ok:
        log_event("canary-fail-smoke", smoke_detail, ["red"])
        print(f"FAIL [Red/smoke]: {smoke_detail}")
        print("Quarantined. Black/Pale NOT affected.")
        sys.exit(2)

    # Phase 3: Promote to Black and Pale
    for host in ["black", "pale"]:
        promote("red", host)
        ok, detail = smoke_test(host)
        if not ok:
            log_event("canary-fail-promote", f"{host}: {detail}", [host])
            print(f"FAIL [{host}/post-promote]: {detail}")
            sys.exit(3)

    log_event("canary-success", "all hosts green", HOSTS)
    print(f"SUCCESS: change promoted to all hosts: {HOSTS}")
    print(f"  Red:   {smoke_detail}")
    print(f"  Black: OK")
    print(f"  Pale:  OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
