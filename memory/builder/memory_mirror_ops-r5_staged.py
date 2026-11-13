#!/usr/bin/env python3
"""memory_mirror.py - push shared project state into REMOTE host sandboxes over SMB.

Companion to _sync_workspace_to_sandbox() in agent_portal.py (which two-way syncs HERE <-> White's
own sandbox per chat turn). This script pushes the git-tracked allowlist HERE -> \\\\host\C$ for
Red/Pale/Black so remote agents can read TODO.md / MEMORY.md / code / memory/ with their own tools
(2026-11-13 mount asymmetry), and PULLS BACK each host's memory/ tree (newer/new files only) so
remote agent work lands in White (r29, 2026-11-13).

Design notes:
  * mtime-guarded (0.5 s tolerance, copy2 preserves mtime) -> steady-state runs push nothing.
  * OPS r5 (2026-11-13): push direction is strictly src-newer-only (the old abs() guard let stale
    local copies clobber newer remote memory/ work); files skipped that way are audited as
    skipped_stale in the per-host log line.
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
SYNC_FILES = ["TODO.md", "MEMORY.md", "agents.json", "agent_portal.py"]   # fallback if the git repo is missing
GIT_EXE = os.path.join(HERE, "mingit", "cmd", "git.exe")

def _allowlist():
    """The git-tracked file set (curated .gitignore allowlist, ~43 files) - what gets pushed to the
    remotes. Falls back to SYNC_FILES when the repo is missing so the mirror degrades safely."""
    import subprocess
    try:
        r = subprocess.run([GIT_EXE, "ls-files"], cwd=HERE, capture_output=True, text=True, timeout=20)
        out = [l.strip().replace("\\", "/") for l in (r.stdout or "").splitlines() if l.strip()]
        if out:
            return out
    except Exception:
        pass
    return list(SYNC_FILES)
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
    """mtime-guarded mirror of src_root -> dst_root. OPS r5 direction fix (2026-11-13): push only
    when SRC is newer than DST + MTOL - the old abs() guard pushed stale local copies OVER newer
    remote work. Returns (pushed, errors, skipped_stale)."""
    pushed, errors, skipped = [], [], []
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
                if ds is None or ss.st_mtime > ds.st_mtime + MTOL:
                    os.makedirs(os.path.dirname(dp), exist_ok=True)
                    shutil.copy2(sp, dp)
                    pushed.append(rel)
                elif ds is not None and ds.st_mtime > ss.st_mtime + MTOL:
                    skipped.append(rel)   # remote copy newer - never clobber it (audit trail)
            except Exception as e:
                errors.append("%s: %s" % (rel, str(e)[:80]))
    return pushed, errors, skipped

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
    for rel in _allowlist():
        if rel == ".gitignore":
            continue
        sp = os.path.join(HERE, rel.replace("/", os.sep))
        if not os.path.isfile(sp):
            continue
        dp = os.path.join(dst_root, rel.replace("/", os.sep))
        try:
            ss = os.stat(sp)
            ds = os.stat(dp) if os.path.exists(dp) else None
            if ds is None or ss.st_mtime > ds.st_mtime + MTOL:
                os.makedirs(os.path.dirname(dp), exist_ok=True)   # new subdirs (memory/<agent>/) may not exist remotely yet
                shutil.copy2(sp, dp)
                pushed.append(rel.replace(os.sep, "/"))
        except Exception as e:
            errors.append("%s: %s" % (rel, str(e)[:80]))
    p2, e2, sk2 = push_tree(os.path.join(HERE, "memory"), os.path.join(dst_root, "memory"))
    pushed += ["memory/" + r for r in p2]
    errors += e2
    skipped_stale = ["memory/" + r.replace(os.sep, "/") for r in sk2]
    # r29 (2026-11-13): pull back the remote memory/ tree - newer/new files only, never overwrite a
    # newer local copy (so e.g. Scribe's goal batches on Red land in White).
    pulled, perrors = [], []
    rm = os.path.join(dst_root, "memory")
    if os.path.isdir(rm):
        for root, dirs, files in os.walk(rm):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                if f.startswith("."):
                    continue
                sp = os.path.join(root, f)
                rel = "memory/" + os.path.relpath(sp, rm).replace(os.sep, "/")
                dp = os.path.join(HERE, rel.replace("/", os.sep))
                try:
                    ss = os.stat(sp)
                    ds = os.stat(dp) if os.path.exists(dp) else None
                    if ds is None or ss.st_mtime > ds.st_mtime + MTOL:
                        os.makedirs(os.path.dirname(dp), exist_ok=True)
                        shutil.copy2(sp, dp)
                        pulled.append(rel)
                except Exception as e:
                    perrors.append("%s: %s" % (rel, str(e)[:80]))
    res = {"host": name, "pushed": len(pushed), "files": pushed[:12], "errors": errors}
    if skipped_stale:
        res["skipped_stale"] = skipped_stale[:12]   # audit line: newer remote copies NOT clobbered
    if pulled or perrors:
        res["pulled"] = len(pulled)
        res["pulled_files"] = pulled[:12]
        res["pull_errors"] = perrors
    return res

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
