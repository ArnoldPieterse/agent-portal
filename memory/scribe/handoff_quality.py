#!/usr/bin/env python3
"""Handoff Quality Scoring (Scribe goal #4).

Scores every entry in memory/scribe/handoffs.jsonl on three axes:
  - completeness : are all expected fields present and non-empty?   (0-30)
  - specificity  : does the summary carry concrete detail vs vague filler? (0-40)
  - actionability: is next_step executable without clarification?    (0-30)

Output (stdout, JSON list): [{id, from_agent, to_agent, score, sub_scores, weak_fields[]}]
Also writes the same array to memory/scribe/handoff_quality.json.

Usage:
  python memory/scribe/handoff_quality.py            # score real handoffs
  python memory/scribe/handoff_quality.py --selftest # run acceptance self-test
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HANDOFFS = HERE / "handoffs.jsonl"
OUT_JSON = HERE / "handoff_quality.json"

# Fields a well-formed handoff should carry.
EXPECTED_FIELDS = ["from_agent", "to_agent", "artifact_path", "summary", "assumptions", "next_step"]

# Vague filler that signals low specificity (lowercased substring match).
VAGUE_TERMS = [
    "some ", "something", "stuff", "things", "etc", "various",
    "maybe", "probably", "roughly", "approximately", "a few",
    "as needed", "if possible", "tbd", "todo", "will figure out",
]

# Concrete-detail signals in a summary.
PATH_RE = re.compile(r"[A-Za-z0-9_./-]+\.(md|py|jsonl?|js|css|html|json)")
NUM_RE = re.compile(r"\b\d+(?:\.\d+)?%?\b")
CODE_RE = re.compile(r"`[^`]+`")
AGENT_NAMES = {"orchestrator", "researcher", "builder", "verifier",
               "designer", "archivist", "scribe", "mechanic"}

# Ambiguity markers that make a next_step non-actionable.
AMBIGUOUS_RE = re.compile(
    r"\b(maybe|perhaps|possibly|might|should (?:we|probably)|figure out|" +
    r"tbd|todo|as appropriate|if needed|later|soon)\b", re.IGNORECASE)
VERB_START_RE = re.compile(
    r"^\s*(add|run|write|create|update|fix|check|verify|test|build|extend|" +
    r"grep|diff|log|re-?run|author|collect|ingest|score|flag|append|remove|" +
    r"reproduce|instrument|compare|generate|submit|re-rank|open|close)\b", re.IGNORECASE)


def _nonempty(v):
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return True


def score_completeness(entry):
    """0-30: fraction of expected fields present and non-empty."""
    filled = sum(1 for f in EXPECTED_FIELDS if _nonempty(entry.get(f)))
    ratio = filled / len(EXPECTED_FIELDS)
    return round(ratio * 30, 1), [f for f in EXPECTED_FIELDS if not _nonempty(entry.get(f))]


def score_specificity(summary):
    """0-40: concrete detail density vs vague filler."""
    if not summary or not summary.strip():
        return 0.0, []
    s = summary.lower()
    concrete = 0
    concrete += len(PATH_RE.findall(summary))          # file paths
    concrete += len(NUM_RE.findall(summary))            # numbers/percentages
    concrete += len(CODE_RE.findall(summary))           # inline code refs
    concrete += sum(1 for w in AGENT_NAMES if w in s)   # named agents
    vague = sum(1 for t in VAGUE_TERMS if t in s)
    # Each of the first 5 concrete signals earns 8 pts (saturates at 40);
    # each vague filler term costs 8.
    raw = min(concrete, 5) * 8 - vague * 8
    return max(0.0, min(40.0, float(raw))), (["summary_vague"] if vague > concrete else [])


def score_actionability(next_step):
    """0-30: is the next step executable without clarification?"""
    if not next_step or not next_step.strip():
        return 0.0, ["next_step_missing"]
    s = next_step.strip()
    score = 0.0
    weak = []
    if VERB_START_RE.match(s):
        score += 12          # starts with an imperative verb
    else:
        weak.append("next_step_no_verb")
    if AMBIGUOUS_RE.search(s):
        score -= 10
        weak.append("next_step_ambiguous")
    if PATH_RE.search(s) or NUM_RE.search(s) or CODE_RE.search(s):
        score += 8           # references a concrete target
    else:
        weak.append("next_step_no_target")
    if len(s) >= 20:
        score += 10          # enough detail to act on
    else:
        weak.append("next_step_thin")
    return max(0.0, min(30.0, float(score))), weak


def score_entry(entry, idx):
    comp, comp_weak = score_completeness(entry)
    spec, spec_weak = score_specificity(entry.get("summary"))
    act, act_weak = score_actionability(entry.get("next_step"))
    total = round(comp + spec + act, 1)
    weak_fields = comp_weak + spec_weak + act_weak
    return {
        "id": entry.get("id", f"handoff-{idx}"),
        "from_agent": entry.get("from_agent", "?"),
        "to_agent": entry.get("to_agent", "?"),
        "score": total,
        "sub_scores": {"completeness": comp, "specificity": spec, "actionability": act},
        "weak_fields": weak_fields,
    }


def load_handoffs(path=HANDOFFS):
    if not path.exists():
        return []
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def main():
    entries = load_handoffs()
    results = [score_entry(e, i) for i, e in enumerate(entries)]
    print(json.dumps(results, indent=2))
    OUT_JSON.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def selftest():
    """Acceptance self-test: >=5 scored, vague<50, specific>80, valid JSON."""
    real = main()
    assert len(real) >= 5, f"expected >=5 handoffs scored, got {len(real)}"

    vague = {
        "id": "test-vague", "from_agent": "A", "to_agent": "B",
        "summary": "some stuff about things, maybe various as needed",
        "next_step": "figure out later if possible",
    }
    specific = {
        "id": "test-specific", "from_agent": "Orchestrator", "to_agent": "Builder",
        "artifact_path": "memory/mirror/memory_mirror.py",
        "summary": ("Mirror-sync pin-file clobber loop in memory_mirror.py reverts index.html "
                    "edits on the next mirror cycle due to a `sha12` mismatch between the canonical "
                    "backup and live file; reproduced on 3 of 4 hosts (White, Blue, Green, Red)."),
        "assumptions": ["PIN_FILES is the sole revert mechanism"],
        "next_step": "Add before/after hash log to mirror write path, re-run one cycle, diff log against actual file changes",
    }
    vs = score_entry(vague, 90)["score"]
    ss = score_entry(specific, 91)["score"]
    print(f"\nSELFTEST: real={len(real)} vague={vs} specific={ss}")
    assert vs < 50, f"vague handoff should score <50, got {vs}"
    assert ss > 80, f"specific handoff should score >80, got {ss}"
    # valid JSON round-trip
    json.dumps([score_entry(e, i) for i, e in enumerate(load_handoffs())])
    print("SELFTEST PASS")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        main()