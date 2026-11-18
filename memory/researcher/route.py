# Fleet Question Router (Researcher cycle-5 goal 6)
# /api/research/route ?q=<free text> -> which agent(s) should answer.
# Ranking = keyword overlap between the question and each agent's goal file
# (memory/goals/<agent>.md) + a role-seed topic map. Self-contained, never raises.
import os, re, json

HERE = os.path.dirname(os.path.abspath(__file__))
_GOALS_DIR = os.path.join(HERE, "..", "goals")
_AGENTS_FILE = os.path.normpath(os.path.join(HERE, "..", "..", "agents.json"))

# Role-seed topics: baseline signal when goal files are thin or missing.
ROLE_SEED = {
    "orchestrator": ["goal", "plan", "roadmap", "assign", "coordinate", "onboard",
                     "todo", "prioritiz", "dispatch", "cycle", "backlog", "seat"],
    "researcher": ["research", "investigate", "source", "reliab", "confidence",
                   "evidence", "verif", "cross-check", "kb", "terminolog", "drift", "sla", "brief"],
    "builder": ["build", "implement", "feature", "code", "snippet", "app", "endpoint",
                "api", "function", "component", "increment"],
    "verifier": ["test", "verify", "proof", "pass", "fail", "assert", "latency",
                 "reproduc", "evidence-based", "regression"],
    "designer": ["ui", "css", "layout", "frontend", "canvas", "render_html", "mockup",
                "mobile", "responsive", "visual", "token", "component"],
    "archivist": ["archive", "memory", "index", "retrieve", "reference", "dictionary",
                 "knowledge-base", "record", "history", "citation"],
    "scribe": ["synthes", "compress", "decision", "log", "summary", "minutes",
               "narrative", "close-out", "consensus"],
    "mechanic": ["ops", "host", "reboot", "probe", "health", "disk", "uptime",
                 "monitor", "fleet-health", "recover", "elevation", "helper"],
}

_STOP = set("a an the and or of to in on for with this that is are was were be been it its as by at from not no yes i you we they he she can could will would should do does did what which who how why when where if then than so such only own same just about into over under again once here there all any both each few more most other some too very s t don didn won isn aren wasn weren has have had having will shall may might must".split())


def _tokenize(text):
    toks = re.findall(r"[a-z][a-z0-9\-]{2,}", (text or "").lower())
    return [t for t in toks if t not in _STOP]


def _load_agent_names():
    try:
        d = json.load(open(_AGENTS_FILE, encoding="utf-8"))
        names = [a["name"].lower() for a in d.get("agents", [])]
        if names:
            return names
    except Exception:
        pass
    return list(ROLE_SEED.keys())


def _goal_keywords(agent):
    """Extract weighted topic terms from an agent's goal file (title lines weigh 3x)."""
    path = os.path.join(_GOALS_DIR, agent + ".md")
    weights = {}
    if not os.path.exists(path):
        return weights
    try:
        for line in open(path, encoding="utf-8", errors="replace"):
            stripped = line.strip()
            is_title = bool(re.match(r"^\s*(#|\d+\.|[A-Z0-9][^:]*:\s*)", stripped)) or (stripped.startswith("**") and "**" in stripped[2:])
            for t in _tokenize(stripped):
                weights[t] = weights.get(t, 0) + (3 if is_title else 1)
    except Exception:
        pass
    return weights


def route(question):
    """Return ranked agents for a free-text question. Never raises."""
    try:
        qtoks = _tokenize(question)
        if not qtoks:
            return {"ok": True, "question": question, "agents": [],
                    "note": "no routable terms found in question"}
        # seed tokens always count lightly so a bare role keyword still routes
        scored = []
        for agent in _load_agent_names():
            seed = [t for t in ROLE_SEED.get(agent, [])]
            goalw = _goal_keywords(agent)
            hits = []
            score = 0.0
            for qt in qtoks:
                # exact match against seed or goal keywords (with stemming via prefix)
                w = 0.0
                matched_term = None
                if qt in seed or any(s.startswith(qt) or qt.startswith(s) for s in seed):
                    w += 2.0
                    matched_term = qt
                if qt in goalw:
                    w += min(goalw[qt], 6) / 3.0
                    matched_term = matched_term or qt
                # prefix match against goal keywords (e.g. 'verif' -> 'verify')
                elif any(g.startswith(qt[:4]) for g in goalw if len(g) >= 4):
                    w += 1.0
                    matched_term = matched_term or qt
                if w > 0:
                    score += w
                    hits.append(matched_term)
            scored.append((score, agent, sorted(set(hits))))
        scored.sort(key=lambda x: (-x[0], x[1]))
        top = [a for a in scored if a[0] > 0]
        maxs = top[0][0] if top else 1.0
        out = []
        for s, agent, hits in top[:4]:
            out.append({"agent": agent.capitalize(), "score": round(s, 2),
                        "confidence": round(min(1.0, s / (maxs * 1.5)), 2),
                        "matched_terms": hits[:8]})
        return {"ok": True, "question": question,
                "primary": out[0]["agent"] if out else None,
                "agents": out,
                "note": ("no strong match - default to Orchestrator for routing"
                         if not out else f"{len(out)} candidate(s) ranked by topic overlap")}
    except Exception as e:
        return {"ok": False, "error": str(e), "question": question, "agents": []}


if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "how do I fix a host reboot issue?"
    print(json.dumps(route(q), indent=2))
