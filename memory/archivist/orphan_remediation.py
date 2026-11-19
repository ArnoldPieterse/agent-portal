"""
orphan_remediation.py - Archivist Goal #1: auto-link orphan nodes in the knowledge graph.

Reads kg_state / knowledge_graph.json, finds orphans (no inbound edges), classifies them,
and for those needing links, appends a pointer line to the closest parent INDEX.md under
a "Linked content" section. Applies changes and reports before/after counts.

Usage:
    python memory/archivist/orphan_remediation.py            # dry-run (report only)
    python memory/archivist/orphan_remediation.py --apply    # apply links to INDEX.md files
    python memory/archivist/orphan_remediation.py --json     # emit machine-readable report
"""
import json, os, re, sys, argparse
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]  # project root (two levels up from memory/archivist/)
KG_PATH = ROOT / "memory" / "archivist" / "knowledge_graph.json"
ALLOWLIST_PATH = ROOT / "memory" / "archivist" / "orphan-allowlist.json"
REPORT_PATH = ROOT / "memory" / "archivist" / "orphan-remediation-cycle5.md"
LINK_SECTION_HEADER = "## Linked content (KG orphan remediation)"


def load_kg() -> dict:
    with open(KG_PATH, encoding="utf-8") as f:
        return json.load(f)


def find_orphans(kg: dict) -> list:
    """Return nodes that have no inbound edges (no other file points to them)."""
    nodes = set()
    inbound = defaultdict(int)
    for e in kg.get("edges", []):
        src, dst = e.get("from", ""), e.get("to", "")
        if src:
            nodes.add(src)
        if dst:
            nodes.add(dst)
            inbound[dst] += 1
    # also add root node if present
    root = kg.get("root")
    if root:
        nodes.add(root)
    orphans = sorted(n for n in nodes if inbound.get(n, 0) == 0)
    return orphans


def classify(path: str) -> tuple[str, str]:
    """Return (category, reason). Category is 'standalone' or 'needs-link'."""
    p = path.replace("\\", "/")
    name = p.split("/")[-1].lower()

    # Rule 1: INDEX.md files are entry points
    if name == "index.md":
        return ("standalone", "Entry point / navigation hub - no inbound link needed")

    # Rule 2: scripts
    if name.endswith((".py", ".sh", ".ps1", ".js")):
        return ("standalone", "Tool script - invoked directly, not referenced by content")

    # Rule 3: data files
    if name.endswith((".json", ".jsonl", ".yaml", ".yml", ".csv")):
        return ("standalone", "Data file - consumed by scripts, not linked from prose")

    # Rule 4: __pycache__ / compiled artifacts
    if "__pycache__" in p or name.endswith(".pyc"):
        return ("standalone", "Compiled artifact - auto-generated, not content")

    # Rule 5: merge-queue files (transient)
    if "/merge-queue/" in p:
        return ("standalone", "Merge queue transient file - not permanent content")

    # Rule 6: dated evidence/report artifacts (point-in-time snapshots)
    # Heuristic: filename contains a date pattern YYYY-MM-DD or rNN round marker
    if re.search(r"(20\d{2}-\d{2}-\d{2}|r\d{1,3}[a-z]?[-_]|-cycle|_cycle)", name):
        return ("standalone", "Dated evidence/report artifact - point-in-time snapshot")

    # Rule 7: goal files in memory/goals/
    if p.startswith("memory/goals/") and p.endswith(".md"):
        return ("standalone", "Goal file - referenced by ledger, not content-linked")

    # Rule 8: MEMORY.md / TODO.md at seat root -> needs link from seat INDEX.md
    if name in ("memory.md", "todo.md") and p.count("/") <= 3:
        return ("needs-link", "Seat state file - should be linked from parent INDEX.md")

    # Rule 9: .md content files that are not dated, not goals -> needs link
    if name.endswith(".md"):
        return ("needs-link", "Content file with no inbound edges; suggest adding pointer from parent INDEX.md")

    # Default: standalone (unknown type, leave alone)
    return ("standalone", "Uncategorized - left as standalone by default")


def parent_index_for(path: str) -> str:
    """Return the path to the parent seat/domain INDEX.md that should link this file."""
    parts = path.replace("\\", "/").split("/")
    # memory/<seat>/file.md  ->  memory/<seat>/INDEX.md
    if len(parts) >= 3 and parts[0] == "memory":
        seat = parts[1]
        return f"memory/{seat}/INDEX.md"
    # memory/file.md -> memory/INDEX.md
    if len(parts) == 2 and parts[0] == "memory":
        return "memory/INDEX.md"
    return None


def load_allowlist() -> set:
    """Load manually-approved orphans that should NOT be auto-linked."""
    if ALLOWLIST_PATH.exists():
        with open(ALLOWLIST_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return set(data)
        if isinstance(data, dict):
            return set(data.get("allowlisted", []))
    return set()


def is_already_linked(index_path: str, target_path: str) -> bool:
    """Check if target_path already appears as a link in index_path."""
    idx_file = ROOT / index_path
    if not idx_file.exists():
        return False
    content = idx_file.read_text(encoding="utf-8")
    # Match markdown link [text](target) or bare target path
    escaped = re.escape(target_path.replace("\\", "/"))
    pattern = rf"[\(>]?{escaped}[\)]?"
    return bool(re.search(pattern, content))


def add_link(index_path: str, target_path: str) -> bool:
    """Append a link line under the LINK_SECTION_HEADER in index_path. Returns True if added."""
    idx_file = ROOT / index_path
    if not idx_file.exists():
        return False
    content = idx_file.read_text(encoding="utf-8")
    target_norm = target_path.replace("\\", "/")
    fname = target_norm.split("/")[-1]
    link_line = f"- [{fname}]({target_norm})"

    if LINK_SECTION_HEADER in content:
        # Insert after the header line (before existing entries or at end of that section)
        lines = content.split("\n")
        idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith(LINK_SECTION_HEADER):
                idx = i + 1
                break
        # Find the last existing link under this section, insert after it
        last_link_idx = idx - 1
        for i in range(idx, len(lines)):
            if lines[i].strip().startswith("- [") or lines[i].strip().startswith("- ") and "(memory/" in lines[i]:
                last_link_idx = i
            elif lines[i].startswith("## ") and i > idx:
                break  # next section starts, insert before it
        new_line = link_line
        if last_link_idx >= idx:
            lines.insert(last_link_idx + 1, new_line)
        else:
            lines.insert(idx, new_line)
        idx_file.write_text("\n".join(lines), encoding="utf-8")
    else:
        # No Linked content section yet - append one
        content = content.rstrip() + f"\n\n{LINK_SECTION_HEADER}\n{link_line}\n"
        idx_file.write_text(content, encoding="utf-8")
    return True


def main():
    ap = argparse.ArgumentParser(description="Orphan remediation for KG")
    ap.add_argument("--apply", action="store_true", help="Apply links (default: dry-run)")
    ap.add_argument("--json", action="store_true", help="Emit JSON report to stdout")
    args = ap.parse_args()

    kg = load_kg()
    orphans = find_orphans(kg)
    allowlist = load_allowlist()

    standalone, needs_link = [], []
    for orphan in orphans:
        if orphan in allowlist:
            standalone.append((orphan, "Allowlisted - manually approved as standalone"))
            continue
        cat, reason = classify(orphan)
        if cat == "standalone":
            standalone.append((orphan, reason))
        else:
            needs_link.append((orphan, reason))

    # For needs_link: determine target INDEX.md and check if already linked
    to_add, already_linked = [], []
    for orphan, reason in needs_link:
        parent_idx = parent_index_for(orphan)
        if parent_idx is None:
            standalone.append((orphan, "No parent INDEX.md determined - left alone"))
            continue
        if is_already_linked(parent_idx, orphan):
            already_linked.append((orphan, parent_idx))
        else:
            to_add.append((orphan, parent_idx, reason))

    # Apply links
    applied = skipped = 0
    for orphan, parent_idx, reason in to_add:
        if args.apply:
            ok = add_link(parent_idx, orphan)
            if ok:
                applied += 1
            else:
                skipped += 1
                print(f"  SKIP (parent not found): {orphan} -> {parent_idx}", file=sys.stderr)

    # Build report
    total_orphans = len(orphans)
    n_standalone = len(standalone) + len(already_linked)
    n_to_link = len(to_add)
    n_applied = applied if args.apply else 0
    n_remaining = n_to_link - (applied if args.apply else 0)

    report = {
        "total_nodes": kg.get("node_count", 0),
        "total_edges": kg.get("edge_count", 0),
        "orphans_total": total_orphans,
        "orphans_standalone": n_standalone,
        "orphans_needing_links": n_to_link + len(already_linked),
        "already_linked": len(already_linked),
        "to_add": len(to_add),
        "applied": n_applied,
        "skipped": skipped,
        "remaining_after": n_remaining,
        "apply_mode": args.apply,
        "orphan_rate_before": round(total_orphans / max(kg.get("node_count", 1), 1) * 100, 1),
        "orphan_rate_after": round(n_remaining / max(kg.get("node_count", 1), 1) * 100, 1),
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        mode = "APPLY" if args.apply else "DRY-RUN"
        print(f"\n=== Orphan Remediation Report ({mode}) ===")
        print(f"  Total nodes:          {report['total_nodes']}")
        print(f"  Total edges:          {report['total_edges']}")
        print(f"  Orphans (no inbound): {total_orphans} ({report['orphan_rate_before']}%)")
        print(f"  Classified standalone: {n_standalone}")
        print(f"  Already linked:       {len(already_linked)}")
        print(f"  To add links:         {len(to_add)}")
        if args.apply:
            print(f"  Applied:              {applied}")
            print(f"  Skipped:              {skipped}")
        print(f"  Remaining after:      {n_remaining} ({report['orphan_rate_after']}%)")
        if to_add and not args.apply:
            print(f"\n  First 10 to link (dry-run):")
            for orphan, parent_idx, reason in to_add[:10]:
                print(f"    {orphan}  ->  {parent_idx}")
        if applied > 0:
            print(f"\n  Applied {applied} links. Re-run knowledge_graph.py to refresh KG.")

    # Write summary leaf
    leaf = ROOT / "memory" / "archivist" / f"orphan-remediation-{mode.lower()}-report.md"
    with open(leaf, "w", encoding="utf-8") as f:
        f.write(f"# Orphan Remediation Report ({'Applied' if args.apply else 'Dry-run'})\n\n")
        for k, v in report.items():
            f.write(f"- {k}: {v}\n")
        f.write(f"\n## Links to add ({len(to_add)})\n")
        for orphan, parent_idx, reason in to_add:
            status = "APPLIED" if args.apply else "PENDING"
            f.write(f"- `{orphan}` -> `{parent_idx}` [{status}] - {reason}\n")

    print(f"\n  Report written: {leaf.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
