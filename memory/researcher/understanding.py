"""UNDERSTANDING MODULE (2026-11-18) -- key-term meaning + usage for pre-context.

Pipeline: latest prompt -> key terms -> (a) SYNONYM expansion feeds the memory
index lookup in agent_portal._mem_local_hits, and (b) DICTIONARY lookup gives
each term its meaning + usage; both are indexed with U-refs and pointers into
memory/researcher/dictionary_*.json, folded into pre-context before the main
LLM prompt. ReadMem/StoreMem rounds then see the same terms already resolved.

Files (siblings): goal_ledger.py (goal evidence), dictionary_core.json,
dictionary_project.json. Parent pointer: memory/INDEX.md.
Never raises; every public function degrades to '' / [] on any failure."""
import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
DICT_FILES = [os.path.join(_HERE, "dictionary_core.json"),
              os.path.join(_HERE, "dictionary_project.json")]

_STOP = set("a an the and or but if then else when while for to of in on at by with from into over under "
            "is are was were be been being do does did done have has had having will would shall should can could "
            "may might must not no yes i you he she it we they me him her us them my your his its our their "
            "this that these those there here what which who whom whose how why all any both each few more most "
            "other some such only own same so than too very just also now please can could would should i'm don't "
            "it's let get got make made take took say said know think want need look see show give use put set "
            "one two three first last new old big small good bad yes no ok okay well back out up down off again "
            "still further once here where why how please tell show give add fix complete continue reboot".split())

# --- synonym groups (base forms; stemming covers inflections) -----------------
_GROUPS = [
    ("error", "bug", "fault", "defect", "issue", "mistake"),
    ("fix", "repair", "correct", "resolve", "solve", "patch", "amend"),
    ("build", "create", "make", "construct", "develop", "compile"),
    ("test", "verify", "check", "validate", "confirm", "assure"),
    ("stall", "stuck", "halt", "block", "freeze", "jam", "holdup"),
    ("memory", "recall", "remember", "recollection", "retention", "store"),
    ("context", "background", "setting", "situation", "scope"),
    ("prompt", "request", "query", "instruction", "ask"),
    ("reply", "response", "answer", "reaction"),
    ("goal", "target", "objective", "aim", "purpose"),
    ("task", "job", "work", "duty", "chore"),
    ("progress", "advance", "momentum"),
    ("complete", "finish", "end", "conclude", "wrap"),
    ("blocker", "obstacle", "barrier", "impediment", "hindrance", "gate"),
    ("queue", "backlog", "stack", "lineup"),
    ("fast", "quick", "rapid", "swift", "speedy"),
    ("slow", "sluggish", "delayed", "lagging", "drag"),
    ("cheap", "inexpensive", "affordable"),
    ("expensive", "costly", "pricey"),
    ("improve", "enhance", "upgrade", "refine", "optimize"),
    ("remove", "delete", "drop", "erase", "eliminate", "discard"),
    ("add", "append", "insert", "include", "attach", "incorporate"),
    ("update", "refresh", "renew", "revise", "modify"),
    ("restart", "reboot", "reload", "reset", "reinitialize"),
    ("crash", "fail", "break", "collapse"),
    ("run", "execute", "launch", "start", "trigger", "invoke"),
    ("search", "find", "locate", "scan", "seek"),
    ("index", "catalog", "registry", "listing"),
    ("pointer", "reference", "ref", "link", "marker", "signpost"),
    ("synonym", "equivalent", "paraphrase", "counterpart"),
    ("meaning", "definition", "sense", "significance", "interpretation"),
    ("usage", "use", "application", "employment"),
    ("term", "word", "phrase", "vocabulary"),
    ("dictionary", "glossary", "thesaurus", "lexicon"),
    ("module", "component", "section", "unit", "piece"),
    ("function", "method", "routine", "procedure", "operation", "capability"),
    ("file", "document", "record", "entry", "item"),
    ("folder", "directory", "dir", "container", "archive"),
    ("path", "route", "way", "trail", "track"),
    ("server", "host", "machine", "node", "endpoint"),
    ("client", "consumer", "user", "caller"),
    ("browser", "navigator", "viewer"),
    ("page", "screen", "view", "display", "pane"),
    ("element", "widget", "control", "node"),
    ("click", "tap", "press", "select", "choose"),
    ("screenshot", "snapshot", "capture", "picture", "image", "photo"),
    ("render", "draw", "paint", "produce"),
    ("log", "trace", "history", "journal", "diary"),
    ("debug", "diagnose", "troubleshoot", "investigate", "examine"),
    ("monitor", "watch", "observe", "track", "surveil"),
    ("alert", "warning", "signal", "notice", "flag", "notification"),
    ("timeout", "expiry", "deadline", "cutoff"),
    ("budget", "allowance", "quota", "allocation", "cap", "limit"),
    ("parallel", "concurrent", "simultaneous"),
    ("process", "procedure", "workflow", "pipeline", "sequence"),
    ("service", "daemon", "utility", "facility"),
    ("sync", "synchronize", "align", "reconcile"),
    ("copy", "duplicate", "clone", "replica"),
    ("merge", "combine", "join", "unify", "integrate", "consolidate"),
    ("split", "divide", "separate", "partition"),
    ("filter", "screen", "sieve"),
    ("sort", "order", "arrange", "organize", "rank"),
    ("priority", "precedence", "importance", "urgency"),
    ("schedule", "timetable", "calendar", "plan", "timeline"),
    ("delay", "postpone", "defer", "hold", "wait"),
    ("pause", "suspend", "interrupt"),
    ("resume", "continue", "proceed"),
    ("private", "personal", "confidential", "secret"),
    ("public", "open", "shared", "common"),
    ("visible", "shown", "displayed", "apparent", "evident"),
    ("hidden", "concealed", "masked", "buried", "obscure"),
    ("send", "transmit", "dispatch", "deliver", "post", "push"),
    ("receive", "accept", "take", "collect", "pull"),
    ("share", "distribute", "broadcast", "disseminate", "propagate"),
    ("message", "communication", "note", "signal"),
    ("session", "conversation", "exchange", "dialogue", "discussion"),
    ("model", "representation", "pattern", "template", "prototype"),
    ("token", "symbol", "marker", "sign", "tag"),
    ("temperature", "creativity", "randomness", "variance"),
    ("stream", "flow", "cascade"),
    ("window", "frame", "viewport"),
    ("commit", "submit", "checkin"),
    ("version", "edition", "release", "iteration", "revision"),
    ("deploy", "publish", "ship"),
    ("install", "setup", "configure", "provision"),
    ("credential", "password", "passphrase", "secret"),
    ("login", "signin", "logon", "authenticate"),
    ("auth", "authorization", "permission", "approval", "clearance"),
    ("allowlist", "whitelist"),
    ("blocklist", "blacklist"),
    ("evidence", "proof", "confirmation", "verification"),
    ("verdict", "decision", "ruling", "judgment", "conclusion"),
    ("cycle", "iteration", "round", "loop", "pass"),
    ("fleet", "cohort", "ensemble", "group"),
    ("lane", "channel", "swimlane"),
    ("nudge", "reminder", "poke", "hint"),
    ("ack", "acknowledgement", "confirmation", "receipt"),
    ("silent", "quiet", "muted", "suppressed", "hushed"),
    ("concluded", "resolved", "settled", "closed"),
    ("pin", "anchor", "lock", "fasten"),
    ("mirror", "reflection", "twin"),
    ("clobber", "overwrite", "trample", "smash"),
    ("unblock", "clear", "free", "release"),
    ("delegate", "assign", "outsource"),
]

_syn_map = {}
for _g in _GROUPS:
    for _w in _g:
        _syn_map.setdefault(_w, set()).update(_g)

def synonyms(word):
    """All base-form equivalents of word (via stem + synonym groups); [] on failure."""
    try:
        out = set()
        for s in _stems(word.lower()):
            out.update(_syn_map.get(s, ()))
        return sorted(out)
    except Exception:
        return []

_IRR = {"built": "build", "went": "go", "made": "make", "took": "take", "came": "come",
        "ran": "run", "began": "begin", "found": "find", "kept": "keep", "sent": "send",
        "got": "get", "saw": "see", "gave": "give", "held": "hold", "told": "tell",
        "showed": "show", "broke": "break", "drew": "draw", "grew": "grow", "knew": "know",
        "threw": "throw", "drove": "drive", "done": "do", "stalled": "stall"}

def _stem(w):
    if w in _IRR:
        return _IRR[w]
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 5 and w.endswith("ing"):
        return w[:-3]
    if len(w) > 4 and w.endswith("ed"):
        return w[:-2]
    if len(w) > 4 and w.endswith("ly"):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w

def _stems(w):
    s = _stem(w)
    return {w, s} | ({_stem(s)} if s != w else set())

def expand(words):
    """Expand each word with its synonym base forms (deduped, original kept first)."""
    try:
        out, seen = [], set()
        for w in words:
            w = w.lower()
            if w not in seen:
                out.append(w); seen.add(w)
            for s in synonyms(w):
                if s not in seen:
                    out.append(s); seen.add(s)
        return out
    except Exception:
        return list(words)

# --- dictionary ---------------------------------------------------------------
_dict_cache = {}

def load_dictionary():
    """Load dictionary_*.json (term -> [definition, usage]); mtime-cached; {} on failure."""
    try:
        sig = tuple((f, os.path.getmtime(f)) for f in DICT_FILES if os.path.exists(f))
        if _dict_cache.get("sig") == sig and "d" in _dict_cache:
            return _dict_cache["d"]
        d = {}
        for f in DICT_FILES:
            if os.path.exists(f):
                try:
                    raw = json.load(open(f, encoding="utf-8"))
                    for k, v in raw.items():
                        if k.startswith("_"):
                            continue
                        if isinstance(v, (list, tuple)) and len(v) >= 1:
                            d[k.lower()] = [str(v[0]), str(v[1]) if len(v) > 1 else ""]
                except Exception:
                    pass
        _dict_cache["sig"], _dict_cache["d"] = sig, d
        return d
    except Exception:
        return {}

def lookup(words):
    """[(prompt_word, term, definition, usage)] for words found in the dictionary.
    Tries exact form then stems; first hit wins per prompt word."""
    try:
        d = load_dictionary()
        out, seen_terms = [], set()
        for w in words:
            w = w.lower()
            hit = None
            for cand in [w] + [_stem(w)] + synonyms(w):
                if cand in d and cand not in seen_terms:
                    hit = cand
                    break
            if hit:
                seen_terms.add(hit)
                out.append((w, hit, d[hit][0], d[hit][1]))
        return out
    except Exception:
        return []

def key_terms(text, limit=14):
    """Meaningful words of a prompt (stopwords removed, order of first appearance)."""
    try:
        words = re.findall(r"[a-z0-9_]{3,}", (text or "").lower())
        out, seen = [], set()
        for w in words:
            if w not in _STOP and w not in seen:
                out.append(w); seen.add(w)
            if len(out) >= limit:
                break
        return out
    except Exception:
        return []

def understanding_block(messages, limit=8):
    """Pre-context block: dictionary meanings + usage of the prompt's key terms,
    indexed U1..Un with pointers into memory/researcher/dictionary_*.json.
    '' when nothing matches or on any failure."""
    try:
        q = ""
        for m in reversed(messages or []):
            c = (m.get("content") or "").strip()
            if c and (m.get("speaker") or "").strip().lower() == "you":
                q = c
                break
        if not q:
            for m in reversed(messages or []):
                c = (m.get("content") or "").strip()
                if c:
                    q = c
                    break
        hits = lookup(key_terms(q))[:limit]
        if not hits:
            return ""
        out = ["UNDERSTANDING (key terms of this prompt -> dictionary meaning + usage; U-refs point to memory/researcher/dictionary_*.json):"]
        for i, (word, term, d, u) in enumerate(hits, 1):
            line = "U%d %s: %s" % (i, term, d)
            if u:
                line += " Usage: %s" % u
            out.append(line)
        return "\n".join(out)
    except Exception:
        return ""
