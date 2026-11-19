#!/usr/bin/env python3
"""archivist/retrieval_benchmark.py (cycle-5 goal 5) - Retrieval Quality Benchmark.
20 test queries with known-correct answer leaves (curated from file titles, NOT
from the retrieval method itself; each query may have several acceptable paths).
Measures precision@5, recall@10 and MRR of the current retrieval method
(kb_search TF-IDF). Writes memory/archivist/retrieval_metrics.json with all three
scores + per-query breakdown. Archives the previous metrics as
retrieval_metrics_prev.json so weekly_digest.py can report the delta.
CLI: python memory/archivist/retrieval_benchmark.py [--json]
"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kb_search as ks
ROOT = ks.ROOT
OUT = os.path.join(HERE, "retrieval_metrics.json")
PREV = os.path.join(HERE, "retrieval_metrics_prev.json")
# (query, [acceptable answer paths]) - curated 2026-11-19 from KB file titles.
QUERIES = [
    ("file modularity rule pointer budget ui modules", ["memory/portal/file-modularity.md"]),
    ("goal stall loop bug where agents re-edit index.html and pin guard fix", ["memory/portal/bugs/goal-stall-loop-2026-11-16.md", "memory/ops/pin-guard-extension-ui-files.md"]),
    ("fleet monitoring cadence escalation policy host outage", ["memory/ops/fleet-monitoring-cadence.md", "memory/portal/fleet-status.md"]),
    ("windows runbook scheduled tasks services", ["memory/ops/windows-runbook.md"]),
    ("boot deployment runbook portal startup steps", ["memory/ops/boot-deployment-runbook.md", "memory/ops/boot-detection-runbook.md"]),
    ("git hygiene commit message rules repo", ["memory/ops/git-hygiene.md"]),
    ("mirror clobber pattern remote sync overwrites local edits", ["memory/portal/mirror-clobber-pattern-2026-11-14.md", "memory/ops/mirror-revert-prevention-2026-11-18.md"]),
    ("portal API reference endpoints list", ["memory/portal/api-reference.md"]),
    ("portal architecture server frontend mirror overview", ["memory/portal/architecture.md", "memory/portal/system-map.md"]),
    ("live design tokens app.css root hex colors tokenized", ["memory/portal/design-tokens-live.md", "memory/portal/ui-tokens.md", "memory/portal/design-tokens.md"]),
    ("visual regression checklist UI changes", ["memory/portal/visual-regression-checklist.md"]),
    ("evidence closure protocol verified goals", ["memory/ops/evidence-closure-protocol.md"]),
    ("autoloop behaviour rules idle agents", ["memory/ops/autoloop.md", "memory/ops/autoloop-behaviour-hint-staleness-2026-11-18.md"]),
    ("hotline v2 escalation procedure", ["memory/ops/hotline-v2.md"]),
    ("sandbox egress self probe workaround blocked network", ["memory/ops/sandbox-egress-selfprobe-workaround-2026-11-19.md"]),
    ("remote host metrics probe spec disk memory", ["memory/ops/remote-host-metrics-probe-spec.md"]),
    ("pdf reporting workflow generated reports", ["memory/ops/pdf-reporting.md"]),
    ("memory sync spec SMB mirror rules r13", ["memory/ops/memory-sync-spec-r13.md"]),
    ("stale claim check fallback regression jsonl", ["memory/ops/stale-claim-check-fallback-regression-2026-11-19.md", "memory/ops/stale-claim-check-jsonl-fallback-2026-11-18.md"]),
    ("agent onboarding playbook new fleet host", ["memory/ops/agent-onboarding-playbook.md"]),
]

def run():
    ks.build_index(force=True)
    per = []
    for q, acc in QUERIES:
        res = ks.score_query(q)[:10]
        paths = [r["path"] for r in res]
        rank = next((i + 1 for i, p in enumerate(paths) if p in acc), None)
        per.append({"query": q, "acceptable": acc, "top5": paths[:5],
                    "rank": rank,
                    "in_top5": rank is not None and rank <= 5,
                    "in_top10": rank is not None and rank <= 10})
    n = len(per)
    p5 = sum(1 for r in per if r["in_top5"]) / n
    r10 = sum(1 for r in per if r["in_top10"]) / n
    mrr = sum((1.0 / r["rank"] if r["rank"] else 0.0) for r in per) / n
    out = {"run_ts": time.time(), "method": "tfidf (kb_search.py)", "n_queries": n,
           "precision_at_5": round(p5, 4), "recall_at_10": round(r10, 4),
           "mrr": round(mrr, 4), "queries": per}
    if os.path.exists(OUT):
        try: os.replace(OUT, PREV)
        except Exception: pass
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1)
    return out

if __name__ == "__main__":
    m = run()
    print("retrieval_benchmark: P@5=%.3f R@10=%.3f MRR=%.3f over %d queries -> %s"
          % (m["precision_at_5"], m["recall_at_10"], m["mrr"], m["n_queries"],
             os.path.relpath(OUT, ROOT)))
    for r in m["queries"]:
        mark = "OK@%d" % r["rank"] if r["rank"] else ("MISS")
        print("  [%s] %s" % (mark, r["query"][:70]))
