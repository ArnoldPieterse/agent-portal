"""modularity_check.py - Linter for the fleet file-modularity rule.

Enforces: INDEX.md files <= 1600 chars; leaf .md files in memory/ <= 4KB (4096 bytes).
Reports violations with exact line numbers where budget is exceeded.
Uses a baseline file to tolerate pre-existing violations; fails only on NEW ones.
Exit 0 = clean (no new violations), Exit 1 = new violations found.

Usage:
  python memory/builder/modularity_check.py [--verbose]       # compare vs baseline
  python memory/builder/modularity_check.py --update-baseline # re-record all as known
  python memory/builder/modularity_check.py --no-baseline     # strict: any violation fails
"""
import os, sys, json

# --- Configurable limits ---
INDEX_LIMIT_CHARS = 1600      # INDEX.md files (root or sub-index)
LEAF_LIMIT_BYTES  = 4096      # other .md leaf files in memory/
SCAN_ROOT         = "memory"  # directory to scan
EXT               = ".md"     # file extension to check
BASELINE_PATH     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modularity_baseline.json")

# --- Exclusions: dirs/files to skip ---
SKIP_DIRS   = {"__pycache__", "backups", "canary", "portal-recovery"}
SKIP_FILES  = {"MEMORY.md"}  # MEMORY.md has its own ~2KB rule elsewhere; skip here


def scan_tree(root):
    """Yield (relpath, filepath) for every .md file under root."""
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded dirs in-place
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in sorted(filenames):
            if fname.endswith(EXT) and fname not in SKIP_FILES:
                fpath = os.path.join(dirpath, fname)
                rel = os.path.relpath(fpath)
                yield rel, fpath


def check_file(rel, fpath):
    """Check one file. Returns (passed: bool, report_lines: list[str])."""
    try:
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except OSError as e:
        return False, [f"  ERROR reading {rel}: {e}"]

    is_index = os.path.basename(rel) == "INDEX.md"
    limit = INDEX_LIMIT_CHARS if is_index else LEAF_LIMIT_BYTES
    kind = "INDEX" if is_index else "leaf"

    # Measure in the right unit
    size = len(content) if is_index else len(content.encode('utf-8'))
    unit = "chars" if is_index else "bytes"

    if size <= limit:
        return True, [f"  OK   {rel} ({size:,}/{limit:,} {unit}, {kind})"]

    # Find the line number where budget is exceeded (1-indexed)
    lines = content.split('\n')
    cumulative = 0
    exceed_line = len(lines)  # default: last line
    for i, line in enumerate(lines, 1):
        # Add line + newline (except last line which may not have \n)
        line_size = len(line) + (1 if i < len(lines) else 0)
        cumulative += line_size
        if cumulative > limit:
            exceed_line = i
            break

    overage = size - limit
    lines_out = [
        f"  FAIL {rel}: {size:,}/{limit:,} {unit} ({kind}) — over by {overage:,}",
        f"       budget exceeded at line {exceed_line} (of {len(lines)} total)",
        f"       FIX: split into sub-modules with -> pointers; see memory/portal/file-modularity.md",
    ]
    return False, lines_out


def load_baseline():
    """Load the baseline set of known-violation file paths."""
    if not os.path.exists(BASELINE_PATH):
        return None
    with open(BASELINE_PATH, 'r') as f:
        data = json.load(f)
    return {v["file"] for v in data.get("violations", [])}


def write_baseline(violations):
    """Write the current violation set as the new baseline."""
    entries = []
    for rel, report in violations:
        # Parse size/limit from report[0]
        parts = report[0].split("/")
        try:
            size = int(parts[0].split()[-1].rstrip(":").replace(",", ""))
            limit_str = parts[1].split()[0].replace(",", "")
            limit = int(limit_str)
        except (IndexError, ValueError):
            size, limit = 0, 0
        unit_idx = report[0].find("chars") if "chars" in report[0] else -1
        unit = "chars" if unit_idx >= 0 else "bytes"
        ftype = "INDEX" if "INDEX" in report[0] else "leaf"
        entries.append({"file": rel, "size": size, "limit": limit, "type": ftype, "unit": unit})
    baseline = {
        "_comment": "Known modularity violations. Linter fails only on NEW violations not in this list.",
        "generated": __import__("datetime").date.today().isoformat(),
        "total_files_scanned": None,  # filled by caller
        "violations": sorted(entries, key=lambda v: v["file"])
    }
    with open(BASELINE_PATH, 'w') as f:
        json.dump(baseline, f, indent=2)


def main():
    verbose = "--verbose" in sys.argv
    update_baseline = "--update-baseline" in sys.argv
    no_baseline = "--no-baseline" in sys.argv

    print("=== MODULARITY CHECK ===")
    print(f"  Scan root: {SCAN_ROOT}/")
    print(f"  Limits: INDEX.md <= {INDEX_LIMIT_CHARS} chars | leaf .md <= {LEAF_LIMIT_BYTES} bytes")
    if no_baseline:
        print(f"  Mode: STRICT (no baseline - any violation fails)")
    elif update_baseline:
        print(f"  Mode: UPDATE BASELINE")
    else:
        print(f"  Mode: BASELINE ({BASELINE_PATH.split(os.sep)[-1]})")
    print()

    if not os.path.isdir(SCAN_ROOT):
        print(f"  ERROR: scan root '{SCAN_ROOT}' not found")
        sys.exit(1)

    violations = []
    total_files = 0
    pass_count = 0

    for rel, fpath in scan_tree(SCAN_ROOT):
        # Normalize to forward slashes for baseline comparison
        rel_norm = rel.replace(os.sep, "/")
        total_files += 1
        passed, report = check_file(rel, fpath)
        if passed:
            pass_count += 1
            if verbose:
                print(report[0])
        else:
            violations.append((rel_norm, report))

    # Load baseline for comparison
    baseline_set = None
    if not no_baseline and not update_baseline:
        baseline_set = load_baseline()

    # Determine NEW violations (not in baseline)
    new_violations = []
    known_count = 0
    for rel, report in violations:
        if baseline_set is not None and rel in baseline_set:
            known_count += 1
        else:
            new_violations.append((rel, report))

    # Print results
    if no_baseline:
        # Strict mode: show all violations
        for rel, report in violations:
            for line in report:
                print(line)
        print()
        print(f"  Scanned: {total_files} .md files")
        print(f"  Pass:    {pass_count}/{total_files}")
        print(f"  Violations: {len(violations)}")
    else:
        for rel, report in new_violations:
            for line in report:
                print(line)
        print()
        print(f"  Scanned: {total_files} .md files")
        print(f"  Pass:    {pass_count}/{total_files}")
        print(f"  Total violations: {len(violations)} ({known_count} known, {len(new_violations)} NEW)")

    # Handle --update-baseline
    if update_baseline:
        write_baseline(violations)
        print(f"\n=== BASELINE UPDATED: {len(violations)} violations recorded ===")
        sys.exit(0)

    # Exit based on new violations (or all in strict mode)
    fail_list = violations if no_baseline else new_violations
    if fail_list:
        print(f"\n=== RESULT: FAIL ({len(fail_list)} {'new ' if not no_baseline else ''}violations) ===")
        sys.exit(1)
    else:
        msg = "PASS (no new violations)" if not no_baseline else "PASS (all within budget)"
        print(f"\n=== RESULT: {msg} ===")
        sys.exit(0)


if __name__ == "__main__":
    main()
