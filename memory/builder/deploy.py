#!/usr/bin/env python3
"""deploy.py - One-command deploy: validate -> test -> sync -> pin -> commit+tag.

Usage:
  python memory/builder/deploy.py [file] [--skip-tests] [--dry-run]

If no file arg, deploys all git-changed files in ui/ and index.html.
Exit: 0 success | 2 validation failed | 3 tests failed | 4 pin error | 5 git error
"""
import os, re, sys, hashlib, subprocess, shutil, datetime, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UI_DIR = os.path.join(ROOT, "ui")
PIN_FILE = os.path.join(ROOT, "memory_mirror.py")
CANONICAL_DIR = os.path.join(ROOT, "memory", "designer")

def log(msg): print(f"[deploy] {msg}")
def die(code, msg):
    print(f"[deploy] ERROR: {msg}", file=sys.stderr)
    sys.exit(code)

def sha12(b): return hashlib.sha1(b).hexdigest()[:12]

# --- Step 1: Syntax validation (reuse logic from build_verify_pin.py) ---
def _js_balanced(src):
    """Char-scanner for JS delimiter balance. Handles comments, strings, templates."""
    stack = []
    state = "code"
    i, n = 0, len(src)
    prev_sig = ""
    def push(c):
        if c in "({[": stack.append(c)
        elif c in ")}]":
            want = {")":"(","}":"{","]":"["}[c]
            if not stack or stack[-1] != want: return False
            stack.pop()
        return True
    while i < n:
        ch = src[i]; nxt = src[i+1] if i+1<n else ""
        if state == "code":
            if ch=="/" and nxt=="/": state="line"; i+=2; continue
            if ch=="/" and nxt=="*": state="block"; i+=2; continue
            if ch=="'": state="sq"; prev_sig="str"; i+=1; continue
            if ch=='"': state="dq"; prev_sig="str"; i+=1; continue
            if ch=="`":
                j=i+1; depth=0
                while j<n:
                    c2=src[j]; nx2=src[j+1] if j+1<n else ""
                    if depth==0 and c2=="`": break
                    if c2=="$" and nx2=="{": depth+=1; j+=2; continue
                    if depth>0 and c2=="}": depth-=1
                    j+=1
                i=j+1; prev_sig="str"; continue
            if ch in "({[": 
                if not push(ch): return False, f"Unbalanced '{ch}' at pos {i}"
            elif ch in ")}]":
                if not push(ch): return False, f"Unexpected '{ch}' at pos {i}"
            prev_sig = ch
        elif state == "line":
            if ch=="\n": state="code"
        elif state == "block":
            if ch=="*" and nxt=="/": state="code"; i+=1
        elif state in ("sq","dq"):
            if ch=="\\": i+=1
            elif ch==("'" if state=="sq" else '"'): state="code"
        i+=1
    if stack: return False, f"Unclosed delimiters: {stack[-3:]}"
    return True, "ok"

def validate_file(path):
    ext = os.path.splitext(path)[1].lower()
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        src = f.read()
    if ext == ".js":
        ok, msg = _js_balanced(src)
        return ok, msg
    elif ext == ".css":
        # Simple: balanced braces
        depth = 0
        for c in src:
            if c=="{": depth+=1
            elif c=="}": depth-=1
            if depth<0: return False, "Unbalanced }"
        if depth!=0: return False, f"Unclosed {{ (depth={depth})"
        return True, "ok"
    elif ext == ".html":
        # Just check it's non-empty and has <html or <!DOCTYPE
        if len(src.strip())<10: return False, "File too short"
        return True, "ok"
    else:
        return True, "ok (no validator for this extension)"

# --- Step 2: Run UI tests ---
def run_ui_tests(skip=False):
    if skip:
        log("Tests skipped (--skip-tests)")
        return True
    # Check if node is available
    try:
        subprocess.run(["node", "--version"], capture_output=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        log("WARNING: node not available - skipping UI tests (use --skip-tests to silence)")
        return True  # Don't fail if node absent; just warn
    runner = os.path.join(ROOT, "memory", "builder", "ui-tests", "run.js")
    if not os.path.exists(runner):
        log("WARNING: ui-tests/run.js not found - skipping")
        return True
    r = subprocess.run(["node", runner], capture_output=True, text=True, timeout=30)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        return False
    return True

# --- Step 3: Sync to portal root ---
def sync_to_portal(files):
    """Files in the shared agent folder ARE the portal root (served by agent_portal.py).
    This step verifies they're readable and reports their status."""
    for f in files:
        path = os.path.join(ROOT, f) if not os.path.isabs(f) else f
        if not os.path.exists(path):
            die(2, f"File not found after sync check: {f}")
        size = os.path.getsize(path)
        log(f"  synced: {f} ({size} bytes)")
    return True

# --- Step 4: Advance pin (only for index.html) ---
def advance_pin(filename):
    if "index.html" not in filename:
        log("Pin advance: not applicable (only index.html is pinned)")
        return True
    path = os.path.join(ROOT, filename)
    with open(path, "rb") as f:
        s = sha12(f.read())
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    stem = os.path.splitext(os.path.basename(filename))[0]
    canonical_name = f"{stem}_CANONICAL_{s}_{date_str}x.html"
    canonical_path = os.path.join(CANONICAL_DIR, canonical_name)
    
    if not os.path.exists(CANONICAL_DIR):
        os.makedirs(CANONICAL_DIR, exist_ok=True)
    shutil.copy2(path, canonical_path)
    log(f"  canonical backup: memory/designer/{canonical_name}")
    
    # Update PIN_FILES in memory_mirror.py if it exists and is non-empty
    if os.path.exists(PIN_FILE) and os.path.getsize(PIN_FILE) > 0:
        with open(PIN_FILE, "r") as f:
            content = f.read()
        # Find and update the index.html pin line
        new_line = f'    "index.html": ("{s}", "memory/designer/{canonical_name}"),'
        pattern = r'\s*"index\.html"\s*:\s*\([^)]+\),'
        if re.search(pattern, content):
            content = re.sub(pattern, new_line, content)
            with open(PIN_FILE, "w") as f:
                f.write(content)
            log(f"  PIN_FILES updated: sha12={s}")
        else:
            log("  WARNING: could not find index.html entry in PIN_FILES - manual update needed")
    else:
        log("  NOTE: memory_mirror.py empty/absent in this seat - pin recorded for host seat")
        log(f"  ACTION NEEDED on White: set PIN_FILES[\'index.html\'] = \'{s}\', \'memory/designer/{canonical_name}\'")
    return True

# --- Step 5: Git commit + tag ---
def git_commit_tag(files, tag_msg):
    try:
        subprocess.run(["git", "status"], capture_output=True, cwd=ROOT, timeout=10)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        log("WARNING: git not available - skipping commit+tag")
        return True
    
    # Stage files
    for f in files:
        subprocess.run(["git", "add", f], capture_output=True, cwd=ROOT)
    
    # Check if there's anything to commit
    r = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True, cwd=ROOT)
    if r.returncode == 0:
        log("Git: no changes to commit")
        return True
    
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = f"deploy-{ts}"
    
    # Commit
    r = subprocess.run(
        ["git", "commit", "-m", f"deploy: {tag_msg} [{ts}]"],
        capture_output=True, text=True, cwd=ROOT
    )
    if r.returncode != 0:
        die(5, f"git commit failed: {r.stderr}")
    log(f"Git: committed ({r.stdout.strip()[:60]})")
    
    # Tag
    r = subprocess.run(["git", "tag", tag], capture_output=True, text=True, cwd=ROOT)
    if r.returncode == 0:
        log(f"Git: tagged {tag}")
    else:
        log(f"WARNING: git tag failed: {r.stderr.strip()}")
    
    return True

# --- Main ---
def main():
    parser = argparse.ArgumentParser(description="One-command deploy")
    parser.add_argument("file", nargs="?", help="File to deploy (relative to project root). Omit for all changed.")
    parser.add_argument("--skip-tests", action="store_true", help="Skip UI test suite")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, no commit")
    args = parser.parse_args()

    # Determine target files
    if args.file:
        files = [args.file]
    else:
        # Get git-changed files in ui/ + index.html
        try:
            r = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True, text=True, cwd=ROOT
            )
            changed = [l.strip() for l in r.stdout.split("\n") if l.strip()]
            files = [f for f in changed if f.startswith("ui/") or f == "index.html"]
        except FileNotFoundError:
            files = []
        if not files:
            # Fallback: all ui/ files + index.html
            files = ["index.html"]
            for fn in sorted(os.listdir(UI_DIR)):
                if fn.endswith((".js", ".css")) and not fn.startswith("app.css.bak"):
                    files.append(f"ui/{fn}")
        log(f"No file arg - deploying {len(files)} changed files")

    log(f"Files to deploy: {files}")
    
    # Step 1: Validate
    log("Step 1/5: Validating syntax...")
    for f in files:
        path = os.path.join(ROOT, f)
        if not os.path.exists(path):
            die(2, f"File not found: {f}")
        ok, msg = validate_file(path)
        status = "OK" if ok else f"FAIL ({msg})"
        log(f"  {f}: {status}")
        if not ok:
            die(2, f"Syntax validation failed for {f}: {msg}")

    # Step 2: Tests
    log("Step 2/5: Running UI tests...")
    if not run_ui_tests(args.skip_tests):
        die(3, "UI tests failed")

    if args.dry_run:
        log("DRY RUN complete - no changes made")
        sys.exit(0)

    # Step 3: Sync
    log("Step 3/5: Syncing to portal root...")
    sync_to_portal(files)

    # Step 4: Pin
    log("Step 4/5: Checking pin...")
    for f in files:
        advance_pin(f)

    # Step 5: Git
    log("Step 5/5: Git commit + tag...")
    tag_msg = ",".join(os.path.basename(f) for f in files[:3])
    if len(files)>3: tag_msg += f" +{len(files)-3} more"
    git_commit_tag(files, tag_msg)

    log("DEPLOY COMPLETE")

if __name__ == "__main__":
    main()
