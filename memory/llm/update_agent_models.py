"""update_agent_models.py (2026-11-25) - one-shot: add recommended_models + gpu_access
to every agent in agents.json, based on live /v1/models probes + hosts.md residency.
Run: python memory/llm/update_agent_models.py
"""
import json

W = [("atlas-q8", "Q8_0 main seat (32k ctx)"),
     ("Qwen3.8-27B-Q4_K_S", "131k ctx for long context"),
     ("unsloth/Qwen3.5-4B-MTP-GGUF", "fast triage / cheap calls")]
R = [("quinn-q4", "Q4 131k ctx - deep research needs big windows"),
     ("Qwen3.8-27B-Q8_0", "highest accuracy for synthesis"),
     ("qwen3-asr-1.7b", "transcribe voice-note inputs")]
B = [("Qwen3.8-27B-Q8_0", "code accuracy - primary build seat"),
     ("Qwen3.8-27B-Q4_K_S", "fast iteration / bulk edits")]
P = [("designer-q4", "Q4 65k - visual direction + long briefs"),
     ("archivist-q8", "Q8 seat when free - precision specs")]
A = [("archivist-q8", "Q8 32k - catalog/summarise accuracy"),
     ("designer-q4", "fallback seat on same host")]
S = [("scribe-q8", "Q8 16k - prose quality primary"),
     ("mechanic-q4", "UD-Q4_K_XL 65k fallback, longer docs")]
M = [("mechanic-q4", "UD-Q4_K_XL 65k - systems work"),
     ("scribe-q8", "heavy reasoning seat when free")]
O = [("quinn-q4", "personality + 131k ctx for long threads"),
     ("Qwen3.8-27B-Q8_0", "careful public replies on Q8")]
VGEN = [("designer-q4", "storyboard / prompt pipelines"),
        ("unsloth/LTX-2.5-GGUF", "(on white) video model - cross-host request")]

REC = {"orchestrator": W, "researcher": R, "builder": B, "verifier": list(B),
       "designer": P, "archivist": A, "scribe": S, "mechanic": M, "outlet": O,
       "pixel": list(B), "forge": list(B),
       "lumen": [("designer-q4", "prompt drafting for image gen")] + [VGEN[1]],
       "reel": VGEN, "splice": VGEN}

path = "agents.json"
d = json.load(open(path, encoding="utf-8"))
n = 0
for ag in d["agents"]:
    ag["recommended_models"] = [{"id": i, "why": w} for i, w in REC.get(ag["id"], B)]
    ag.setdefault("gpu_access", "auto")
    n += 1
json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(n, "agents updated")
