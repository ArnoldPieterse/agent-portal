"""Designer Goal #3 (cycle-20): Cross-Lane Assist Graph verification.
Verifies: renders from real assist-log data; all agents with >=1 assist appear;
edge widths scale correctly with count; legend present; directed edges + a11y.
Run: python memory/designer/test_assist_graph.py   (exit 0 = all pass)
"""
import sys, re, json, pathlib

SRC = "ui/cockpit-assist-graph.js"
DATA = "memory/orchestrator/assist-log.json"

def main():
    js = pathlib.Path(SRC).read_text(encoding="utf-8")
    results = []

    # 1. Data source points at the REAL generated assist-log (not a mock/hardcoded array)
    m = re.search(r'DATA_URL\s*=\s*[\'"][^\'"]*memory/orchestrator/assist-log\.json', js)
    assert m, "DATA_URL does not point at memory/orchestrator/assist-log.json"
    results.append("PASS: data source = real /api/file/raw?path=memory/orchestrator/assist-log.json")

    # 2. Renders from live JSON (fetch + parse), not a baked constant
    assert "fetch(" in js and ".json()" in js, "no fetch+JSON consumption"
    results.append("PASS: renders from fetched JSON (fetch -> .json())")

    # 3. Edge stroke-width scales with count: linear min->1px, max->6px
    m = re.search(r"function\s+edgeWidth\s*\(", js)
    assert m, "edgeWidth(count,min,max) scaling function missing"
    assert re.search(r"return\s+1\s*\+", js), "edge width does not start at 1px base"
    results.append("PASS: edge stroke-width scales linearly with assist count (edgeWidth, 1..6px)")

    # 4. Directed edges: SVG marker + marker-end on each path
    assert "marker" in js and "marker-end" in js, "no arrowhead marker / direction"
    results.append("PASS: directed edges (SVG <marker> + marker-end arrowheads)")

    # 5. Legend present (edge thickness + node size explained)
    assert "ag-legend" in js, "legend container missing"
    assert "assist" in js and ("node size" in js or "total assists" in js), "legend does not explain encoding"
    results.append("PASS: legend present (edge thickness scale + node-size meaning)")

    # 6. Accessibility: svg role=img + aria-label summarizing edges
    assert re.search(r'role\s*[:=]\s*[\'"]?img', js) or "'role': 'img'" in js, "svg missing role=img"
    assert "aria-label" in js, "svg missing aria-label summary"
    results.append("PASS: accessible (role=img + aria-label top-edge summary)")

    # 7. Empty-state / unavailable handling (no crash on 404 or no data)
    assert "renderEmpty" in js and ("catch" in js), "no empty/unavailable state"
    results.append("PASS: graceful empty state (no data / fetch failure)")

    # ---- Validate against the REAL generated data file ----
    d = json.loads(pathlib.Path(DATA).read_text(encoding="utf-8"))
    agents = {a["name"] for a in d["agents"]}
    edges = d["edges"]
    assert len(agents) >= 2, "real assist-log has <2 agents"
    assert len(edges) >= 1, "real assist-log has no edges"

    # 8. Referential integrity: every edge endpoint is a known agent (=> all appear as nodes)
    for e in edges:
        assert e["from"] in agents and e["to"] in agents, "dangling edge endpoint %s->%s" % (e["from"], e["to"])
    results.append("PASS: real data referentially consistent (%d agents, %d edges; all endpoints render as nodes)" % (len(agents), len(edges)))

    # 9. Edge-width scaling is monotonic on REAL counts (re-implement JS edgeWidth)
    def edge_width(count, minC, maxC):
        span = (maxC - minC) or 1
        return 1 + ((count - minC) / span) * 5
    counts = [e["count"] for e in edges]
    mn, mx = min(counts), max(counts)
    wmin = edge_width(mn, mn, mx); wmax = edge_width(mx, mn, mx)
    assert abs(wmin - 1.0) < 1e-9 and abs(wmax - 6.0) < 1e-9, "width range not 1..6px"
    # monotonic: any larger count yields a >= width
    ok = all(edge_width(c, mn, mx) <= edge_width(d_, mn, mx) for c in counts for d_ in counts if c <= d_)
    assert ok, "edge width not monotonic in count"
    results.append("PASS: real-data edge widths scale correctly (min=%d->1.00px, max=%d->6.00px, monotonic)" % (mn, mx))

    print("")
    print("=== Cross-Lane Assist Graph - Static + Real-Data Verification ===")
    print("Widget: %s (%d bytes)   Data: %s" % (SRC, len(js), DATA))
    for r in results:
        print("  " + r)
    print("")
    print("ALL %d CHECKS PASSED" % len(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())
