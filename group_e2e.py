# Group e2e - all 8 agents (orchestrator/researcher local + builder/verifier on Black .99
# + designer/archivist on Pale .39 + scribe/mechanic on Red .245).
# Replicates index.html send() group flow: parallel prompt phase, then cross-talk
# rounds with settled/[SILENT]/[CONCLUDED] semantics (MAX_CALLS=20, guard=8).
# 11-12: roster renamed atlas->orchestrator / quinn->researcher; Red pair merged.
import json, time, urllib.request, threading

PORTAL = 'http://127.0.0.1:8099'
AGENTS = ['orchestrator', 'researcher', 'builder', 'verifier',
          'designer', 'archivist', 'scribe', 'mechanic']
names = {}
ag = json.load(urllib.request.urlopen(PORTAL + '/api/agents'))
for a in ag['agents']:
    names[a['id']] = a['name']

PROMPT = ("Round-table planning, one sentence each: Orchestrator, propose our next portal feature. "
          "Builder, say what you would need to build it; Verifier, what you would need to verify it; "
          "Designer, what its UI/UX needs; Archivist, what research or knowledge-base note it should leave behind; "
          "Mechanic, flag any ops/fleet concerns for the 4-host setup; Scribe, compress the thread into a decision. "
          "Researcher, after the others have spoken, stress-test the proposal.")

def jget(path):
    return json.load(urllib.request.urlopen(PORTAL + path, timeout=30))

def _is_truncated(text, finish):
    """2026-11-16 (goal B5): True when a streamed reply was cut off - model signalled
    finish_reason='length', or the stream died mid function-call tag (unbalanced)."""
    if finish == 'length':
        return True
    t = text.replace(' ', '')
    if t.count('< tool_call>') != t.count('< /tool_call>'):
        return True
    if '<function=' in t and '< /function>' not in t:
        return True
    return False

def portal_chat(agent_id, messages, kind, timeout=600):
    body = {'agent_id': agent_id, 'mode': 'group', 'kind': kind, 'messages': messages}
    req = urllib.request.Request(PORTAL + '/api/chat', data=json.dumps(body).encode(), method='POST')
    content, thinking, meta, err, finish = [], [], None, None, None
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw in resp:
                line = raw.decode('utf-8', 'replace').strip()
                if not line.startswith('data:'):
                    continue
                payload = line[5:].strip()
                if payload == '[DONE]':
                    break
                try:
                    d = json.loads(payload)
                except Exception:
                    continue
                if d.get('content'):
                    content.append(d['content'])
                if d.get('thinking'):
                    thinking.append(d['thinking'])
                if d.get('meta'):
                    meta = d['meta']
                if d.get('finish_reason'):
                    finish = d['finish_reason']
                if isinstance(meta, dict) and meta.get('finish_reason'):
                    finish = meta['finish_reason']
                if d.get('error'):
                    err = str(d['error'])[:200]
    except Exception as e:
        err = err or repr(e)[:200]
    text = ''.join(content).strip()
    # 2026-11-16 (goal B5): truncation detection via _is_truncated() - pure fn,
    # unit-tested by test_truncation_detect.py (no live SSE needed to verify it).
    truncated = _is_truncated(text, finish)
    silent = concluded = False
    low = text.lower()
    if low.startswith('[silent]'):
        rest = text[len('[silent]'):].lstrip(' :-').strip()
        silent = not rest
        text = rest
    elif low.startswith('[concluded]'):
        concluded = True
        rest = text[len('[concluded]'):].lstrip(' :-').strip()
        text = rest or '(concluded)'
    return {'text': text, 'silent': silent, 'concluded': concluded,
            'truncated': truncated, 'finish': finish,
            'meta': meta, 'err': err, 'dt': round(time.time() - t0, 1),
            'think_len': sum(len(x) for x in thinking)}

def parallel_call(agent_ids, messages, kind):
    out = {}
    def run(aid):
        out[aid] = portal_chat(aid, messages, kind)
    ts = [threading.Thread(target=run, args=(a,)) for a in agent_ids]
    for t in ts: t.start()
    for t in ts: t.join()
    return out

def P(s):
    print(s, flush=True)

mem0 = jget('/api/memory')
P(f"counter BEFORE: {mem0.get('inter_agent_replies')} (limit={mem0.get('limit')})")

history = [{'speaker': 'You', 'content': PROMPT}]

# ---- Phase 1: parallel prompt (all 4, mirrors frontend Promise.all) ----
P("== PHASE 1: parallel prompt (all 6 agents) ==")
r1 = parallel_call(AGENTS, history, 'prompt')
for a in AGENTS:
    r = r1[a]
    tag = 'SILENT' if r['silent'] else ('CONCLUDED' if r['concluded'] else ('TRUNCATED' if r['truncated'] else ''))
    P(f"  {names[a]:9s} {r['dt']:5.1f}s think={r['think_len']:5d} {tag:9s} err={r['err']} :: {r['text'][:160]!r}")
for a in AGENTS:
    if r1[a]['text'] and not r1[a]['silent']:
        history.append({'speaker': names[a], 'content': r1[a]['text']})

mem1 = jget('/api/memory')
P(f"counter after prompt phase: {mem1.get('inter_agent_replies')} (prompt phase should NOT bump cross-talk)")

# ---- Phase 2: cross-talk rounds ----
settled, guard, calls, lastConcluded = set(), 0, 0, False
trunc_agents = []   # 2026-11-16 (goal B5): agents with truncated replies, any phase
MAX_CALLS = 20  # 8 agents: phase-1 alone is 8 calls (was 12 for the 6-agent roster)
while not lastConcluded and guard < 8 and calls < MAX_CALLS:
    mem = jget('/api/memory')
    if mem.get('limit') is not None and mem['inter_agent_replies'] >= mem['limit']:
        P(f"budget exhausted: {mem['inter_agent_replies']}/{mem['limit']}")
        break
    active = [a for a in AGENTS if a not in settled]
    if not active:
        break
    guard += 1
    calls += len(active)
    P(f"== CROSS-TALK ROUND {guard} (active: {[names[a] for a in active]}, total calls={calls}) ==")
    r2 = parallel_call(active, history, 'cross-talk')
    any_reply = False
    for a in active:
        r = r2[a]
        if r['text'] and not r['silent']:
            history.append({'speaker': names[a], 'content': r['text']})
            any_reply = True
            tag = 'CONCLUDED' if r['concluded'] else ('TRUNCATED' if r['truncated'] else '')
            P(f"  {names[a]:9s} {r['dt']:5.1f}s think={r['think_len']:5d} {tag:9s} err={r['err']} :: {r['text'][:160]!r}")
            if r['truncated']:
                trunc_agents.append(names[a])
            if r['concluded']:
                lastConcluded = True
        else:
            settled.add(a)
            P(f"  {names[a]:9s} {r['dt']:5.1f}s think={r['think_len']:5d} SILENT      err={r['err']} meta={r['meta']}")
    if lastConcluded or not any_reply:
        break

memF = jget('/api/memory')
P(f"counter FINAL: {memF.get('inter_agent_replies')} (limit={memF.get('limit')}) last_reset_by={memF.get('last_reset_by')!r}")
P(f"rounds={guard} calls={calls} concluded={lastConcluded} settled={[names[a] for a in sorted(settled)]}")
json.dump({'prompt': PROMPT, 'history': history,
           'phase1': {a: r1[a] for a in AGENTS},
           'final_counter': memF, 'rounds': guard, 'calls': calls,
           'concluded': lastConcluded,
           'truncated_agents': sorted(set([names[a] for a in AGENTS if r1[a]['truncated']] + trunc_agents)),
           'has_truncation': bool([a for a in AGENTS if r1[a]['truncated']] or trunc_agents)},
          open('group_e2e_result_8agent.json', 'w'), indent=1)
P("saved group_e2e_result_8agent.json")
