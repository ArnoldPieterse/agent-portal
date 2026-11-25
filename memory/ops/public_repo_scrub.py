#!/usr/bin/env python
"""Public-repo hygiene guard (2026-11-25). Scans tracked files for private data
(LAN IPs, Windows usernames in home paths) and auto-scrubs doc/historical files.
Live-code files are listed in LIVE_ALLOWLIST: violations there are reported, not fixed.
Wired into daily_git_commit.py so every 15-min safety-net commit is clean."""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
GIT = os.path.join(ROOT, "mingit", "cmd", "git.exe")
LIVE_ALLOWLIST = {"agent_portal.py", "host_api.py", "fleet_reload.py", "black_dual_load2.py",
                  "git_run.py", "portal_host.py", "reboot_recover.py",
                  os.path.join("memory", "mechanic", "dream_sync.py")}
IP_MAP = [("IP_BLACK", "IP_BLACK"), ("IP_PALE", "IP_PALE"), ("IP_RED", "IP_RED")]
USER_MAP = [("White", "<white>"), ("black", "<black>"), ("Red", "<red>"), ("pale", "<pale>")]

def main():
    r = subprocess.run([GIT, "-C", ROOT, "ls-files"], capture_output=True, text=True)
    tracked = [l.strip() for l in r.stdout.splitlines() if l.strip()]
    fixed, live_violations, bad = 0, [], []
    for f in tracked:
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            continue
        try:
            t = open(p, encoding="utf-8").read()
        except UnicodeDecodeError:
            continue
        orig = t
        for ip, tok in IP_MAP:
            t = t.replace(ip, tok)
        t = re.sub(r"192\.168\.\d{1,3}\.\d{1,3}", "IP_LAN", t)
        for u, tok in USER_MAP:
            t = re.sub(r"C:[\/]+Users[\/]+%s" % re.escape(u), lambda m, tok=tok: "C:\\Users\\" + tok, t)
        t = t.replace("10.0.0.39", "IP_PALE").replace("10.0.0.99", "IP_BLACK").replace("10.0.0.245", "IP_RED")
        if t == orig:
            continue
        if f in LIVE_ALLOWLIST:
            live_violations.append(f)
            continue
        open(p, "w", encoding="utf-8").write(t)
        fixed += 1
    print("public_repo_scrub: %d files auto-scrubbed" % fixed)
    for f in live_violations:
        bad.append("LIVE-CODE VIOLATION (fix via fleet_local.json, do NOT commit real values): " + f)
    if bad:
        print("\n".join(bad))
    return 1 if (bad and "--check" in sys.argv) else 0

if __name__ == "__main__":
    sys.exit(main())
