# OPS-NOTE 2026-11-26 Mechanic: cycle_30m persistent timeout (memory_mirror.py)

**Symptom:** cycle_30m rc=124 (TIMEOUT after 900s) on EVERY run since ~2026-11-23 20:06.
Last success: 2026-11-25 11:07. Currently 24+ hours without a completed mirror cycle.
95 of 132 total completions are timeouts (72%).

**Root cause:** `ensure_conn()` in memory_mirror.py calls `subprocess.run(["net", "use", ...])` 
with NO `timeout=` parameter. When a host is unreachable (SMB path dead, host powered off, 
or credentials rejected), the call hangs for the OS-level SMB timeout (~20-30s per attempt).
With 3 hosts × (os.stat + net use /delete + net use connect) = up to 9 blocking calls that 
each can hang. Worst case: 9 × 100s+ = well over 900s step timeout.

**Evidence:**
- memory_mirror.log last entries (Nov 18-20): all hosts "System error 5 - Access is denied"
- Scheduler log: 10 consecutive rc=124 from 06:50 to 11:11 today (30-min intervals)
- ensure_conn() source: zero timeout= params on any subprocess.run() or os.stat()

**Fix (one-line per call, apply on White where memory_mirror.py is canonical):**

```python
def ensure_conn(ip, user, pw):
    root = r"\\%s\C$" % ip
    try:
        # ADD: timeout via socket pre-check instead of raw os.stat (which has no timeout)
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)  # 5s cap per host
        s.connect((ip, 445))
        s.close()
    except Exception:
        return False, "host unreachable (port 445 timeout)"
    try:
        os.stat(root)
        return True, "already connected"
    except Exception:
        pass
    subprocess.run(["net", "use", root, "/delete", "/y"], capture_output=True, text=True,
                   creationflags=CREATE_NO_WINDOW, timeout=10)
    cmd = ["net", "use", root, "/user:%s" % user]
    if pw:
        cmd.append(pw)
    else:
        cmd.append("")
    r = subprocess.run(cmd, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW, timeout=10)
    if r.returncode == 0:
        try:
            os.stat(root)
            return True, "net use ok"
        except Exception as e:
            return False, "net use rc=0 but stat failed: %s" % str(e)[:80]
    return False, (r.stderr or r.stdout).strip()[:120]
```

**Impact of fix:** Worst-case per-host drops from indefinite to ~25s (5s socket + 10s delete + 10s connect). 
3 hosts × 25s = 75s max for connection phase. Total mirror run should complete well under 900s even 
with all hosts down.

**Apply method:** On White, edit memory_mirror.py ensure_conn() function as above, then:
`python elev.py --shell "python memory_mirror.py -v"` to verify it completes < 120s with all hosts down.

**Interim mitigation (if full fix can't land immediately):** Set host status to "skip" in 
memory_mirror_hosts.json for any host that's consistently unreachable - the mirror already 
respects this and skips those hosts entirely.
