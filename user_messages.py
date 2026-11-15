#!/usr/bin/env python3
"""User message queue CLI (2026-11-15) - inspect the human message queue via the portal API.

Human messages sent while the group is working are queued in user_messages.json with a
timestamp and per-agent checked booleans. The portal auto-injects each agent's pending
entries into its next prompt and marks them seen; this CLI is for inspection/audit.

Usage:
  python user_messages.py list            # recent entries + seen-by status
  python user_messages.py pending <Agent> # entries you have NOT seen yet (does not mark)
  python user_messages.py check <id> <Agent>   # mark an entry seen for one agent ('*' = all in scope)
"""
import json, sys, urllib.request

PORTAL = "http://127.0.0.1:8099"

def _get():
    with urllib.request.urlopen(PORTAL + "/api/user-messages", timeout=5) as r:
        return json.load(r)

def _post(path, payload):
    req = urllib.request.Request(PORTAL + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.load(r)

def main():
    args = sys.argv[1:]
    if not args or args[0] == "list":
        d = _get()
        msgs = d.get("messages", [])
        if not msgs:
            print("(queue empty)")
            return
        for m in msgs[-20:]:
            seen = ",".join(sorted((m.get("checked") or {}).keys())) or "-"
            flag = "DONE " if m.get("processed") else "PEND "
            priv = "@" + ",".join(m["mentions"]) if m.get("mentions") else "broadcast"
            print("%s [%s] %s (%s) seen: %s" % (flag, m["id"], m["ts"], priv, seen))
            print("    " + m["text"][:200].replace("\n", " "))
        return
    if args[0] == "pending" and len(args) >= 2:
        d = _get()
        name = args[1]
        out = [m for m in d.get("messages", [])
               if not (m.get("checked") or {}).get(name)
               and (not m.get("mentions") or name in m["mentions"])]
        if not out:
            print("(nothing pending for %s)" % name)
            return
        for m in out:
            print("[%s] %s %s" % (m["id"], m["ts"], "@" + ",".join(m["mentions"]) if m.get("mentions") else "broadcast"))
            print("    " + m["text"][:400].replace("\n", " "))
        return
    if args[0] == "check" and len(args) >= 3:
        r = _post("/api/user-messages/check", {"id": args[1], "agent": args[2]})
        print(json.dumps(r))
        return
    raise SystemExit(__doc__)

if __name__ == "__main__":
    main()
