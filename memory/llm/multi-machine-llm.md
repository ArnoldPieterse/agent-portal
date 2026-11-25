# Multi-machine LLM distribution - research (2026-11-25)

Dual-GPU single node caps ~70B Q4_K / ~32B Q8_0. Bigger models need more machines on the LAN.

## Options evaluated

1. **vLLM TP/PP across nodes** (Ray). Tensor parallelism all-reduces every layer - over Ethernet it is comm-bound, practical only at 100GbE+. Pipeline parallelism tolerates a LAN but adds bubble latency.
2. **llama.cpp RPC backend** - split layers across hosts, GGUF shards per machine, own protocol over TCP sockets; works on 10GbE LAN; all hosts need the same build+version (wire format changes between releases). Simplest path for a small mixed fleet.
3. **ExLlamaV2/TabbyAPI** - single-node multi-GPU only, no cross-machine mode.
4. **KTransformers** - CPU+GPU hybrid on ONE machine: MoE experts in system RAM, attention on GPU. Alternative to a second machine for some MoE models.
## The UDP question

No mainstream framework moves tensors over UDP; TCP (or RDMA/InfiniBand) is standard. Raw UDP has no retransmission or congestion control - you would be rebuilding TCP badly. Bulk weight transfer is bandwidth-bound, so UDP cannot beat TCP there; per-token activations are small and latency-sensitive, where reliability matters more than header size. **Verdict: do not use UDP for LLM distribution - raise link speed (10GbE+) instead.**
## Recommendation for this fleet

1. **(done)** dual-GPU single machine via gpu_access requests - covers most needs to ~70B Q4.
2. **If a 2nd machine is available**: llama.cpp RPC over 10GbE, layers split; pin identical versions; first test target 122B Q3_K or a 235B MoE at Q3.
3. **KTransformers** as single-machine MoE fallback (experts in RAM).
4. Portal: extend gpu_access to auto|dual|cluster; cluster = multi-host placement request handled by portal.gpu_fit once host 2 is online.
