Testing understanding modules + portal flow  
  
Date: 2026-11-18 (auto-loop pass, user request)  
  
"## Result: ALL PASS"  
  
10 test groups executed against memory/researcher/understanding.py + agent_portal.py integration:  
  
1. Module imports cleanly (no errors)  
2. Dictionary: 96 terms loaded (core=68, project=30), all with non-empty definitions  
3. key_terms extracts meaningful words from sample prompt  
4. synonyms() returns correct expansions (94 groups, 471 word forms)  
5. lookup() finds dictionary entries for prompt words  
6. understanding_block() produces formatted U-ref indexed output  
7. Synonym expansion in _mem_local_hits: 6 base words expanded to 22 (adds mirror-relevant terms like overwrite, reflection, pin)  
8. Portal integration: both call sites present and syntactically valid (py_compile passes)  
9. Never-raises contract verified on all public functions with None/empty/garbage input  
10. Flow confirmed: human msg - readmem path (understanding_block) + _mem_local_hits (synonyms) - lookup_ctx - to_openai_messages - LLM context  
  
"## Notes"  
- 10 words appear in multiple synonym groups (e.g. node, marker, procedure) - harmless but slightly redundant  
- Understanding block only fires when key_terms match dictionary entries; 'flows' and 'portal' had no dict hit in test prompt (expected for less common project terms)  
- Live HTTP verification pending server restart (module lazy-loads on first request, code path verified statically) 
