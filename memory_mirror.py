#!/usr/bin/env python3
"""memory_mirror.py - push shared project state into REMOTE host sandboxes over SMB.

Companion to _sync_workspace_to_sandbox() in agent_portal.py (which mirrors HERE -> White's
own sandbox per chat turn). This script does the same one-way mirror HERE -> \\\\host\C$ for
Red/Pale/Black so remote agents can read TODO.md / MEMORY.md / agents.json / memory/ with their
own tools (2026-11-13 mount asymmetry: remote sandboxes held only .unsloth_sandbox).

Design notes:
  * mtime-guarded (0.5 s tolerance, copy2 preserves mtime) -> steady-state runs push nothing.
  * Per-host net use with explicit creds (admin shares reject anonymous; WinError 1326).
  * Hosts are independent: one dead host never blocks the others.
  * Nothing raises out of main() - a scheduled task must never error-loop noisily.
  * Every run appends one JSON line to memory_mirror.log (audit for the 5-min task).

Credential status 2026-11-13: Red = empty password (works). Pale/Black password recorded in
smb_fix.ps1 ('131991Apiet') was REJECTED by both hosts (error 86) -> status pending_creds;
Arnold supplies the current passwords into memory_mirror_hosts.json, no code change needed.
"""
import json, os, shutil, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CFG_FILE = os.path.join(HERE, "memory_mirror_hosts.json")
LOG_FILE = os.path.join(HERE, "memory_mirror.log")
SYNC_FILES = ["TODO.md", "MEMORY.md", "agents.json", "agent_portal.py"]   # same set as the portal
MTOL = 0.5  # seconds; matches _sync_workspace_to_sandbox tolerance

def log(line):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except Exception:
        pass

def ensure_conn(ip, user, pw):
    """Make sure \\\\ip\C$ is reachable; try net use with creds if not. Returns (ok, note)."""
    root = r"\\%s\C$" % ip
    try:
        os.stat(root)
        return True, "already connected"
    except Exception:
        pass
    # Drop any stale/broken connection for this server first (net use is per-session;
    # a scheduled task may run in a different session than the one that made it).
    subprocess.run(["net", "use", root, "/delete", "/y"], capture_output=True, text=True)
    cmd = ["net", "use", root, "/user:%s" % user]
    if pw:
        cmd.append(pw)
    else:
        cmd.append("")   # empty arg -> net sees a quoted empty password (Red's case)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        try:
            os.stat(root)
            return True, "net use ok"
        except Exception as e:
            return False, "net use rc=0 but stat failed: %s" % str(e)[:80]
    return False, (r.stderr or r.stdout).strip()[:120]

def push_tree(src_root, dst_root):
    """mtime-guarded mirror of src_root -> dst_root. Returns (pushed, errors)."""
    pushed, errors = [], []
    for root, dirs, files in os.walk(src_root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if f.startswith("."):
                continue
            sp = os.path.join(root, f)
            rel = os.path.relpath(sp, src_root)
            dp = os.path.join(dst_root, rel)
            try:
                ss = os.stat(sp)
                ds = os.stat(dp) if os.path.exists(dp) else None
                if ds is None or abs(ss.st_mtime - ds.st_mtime) > MTOL:
                    os.makedirs(os.path.dirname(dp), exist_ok=True)
                    shutil.copy2(sp, dp)
                    pushed.append(rel)
            except Exception as e:
                errors.append("%s: %s" % (rel, str(e)[:80]))
    return pushed, errors

def mirror_host(h):
    name, ip, user, pw = h["name"], h["ip"], h.get("user", ""), h.get("password", "")
    if h.get("status") != "ok":
        return {"host": name, "skipped": h.get("status", "disabled")}
    ok, note = ensure_conn(ip, user, pw)
    if not ok:
        return {"host": name, "error": "connect: " + note}
    dst_root = r"\\%s\C$\Users\%s\.unsloth\studio\sandbox\_default" % (ip, user)
    try:
        os.stat(dst_root)
    except Exception as e:
        return {"host": name, "error": "sandbox dir missing: %s" % str(e)[:80]}
    pushed, errors = [], []
    for rel in SYNC_FILES:
        sp = os.path.join(HERE, rel)
        if not os.path.isfile(sp):
            continue
        dp = os.path.join(dst_root, rel)
        try:
            ss = os.stat(sp)
            ds = os.stat(dp) if os.path.exists(dp) else None
            if ds is None or abs(ss.st_mtime - ds.st_mtime) > MTOL:
                shutil.copy2(sp, dp)
                pushed.append(rel)
        except Exception as e:
            errors.append("%s: %s" % (rel, str(e)[:80]))
    p2, e2 = push_tree(os.path.join(HERE, "memory"), os.path.join(dst_root, "memory"))
    pushed += ["memory/" + r for r in p2]
    errors += e2
    return {"host": name, "pushed": len(pushed), "files": pushed[:12], "errors": errors}

def main():
    try:
        cfg = json.load(open(CFG_FILE, encoding="utf-8"))
    except Exception as e:
        log({"t": datetime.datetime.now().strftime("%H:%M:%S"), "error": "config: %s" % str(e)[:100]})
        return
    results = [mirror_host(h) for h in cfg.get("hosts", [])]
    log({"t": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "results": results})
    if __name__ == "__main__" and "-v" in sys.argv:
        print(json.dumps(results, indent=1))

if __name__ == "__main__":
    main()
