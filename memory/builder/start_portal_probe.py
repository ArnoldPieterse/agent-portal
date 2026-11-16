#!/usr/bin/env python
# 2026-11-17 (Builder): launch agent_portal.py detached, wait, probe :8099. Prints JSON verdict.
# Reusable for the portal-down shared blocker; leaves the portal running on success.
import subprocess, sys, time, socket, json, urllib.request

def main():
    p = subprocess.Popen([sys.executable, "agent_portal.py"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                         creationflags=0x00000010 | 0x00000200)  # NEW_PROCESS_GROUP | DETACHED
    time.sleep(4)
    alive = p.poll() is None
    s = socket.socket(); r = s.connect_ex(("127.0.0.1", 8099)); port_open = (r == 0); s.close()
    status, body = None, ""
    try:
        u = urllib.request.urlopen("http://127.0.0.1:8099/api/goals", timeout=4)
        status = u.status
        body = u.read(120).decode("utf-8", "replace")
    except Exception as e:
        body = repr(e)
    err_tail = ""
    if not alive and p.stderr is not None:
        err_tail = p.stderr.read().decode("utf-8", "replace").strip()[-400:]
    print(json.dumps({"alive": alive, "port8099_open": port_open,
                      "api_goals_status": status, "body_head": body,
                      "stderr_tail": err_tail}, indent=2))

if __name__ == "__main__":
    main()