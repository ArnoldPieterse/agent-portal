# Evidence: Auto-LLM Selector & Hotload Research (2026-11-17)
Task: Human-requested research + architecture proposal for auto LLM selector and hotload technology.
Artifact: memory/llm/hotload-selector.md (144 lines, 5-phase implementation plan)
Index update: memory/llm/INDEX.md new entry added

## What was done
1. Researched 5 relevant systems (SwapServeLLM, vLLM Semantic Router, LLMRouter paper, MS Foundry Model Router, ComfyUI video gen)
2. Analyzed current fleet state (dual residency, serialization bottleneck, backend-swap procedure)
3. Designed 4-layer architecture: Model Registry -> Router -> Hotload Engine -> Agent Activation Manager
4. Identified key risks: parallel_slots=1 serialization, VRAM math for concurrent models, non-LLM runtime adapters
5. Wrote implementation phases P1-P5 with effort estimates

## Sources
- SwapServeLLM (Oxford SC'25): github.com/rst0git/SwapServeLLM
- vLLM Semantic Router: vllm-sr.ai/docs/intro/
- LLMRouter paper: arxiv.org/abs/2608.06867
- Microsoft Model Router: learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-router-how-it-works
- Wan2.1 ComfyUI: github.com/lilinsong1/comfyui-wan-video-pipeline

## Next steps (for Builder/Orchestrator)
- P1: Create model_registry.json + llm_router.py scoring function
- P2: Automate hotload (replace manual schtask with API-driven loop)
- Requires human decision: which non-LLM models to target first (video? 3D?)
