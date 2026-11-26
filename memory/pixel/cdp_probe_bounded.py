#!/usr/bin/env python3
# Bounded (<=20s) probe: does Edge headless open a reachable CDP /json endpoint from THIS seat?
# Tests two launch variants: with and without --no-sandbox. No unbounded awaits.
import json, os, socket, subprocess, sys, time, urllib.request

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p

def probe(extra_flags, label):
    if not os.path.exists(EDGE):
        print("NO_EDGE"); return None
    port = free_port()
    proc = subprocess.Popen([EDGE, "--headless=new", f"--remote-debugging-port={port}",
                             "--disable-gpu", "--no-first-run"] + extra_flags + ["about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = None
    try:
        for _ in range(15):
            try:
                t = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=3).read())
                for x in t:
                    if x.get("type") == "page":
                        url = x.get("webSocketDebuggerUrl"); break
                if url: break
            except Exception as e:
                pass
            time.sleep(1)
    finally:
        try: proc.terminate()
        except Exception: pass
    print(f"[{label}] port={port} devtools={'REACHABLE' if url else 'NOT-REACHABLE'} {url or ''}")
    return url

if __name__ == "__main__":
    a = probe([], "no-nosandbox")
    b = probe(["--no-sandbox"], "with-nosandbox")
    print("RESULT", "WITH-NOSANDBOX-ONLY" if (a is None and b) else ("BOTH" if (a and b) else ("NONE" if (a is None and b is None) else "NO-NOSANDBOX-ONLY")))
