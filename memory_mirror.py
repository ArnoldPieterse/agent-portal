#!/usr/bin/env python3
"""memory_mirror.py - push shared project state into REMOTE host sandboxes over SMB.

Companion to _sync_workspace_to_sandbox() in agent_portal.py (which two-way syncs HERE <-> White's
own sandbox per chat turn). This script pushes the git-tracked allowlist HERE -> \\\host\\C$ for
Red/Pale/Black so remote agents can read TODO.md / MEMORY.md / code / memory/ with their own tools
(2026-11-13 mount asymmetry), and PULLS BACK each host's memory/ tree so remote agent work lands in
White (r29, 2026-11-13).

Design notes (r16 bundle review, 2026-11-13 - supersedes OPS r3 strict-newer-only fix):
  * Hash-first LWW: md5 both sides; equal -> skip and preserve mtime (steady-state runs are true
    no-ops; re-runs idempotent; no mtime churn).
  * Strict-newer mtime rule is trusted ONLY within SKEW_TOL (default 600 s, per-host override in
    memory_mirror_hosts.json key "skew_tol"). Cross-host clock skew was observed up to ~35 min
    (r15: White local 20:43 vs reported mtimes 19:57-21:18), so a large |dmtime| ordering may be a
    skew inversion, not real age. Hash differs AND |dmtime| > SKEW_TOL -> action conflict_skew:
    SKIP in both directions and log both hashes/sizes/mtimes (SKEW_SUSPECT) for Orchestrator
    adjudication. Visible-stale beats invisible-wrong: no silent clobber, no silent loss.
  * Root docs (git allowlist, not under memory/) are White-canonical: push on hash mismatch
    regardless of mtime; pull never touches them (pull walks remote memory/ only).
  * Per-host net use with explicit creds (admin shares reject anonymous; WinError 1326).
  * Hosts are independent: one dead host never blocks the others.
  * Nothing raises out of main() - a scheduled task must never error-loop noisily.
  * Every run appends one JSON line to memory_mirror.log (audit for the 5-min task; every
    hash-differing decision is logged with both md5s so stuck files are adjudicable from the log).

Credential status 2026-11-13: Red = empty password (works). Pale/Black password recorded in
smb_fix.ps1 ('[REDACTED-CREDENTIAL]') was REJECTED by both hosts (error 86) -> status pending_creds;
Arnold supplies the current passwords into memory_mirror_hosts.json, no code change needed.
"""
import json, os, shutil, subprocess, sys, datetime, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
CFG_FILE = os.path.join(HERE, "memory_mirror_hosts.json")
LOG_FILE = os.path.join(HERE, "memory_mirror.log")
SYNC_FILES = ["TODO.md", "MEMORY.md", "agents.json", "agent_portal.py"]   # fallback if the git repo is missing
# 2026-11-15: files that stay OFF the public GitHub repo (untracked, see .gitignore) but are still
# mirrored to internal fleet remotes - they hold private LAN detail and must never be pushed publicly.
INTERNAL_ONLY = ["memory/llm/hosts.md"]
GIT_EXE = os.path.join(HERE, "mingit", "cmd", "git.exe")
CREATE_NO_WINDOW = 0x08000000  # runs under pythonw (no console): without this flag every child (net use / git) allocates a VISIBLE console window - user-critical popup complaint, fixed 2026-11-15 post-reboot

def _allowlist():
    """The git-tracked file set (curated .gitignore allowlist, ~43 files) - what gets pushed to the
    remotes. Falls back to SYNC_FILES when the repo is missing so the mirror degrades safely."""
    import subprocess
    try:
        r = subprocess.run([GIT_EXE, "ls-files"], cwd=HERE, capture_output=True, text=True, timeout=20,
                           creationflags=CREATE_NO_WINDOW)
        out = [l.strip().replace("\\", "/") for l in (r.stdout or "").splitlines() if l.strip()]
        if out:
            return out + INTERNAL_ONLY   # internal-only files keep mirroring though untracked (public-repo hygiene)
    except Exception:
        pass
    return list(SYNC_FILES) + INTERNAL_ONLY

MTOL = 0.5      # seconds; matches _sync_workspace_to_sandbox tolerance (same-clock-domain edits)
SKEW_TOL = 600  # seconds; default cross-host skew band (observed up to ~35 min; tune via hosts.json)

def _md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:8]

def log(line):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    except Exception:
        pass

def _decide(sp, dp, skew_tol, root_canonical=False):
    """LWW decision for one file pair (sp=source, dp=dest). Returns (action, meta).
    action in {copy, skip_same, skip_stale, conflict_skew}. See module docstring for the rules."""
    ss = os.stat(sp)
    if not os.path.exists(dp):
        return "copy", {"reason": "new"}
    ds = os.stat(dp)
    hs, hd = _md5(sp), _md5(dp)
    if hs == hd:
        return "skip_same", {}
    if root_canonical:
        # White is authoritative for root docs; mtime never blocks a canonical push.
        return "copy", {"reason": "white-canonical", "hs": hs, "hd": hd}
    dm = ss.st_mtime - ds.st_mtime
    if abs(dm) > skew_tol:
        meta = {"hs": hs, "hd": hd, "ssz": ss.st_size, "dsz": ds.st_size,
                "src_mt": datetime.datetime.fromtimestamp(ss.st_mtime).strftime("%H:%M:%S"),
                "dst_mt": datetime.datetime.fromtimestamp(ds.st_mtime).strftime("%H:%M:%S"),
                "dm_s": round(dm, 1)}
        return "conflict_skew", meta
    if dm > MTOL:
        return "copy", {"reason": "lww-newer"}
    return "skip_stale", {}

def ensure_conn(ip, user, pw):
    """Make sure \\\ip\\C$ is reachable; try net use with creds if not. Returns (ok, note)."""
    root = r"\\%s\C$" % ip
    try:
        os.stat(root)
        return True, "already connected"
    except Exception:
        pass
    # Drop any stale/broken connection for this server first (net use is per-session;
    # a scheduled task may run in a different session than the one that made it).
    subprocess.run(["net", "use", root, "/delete", "/y"], capture_output=True, text=True,
                   creationflags=CREATE_NO_WINDOW)
    cmd = ["net", "use", root, "/user:%s" % user]
    if pw:
        cmd.append(pw)
    else:
        cmd.append("")   # empty arg -> net sees a quoted empty password (Red's case)
    r = subprocess.run(cmd, capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
    if r.returncode == 0:
        try:
            os.stat(root)
            return True, "net use ok"
        except Exception as e:
            return False, "net use rc=0 but stat failed: %s" % str(e)[:80]
    return False, (r.stderr or r.stdout).strip()[:120]

def mirror_host(h):
    name, ip, user, pw = h["name"], h["ip"], h.get("user", ""), h.get("password", "")
    skew_tol = float(h.get("skew_tol", SKEW_TOL))
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

    pushed, pulled, stale, same, conflicts, errors = [], [], 0, 0, [], []

    # 1) push git allowlist (root docs) - White-canonical on hash mismatch
    for rel in _allowlist():
        if rel == ".gitignore":
            continue
        sp = os.path.join(HERE, rel.replace("/", os.sep))
        if not os.path.isfile(sp):
            continue
        dp = os.path.join(dst_root, rel.replace("/", os.sep))
        try:
            action, meta = _decide(sp, dp, skew_tol, root_canonical=True)
            if action == "copy":
                os.makedirs(os.path.dirname(dp), exist_ok=True)
                shutil.copy2(sp, dp)
                pushed.append(rel)
            elif action == "skip_same":
                same += 1
        except Exception as e:
            errors.append("%s: %s" % (rel, str(e)[:80]))

    # 2) push White memory/ tree (read-view for remotes) - LWW within skew band only
    msrc = os.path.join(HERE, "memory")
    if os.path.isdir(msrc):
        for root, dirs, files in os.walk(msrc):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                if f.startswith("."):
                    continue
                sp = os.path.join(root, f)
                rel = "memory/" + os.path.relpath(sp, msrc).replace(os.sep, "/")
                dp = os.path.join(dst_root, "memory", os.path.relpath(sp, msrc).replace(os.sep, os.sep))
                try:
                    action, meta = _decide(sp, dp, skew_tol)
                    if action == "copy":
                        os.makedirs(os.path.dirname(dp), exist_ok=True)
                        shutil.copy2(sp, dp)
                        pushed.append(rel)
                    elif action == "skip_same":
                        same += 1
                    elif action == "skip_stale":
                        stale += 1
                    else:
                        conflicts.append({"dir": "push", "path": rel, **meta})
                except Exception as e:
                    errors.append("%s: %s" % (rel, str(e)[:80]))

    # 3) pull back remote memory/ tree - LWW within skew band; large-dm mismatches are SKEW_SUSPECT
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
                    action, meta = _decide(sp, dp, skew_tol)
                    if action == "copy":
                        os.makedirs(os.path.dirname(dp), exist_ok=True)
                        shutil.copy2(sp, dp)
                        pulled.append(rel)
                    elif action == "skip_same":
                        same += 1
                    elif action == "skip_stale":
                        stale += 1
                    else:
                        conflicts.append({"dir": "pull", "path": rel, **meta})
                except Exception as e:
                    perrors_note = "%s: %s" % (rel, str(e)[:80])
                    errors.append("pull " + perrors_note)

    res = {"host": name, "pushed": len(pushed), "files": pushed[:12],
           "pulled": len(pulled), "pulled_files": pulled[:12],
           "unchanged": same, "skipped_stale": stale,
           "conflicts": len(conflicts), "errors": errors}
    if conflicts:
        res["conflict_detail"] = conflicts[:8]   # SKEW_SUSPECT entries for adjudication
    return res

# 2026-11-16 PIN GUARD (goal-progress fix): C:\Projects\Workspace\index.html was observed
# flapping between canonical df1bbdaef684 (WCAG pin) and stale 5908b45891d3 within minutes -
# an external sync process (NOT this mirror, which never pulls root files back) is swapping it.
# Recovery: restore from the canonical backup kept in the mirrored memory/ tree, touch mtime
# so White wins future LWW decisions, log every intervention. Push happens right after,
# so remotes get the canonical file in the same cycle.
PIN_FILES = {
    # 2026-11-16 pin advanced (file-modularity rule, Studio seat): index.html split into a
    # markup-only shell + ui/ modules (ui/app.css, ui/core.js, ui/uploads.js) served by the
    # new GET /ui/* route. Supersedes e0679e5f0844 (2026-11-16d) and designer sandbox pins
    # c0629a5b7cee/289a101ccdf5. Advanced in the SAME turn as the edit so pin_guard accepts it.
    # 2026-11-16j pin advanced (Designer cycle-2 goal 4, Studio seat): <nav aria-label="Chat mode">
    # landmark + aside aria-label for screen readers; :focus-visible ring already in ui/app.css.
    "index.html": {"sha12": "2a3ffa6ac79c",
                   "backup": "memory/designer/index_html_CANONICAL_2a3ffa6ac79c_2026-11-16j.html"},
}

def _sha12(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:12]

def pin_guard():
    out = []
    for rel, spec in PIN_FILES.items():
        p = os.path.join(HERE, rel.replace("/", os.sep))
        try:
            if not os.path.isfile(p):
                continue
            s = _sha12(p)
            if s == spec["sha12"]:
                continue
            bak = os.path.join(HERE, spec["backup"].replace("/", os.sep))
            if os.path.isfile(bak) and _sha12(bak) == spec["sha12"]:
                shutil.copy2(bak, p)
                os.utime(p)   # fresh mtime -> White wins LWW against the flapper
                out.append({"file": rel, "was": s, "restored": spec["sha12"]})
            else:
                out.append({"file": rel, "was": s, "error": "backup missing/wrong sha"})
        except Exception as e:
            out.append({"file": rel, "error": str(e)[:80]})
    if out:
        log({"t": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "pin_guard": out})
    return out

def main():
    try:
        cfg = json.load(open(CFG_FILE, encoding="utf-8"))
    except Exception as e:
        log({"t": datetime.datetime.now().strftime("%H:%M:%S"), "error": "config: %s" % str(e)[:100]})
        return
    pg = pin_guard()
    results = [mirror_host(h) for h in cfg.get("hosts", [])]
    log({"t": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "results": results, "pin_guard": pg})
    if __name__ == "__main__" and "-v" in sys.argv:
        print(json.dumps(results, indent=1))

if __name__ == "__main__":
    main()
