# Memory Hygiene Report — 2026-11-18

## Metrics
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total files | 6103 | - | - |
| Total size | 151026.8 KB | - | - |
| Files >5KB | 1943 | 0 | FAIL |
| Orphaned files | 5547 | 0 | FAIL |
| Stale files (>30d) | 0 | 0 | PASS |

## Files >5KB (top 10)

- `memory\archivist\kg_state.json` — 928.8 KB
- `memory\archivist\knowledge_graph_delta.jsonl` — 682.7 KB
- `memory\designer\_ud768\Default\Cache\Cache_Data\index` — 512.4 KB
- `memory\archivist\decay-report.md` — 500.3 KB
- `memory\archivist\manifest-20261118.json` — 495.5 KB
- `memory\designer\_ud768\Default\Service Worker\ScriptCache\013888a1cda32b90_0` — 365.7 KB
- `memory\builder\canary\black\__pycache__\agent_portal.cpython-313.pyc` — 269.1 KB
- `memory\builder\canary\pale\__pycache__\agent_portal.cpython-313.pyc` — 269.1 KB
- `memory\builder\canary\red\__pycache__\agent_portal.cpython-313.pyc` — 269.1 KB
- `memory\designer\_ud_768_1\ShaderCache\data_1` — 264.0 KB

## Orphaned files (top 10)

- `memory/archivist/kg_state.json` — 928.8 KB
- `memory/archivist/knowledge_graph_delta.jsonl` — 682.7 KB
- `memory/archivist/decay-report.md` — 500.3 KB
- `memory/archivist/manifest-20261118.json` — 495.5 KB
- `memory/designer/_ud768/Default/Service Worker/ScriptCache/013888a1cda32b90_0` — 365.7 KB
- `memory/builder/canary/black/__pycache__/agent_portal.cpython-313.pyc` — 269.1 KB
- `memory/builder/canary/pale/__pycache__/agent_portal.cpython-313.pyc` — 269.1 KB
- `memory/builder/canary/red/__pycache__/agent_portal.cpython-313.pyc` — 269.1 KB
- `memory/designer/_ud_768_1/ShaderCache/data_1` — 264.0 KB
- `memory/designer/_ud_768_1/Default/DawnGraphiteCache/data_1` — 264.0 KB

## Stale files >30d (top 10)


## Remediation List

- [ ] SPLIT: memory\archivist\kg_state.json (928.8KB > 5KB limit)
- [ ] SPLIT: memory\archivist\knowledge_graph_delta.jsonl (682.7KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud768\Default\Cache\Cache_Data\index (512.4KB > 5KB limit)
- [ ] SPLIT: memory\archivist\decay-report.md (500.3KB > 5KB limit)
- [ ] SPLIT: memory\archivist\manifest-20261118.json (495.5KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud768\Default\Service Worker\ScriptCache\013888a1cda32b90_0 (365.7KB > 5KB limit)
- [ ] SPLIT: memory\builder\canary\black\__pycache__\agent_portal.cpython-313.pyc (269.1KB > 5KB limit)
- [ ] SPLIT: memory\builder\canary\pale\__pycache__\agent_portal.cpython-313.pyc (269.1KB > 5KB limit)
- [ ] SPLIT: memory\builder\canary\red\__pycache__\agent_portal.cpython-313.pyc (269.1KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_768_1\ShaderCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_768_1\Default\DawnGraphiteCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_768_1\Default\DawnWebGPUCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_768_1\Default\GPUCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_768_1\Default\Storage\ext\ihmafllikibpmigkcoadcmckbfhibefp\def\DawnGraphiteCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_768_1\Default\Storage\ext\ihmafllikibpmigkcoadcmckbfhibefp\def\DawnWebGPUCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_768_1\Default\Storage\ext\ihmafllikibpmigkcoadcmckbfhibefp\def\GPUCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_1920_6\ShaderCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_1920_6\Default\DawnGraphiteCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_1920_6\Default\DawnWebGPUCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_1920_6\Default\GPUCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_1920_6\Default\Storage\ext\ihmafllikibpmigkcoadcmckbfhibefp\def\DawnGraphiteCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_1920_6\Default\Storage\ext\ihmafllikibpmigkcoadcmckbfhibefp\def\DawnWebGPUCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_1920_6\Default\Storage\ext\ihmafllikibpmigkcoadcmckbfhibefp\def\GPUCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_1920_5\ShaderCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_1920_5\Default\DawnGraphiteCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_1920_5\Default\DawnWebGPUCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_1920_5\Default\GPUCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_1920_5\Default\Storage\ext\ihmafllikibpmigkcoadcmckbfhibefp\def\DawnGraphiteCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_1920_5\Default\Storage\ext\ihmafllikibpmigkcoadcmckbfhibefp\def\DawnWebGPUCache\data_1 (264.0KB > 5KB limit)
- [ ] SPLIT: memory\designer\_ud_1920_5\Default\Storage\ext\ihmafllikibpmigkcoadcmckbfhibefp\def\GPUCache\data_1 (264.0KB > 5KB limit)
- ... and 7460 more (see JSON)