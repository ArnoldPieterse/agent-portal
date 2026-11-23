"""
Decision Audit Search Index - SQLite FTS5 over decision-log.jsonl
===============================================================
Builds and queries a full-text search index over all fleet decisions.

Usage:
  python memory/builder/decision_index.py --build       # (re)build the index
  python memory/builder/decision_index.py --search "query"  # full-text search
  python memory/builder/decision_index.py --stats       # index statistics
  python memory/builder/decision_index.py --selftest    # verify build+search work
"""
import json, sqlite3, sys, os
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE / "memory" / "builder" / "decision-index.db"
LOG_PATH = BASE / "memory" / "ops" / "decision-log.jsonl"


def build_index(verbose=True):
    """(Re)build the FTS5 index from decision-log.jsonl."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("""
        CREATE VIRTUAL TABLE decisions USING fts5(
            ts, agent, type, detail, severity, raw,
            content='decisions_content'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS decisions_content(
            id INTEGER PRIMARY KEY, ts TEXT, agent TEXT, type TEXT,
            detail TEXT, severity TEXT, raw TEXT
        )
    """)
    # Actually use contentless table for simpler approach
    conn.close()
    
    # Simpler: contentless FTS5
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("""
        CREATE VIRTUAL TABLE decisions USING fts5(
            ts, agent, type, detail, severity, raw,
            tokenize='unicode61'
        )
    """)
    
    count = 0
    if LOG_PATH.exists():
        for line in LOG_PATH.read_text(encoding="utf-8").strip().split("\n"):
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                ts = d.get("ts") or d.get("timestamp", "")
                agent = d.get("agent", "")
                dtype = d.get("type", "")
                detail = d.get("detail", "") or d.get("reason", "") or ""
                severity = d.get("severity", "INFO")
                raw = json.dumps(d)
                cur.execute(
                    "INSERT INTO decisions(ts, agent, type, detail, severity, raw) VALUES(?,?,?,?,?,?)",
                    (ts, agent, dtype, str(detail), severity, raw)
                )
                count += 1
            except json.JSONDecodeError:
                continue
    
    conn.commit()
    
    # Create convenience views
    cur.execute("""
        CREATE VIEW IF NOT EXISTS by_agent AS
        SELECT agent, COUNT(*) as n, MIN(ts) as first_ts, MAX(ts) as last_ts
        FROM decisions GROUP BY agent ORDER BY n DESC
    """)
    conn.commit()
    
    size = DB_PATH.stat().st_size
    if verbose:
        print(f"  Indexed {count} decisions -> {DB_PATH.name} ({size/1024:.1f} KB)")
    conn.close()
    return count


def search(query, limit=20):
    """Full-text search over the decision index. Returns list of dicts."""
    if not DB_PATH.exists():
        build_index(verbose=False)
    
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT ts, agent, type, detail, severity FROM decisions
            WHERE decisions MATCH ? ORDER BY rank LIMIT ?
        """, (query, limit))
        rows = cur.fetchall()
        results = [
            {"ts": r[0], "agent": r[1], "type": r[2], "detail": r[3], "severity": r[4]}
            for r in rows
        ]
    except sqlite3.OperationalError as e:
        # Fallback to LIKE if FTS query syntax fails
        cur.execute("""
            SELECT ts, agent, type, detail, severity FROM decisions
            WHERE raw LIKE ? ORDER BY ts DESC LIMIT ?
        """, (f"%{query}%", limit))
        rows = cur.fetchall()
        results = [
            {"ts": r[0], "agent": r[1], "type": r[2], "detail": r[3], "severity": r[4]}
            for r in rows
        ]
    conn.close()
    return results


def stats():
    """Return index statistics."""
    if not DB_PATH.exists():
        build_index(verbose=False)
    
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    agents = cur.execute("SELECT * FROM by_agent").fetchall()
    types = cur.execute(
        "SELECT type, COUNT(*) as n FROM decisions GROUP BY type ORDER BY n DESC"
    ).fetchall()
    date_range = cur.execute("SELECT MIN(ts), MAX(ts) FROM decisions").fetchone()
    conn.close()
    
    return {
        "total_decisions": total,
        "date_range": {"from": date_range[0], "to": date_range[1]},
        "by_agent": [{"agent": a[0], "count": a[1]} for a in agents],
        "by_type": [{"type": t[0], "count": t[1]} for t in types],
    }


def cmd_selftest():
    """Self-test: build index, search, verify results."""
    print("Decision Audit Search Index - selftest")
    ok = True
    
    # 1. Build
    n = build_index(verbose=True)
    if n == 0:
        print("  [FAIL] No decisions indexed")
        return False
    ok &= (n > 0)
    
    # 2. Search for a known term
    results = search("chaos")
    if len(results) == 0:
        # Try broader term
        results = search("recovery")
    if len(results) == 0:
        print(f"  [FAIL] No search results for 'chaos' or 'recovery' (index has {n} entries)")
        ok = False
    else:
        print(f"  [PASS] Search returned {len(results)} results")
    
    # 3. Stats
    s = stats()
    if s["total_decisions"] != n:
        print(f"  [FAIL] Stats mismatch: {s['total_decisions']} vs {n}")
        ok = False
    else:
        print(f"  [PASS] Stats: {s['total_decisions']} decisions, {len(s['by_agent'])} agents, "
              f"{len(s['by_type'])} types")
    
    # 4. Fallback LIKE search
    results2 = search("nonexistentterm_xyz123")
    if len(results2) != 0:
        print(f"  [FAIL] Expected 0 results for nonsense term, got {len(results2)}")
        ok = False
    else:
        print(f"  [PASS] Nonsense term returns 0 results")
    
    # 5. DB file exists and is valid
    if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
        print("  [FAIL] DB file missing or empty")
        ok = False
    else:
        print(f"  [PASS] DB file valid ({DB_PATH.stat().st_size/1024:.1f} KB)")
    
    print(f"\n  SELFTEST: {'ALL PASS' if ok else 'FAILURE'}")
    return ok


def main():
    args = sys.argv[1:]
    if not args or "--selftest" in args:
        cmd_selftest()
    elif "--build" in args:
        build_index()
    elif "--search" in args or "--query" in args:
        flag = "--search" if "--search" in args else "--query"
        q = args[args.index(flag) + 1] if args.index(flag) + 1 < len(args) else ""
        results = search(q)
        print(f"Results for '{q}': {len(results)}")
        for r in results:
            print(f"  [{r['severity']}] {r['ts'][:19]} | {r['agent']:12s} | {r['type']:16s} | {r['detail'][:50]}")
    elif "--stats" in args:
        s = stats()
        print(json.dumps(s, indent=2))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
