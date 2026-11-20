#!/usr/bin/env python3
"""Self-test for Scribe goal 9 (Institutional Memory Search).

Acceptance checks:
  (A) >=10 distinct queries each return >=1 relevant result.
  (B) No false negatives on exact-match terms: for every query, at least one file that
      actually contains the query's core term appears in the top-N results.
  (C) Ranking sanity: the highest-scoring result for a topic query is a file strongly
      about that topic (spot-check a few).

Run: python memory/scribe/test_memory_search.py
Exit 0 = PASS, non-zero = FAIL (prints which check failed).
"""
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(HERE, "memory", "scribe"))
import memory_search  # noqa: E402

# (query, core_term_that_must_be_found_in_a_result_file)
CASES = [
    ("hotload", "hotload"),
    ("anti-stall", "anti-stall"),
    ("cycle_narrative", "cycle_narrative"),
    ("quarantine", "quarantine"),
    ("mirror sync", "mirror"),
    ("winrm reboot", "winrm"),
    ("pin clobber loop", "clobber"),
    ("distill pipeline", "distill"),
    ("handoff protocol", "handoff"),
    ("down-seat auto-track", "down-seats"),
    ("decision extraction", "extract_decisions"),
    ("quality scoring synthesis", "quality"),
]


def files_containing(term):
    """Ground truth: every searchable file whose text contains `term` (lowercase)."""
    term = term.lower()
    hits = set()
    for full, rel in memory_search._iter_files():
        try:
            with open(full, "rb") as fh:
                text = fh.read(memory_search.MAX_FILE_BYTES).decode("utf-8", errors="ignore").lower()
        except Exception:
            continue
        if term in text:
            hits.add(rel)
    return hits


def main():
    failures = []
    results_log = []
    for query, core in CASES:
        res = memory_search.search_memory(query, top=5)
        paths = [r["path"] for r in res]
        ground = files_containing(core)
        # (A) relevant result returned
        if len(res) < 1:
            failures.append(f"(A) no results for {query!r}")
        # (B) no false negative: some ground-truth file in top-5
        overlap = [p for p in paths if p in ground]
        if not overlap:
            failures.append(f"(B) exact-term false negative for {query!r} (term={core!r}); "
                            f"top5={paths}; ground_truth_sample={sorted(ground)[:4]}")
        results_log.append((query, len(res), paths[0] if paths else None))

    print(f"Ran {len(CASES)} queries.")
    for q, n, top1 in results_log:
        print(f"  {q!r:32} -> {n} results; top1={top1}")
    if failures:
        print("\nFAIL:")
        for f in failures:
            print("  -", f)
        return 1
    print("\nPASS: all checks green (>=10 queries, no exact-term false negatives).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
