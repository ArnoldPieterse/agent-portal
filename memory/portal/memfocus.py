#!/usr/bin/env python3
"""MemFocus - LOD cursor over the index-regex memory recall (2026-11-25).

Arnold's idea: the regex memory index + DNA recall doubles as a system focus/cursor,
like Level of Detail in rendering. When new memories are recalled, we garbage-collect
memories not required for the moment: they are PARKED (audit log; still re-recallable
via the index - never deleted) and only what the host can provide at that time is kept
at full detail, so recall never overloads a loaded host.

Tiers per recall round:
  T2 IN FOCUS   full line text, within the host char budget
  T1 POINTER    file:line + score only (agent fetches with tools if it matters)
  T0 PARKED     evicted from this round's window -> memfocus-parked.jsonl audit line

Pure functions; importable without the portal. State: memory/portal/memfocus-state.json,
audit: memory/portal/memfocus-parked.jsonl. Never raises (recall must not break chat).
"""
import hashlib, json, os, re, time

HERE = os.path.dirname(os.path.abspath(__file__))   # memory/portal
ROOT = os.path.dirname(os.path.dirname(HERE))       # project root
STATE_F = os.path.join(HERE, "memfocus-state.json")
PARK_F = os.path.join(HERE, "memfocus-parked.jsonl")
METRICS_F = os.path.join(ROOT, "memory", "ops", "fleet-metrics.jsonl")
LINE_COST = 140          # ~chars per T2 line incl. prefix (line text capped at 110)
BUDGET_BASE = 2400       # T2 char budget on an idle host
BUDGET_MIN = 700         # floor: even a loaded host gets some full detail

STOP = set("a an and are as at be but by for from had has have he her his i if in into is it its me my no not of on or our she so that the their them they this to was we were what when where which who will with you your about after again all also any because been before being between both can could did do does doing down during each few here how him herself himself more most other out over own same some such than then there those through too under until up very while within without would should may might must shall".split())


def focus_terms(text, extra=()):
    """Weighted terms for the focus window (prompt words + live-plan topic words)."""
    t = {}
    for w in re.findall(r"[a-z0-9_]{3,}", (text or "").lower()):
        if w not in STOP:
            t[w] = t.get(w, 0) + 1
    for w in extra:
        t.setdefault(w, 0)
    return t


def host_budget_chars(host_name=None):
    """T2 char budget scaled by what the seat's host can provide RIGHT NOW.
    Reads the newest fleet-metrics.jsonl record; unknown host -> conservative fleet-max;
    any failure -> safe middle default. Never raises."""
    try:
        rec = None
        with open(METRICS_F, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
        vram = cpu = None
        hosts = (rec or {}).get("hosts") or []
        if host_name:
            hn = str(host_name).lower()
            for h in hosts:
                if (h.get("name") or "").lower() == hn:
                    vram, cpu = h.get("vram_pct"), h.get("cpu_pct")
                    break
        if vram is None and hosts:
            vram = max((h.get("vram_pct") or 0) for h in hosts)
        if vram is None:
            vram = (rec or {}).get("gpu_usage_pct") or 0
        f = max(0.35, min(1.0, 1.0 - 0.6 * (float(vram) / 100.0)))
        if cpu is not None and float(cpu) > 80:
            f *= 0.7
        return int(max(BUDGET_MIN, min(BUDGET_BASE, BUDGET_BASE * f)))
    except Exception:
        return 1500


def load_state():
    try:
        return json.load(open(STATE_F, encoding="utf-8"))
    except Exception:
        return {"window": [], "focus_sig": "", "parked_total": 0,
                "last_gc_ts": None, "rounds": 0}


def save_state(st):
    try:
        st["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        json.dump(st, open(STATE_F, "w", encoding="utf-8"), indent=1)
    except Exception:
        pass


def park(refs, focus_sig):
    """T0: append evicted refs to the audit log. Returns count parked (0 on failure)."""
    if not refs:
        return 0
    try:
        with open(PARK_F, "a", encoding="utf-8") as f:
            for rel, n in refs:
                f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                    "ref": [rel, int(n)], "focus_sig": focus_sig,
                                    "reason": "lod-evict"}) + "\n")
        return len(refs)
    except Exception:
        return 0


def split_tiers(scored, budget):
    """scored = [((rel,line), score), ...] sorted desc. -> (t2 full, t1 pointer, rest)."""
    t2, t1, rest, used = [], [], [], 0
    for key, sc in scored:
        if used < budget:
            t2.append((key, sc)); used += LINE_COST
        elif len(t1) < 4:
            t1.append((key, sc))
        else:
            rest.append((key, sc))
    return t2, t1, rest


def gc_round(prev_window, new_top):
    """Refs in the previous focus window that fell out of this round's top set."""
    cur = {tuple(k) for k, _s in new_top}
    return [r for r in (prev_window or []) if tuple(r) not in cur]