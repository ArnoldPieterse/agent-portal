#!/usr/bin/env python3
"""
git_run.py — git runner with UAC-popup fallback (2026-11-23)

WHY THIS EXISTS:
The only full git on this box originally lived under
AppData\\Local\\hermes\\tools\\git-2.53.0+3-win32-x64, where the real binary
(mingw64\\bin\\git.exe) carries a locked-down DACL (SYSTEM/Administrators only;
our own elevated icacls /grant gets silently stripped from that one file).
Non-elevated launches therefore failed with "error launching git: Access is denied."

FIX: this runner uses the clean copy at C:\\Users\\White\\mingit (made via one
elevated robocopy, normal ACLs, White has F — see memory/ops/git-access-denied-fix-2026-11-23.md).
If ANY launch still hits access-denied, it automatically retries ELEVATED: Windows
shows a UAC consent popup, you click Yes, and the command's output + exit code come
back to the caller. No silent failures.

USAGE:
  python git_run.py --version
  python git_run.py -C C:\\Projects\\Workspace status --short
  python git_run.py add <files...> && python git_run.py commit -m "msg"   (cwd is inherited)
Exit code = git's exit code.
"""
import os, subprocess, sys, tempfile

GIT = __import__("os").path.expanduser(r"~\mingit\cmd\git.exe")

def _denied(out, err):
    blob = ((out or "") + "\n" + (err or "")).lower()
    return "access is denied" in blob or "access denied" in blob

def _psq(s):
    """PowerShell single-quoted string literal."""
    return "'" + str(s).replace("'", "''") + "'"

def run_git(args, cwd=None):
    args = [str(a) for a in args]
    if not os.path.exists(GIT):
        sys.stderr.write(f"[git_run] git not found at {GIT} — re-copy per ops note\n")
        return subprocess.CompletedProcess([GIT] + args, 127, "", "git executable missing")
    try:
        r = subprocess.run([GIT] + args, capture_output=True, text=True,
                           timeout=600, cwd=cwd)
        if not _denied(r.stdout, r.stderr):
            return r
        sys.stderr.write("[git_run] access denied on normal launch — retrying elevated; "
                         "a UAC popup will appear, click Yes\n")
    except PermissionError as e:
        sys.stderr.write(f"[git_run] {e} — retrying elevated; a UAC popup will appear, click Yes\n")

    # Elevated retry: inner script runs git under the UAC-elevated token and records its exit code.
    d = tempfile.gettempdir()
    ps1, outf = os.path.join(d, "gitrun_elev.ps1"), os.path.join(d, "gitrun_elev.out")
    if os.path.exists(outf):
        os.remove(outf)
    arglist = ", ".join(_psq(a) for a in args)
    script = "\n".join([
        "$ErrorActionPreference='SilentlyContinue'",
        f"$exe = {_psq(GIT)}",
        f"$a = @({arglist})",
        f"$o = {_psq(outf)}",
        f"$cwd = {_psq(cwd or '')}",
        "if ($cwd) { Set-Location $cwd }",
        "& $exe @a *> $o",
        "Add-Content -Path $o -Value ('RC=' + $LASTEXITCODE)",
    ])
    open(ps1, "w", encoding="utf-8").write(script)
    try:
        launcher = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
             f'Start-Process -FilePath powershell -ArgumentList \'-NoProfile -ExecutionPolicy Bypass -File "{ps1}"\' -Verb RunAs -Wait'],
            capture_output=True, text=True, timeout=900)
    except Exception as e:
        sys.stderr.write(f"[git_run] elevated launch failed: {e}\n")
        return subprocess.CompletedProcess([GIT] + args, 125, "", str(e))
    if not os.path.exists(outf):
        hint = (launcher.stderr or "").strip()[:200]
        sys.stderr.write(f"[git_run] elevated run produced no output (UAC declined?): {hint}\n")
        return subprocess.CompletedProcess([GIT] + args, 125, "", "elevated run produced no output")
    raw = open(outf, encoding="utf-8", errors="replace").read()
    rc, body = 1, raw
    for line in raw.splitlines():
        if line.startswith("RC="):
            try:
                rc = int(line[3:])
            except ValueError:
                pass
            body = body.replace(line + "\n", "")
    return subprocess.CompletedProcess([GIT] + args, rc, body, "")

def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if not argv:
        print(__doc__)
        return 2
    r = run_git(argv, cwd=os.getcwd())
    if r.stdout:
        sys.stdout.write(r.stdout)
    if r.stderr:
        sys.stderr.write(r.stderr)
    return r.returncode

if __name__ == "__main__":
    sys.exit(main())
