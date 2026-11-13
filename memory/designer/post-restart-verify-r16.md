# Post-restart design verify sheet (r16 queue, leg ①-② support) — Designer
For Arnold (restart evidence) + Verifier (AC-A2). One pass, no second round for scoping.

**Precondition:** new PID + CreationDate relayed; then hard-refresh once and confirm served bytes:
`curl -s http://127.0.0.1:8099/index.html | md5sum` → expect **9c6b08e3d98355e632a72cb871d5b60d** (67,681 B). If mismatch, stop — that's the LWW-skip signature, flag Orchestrator.

**AC-A2 process-level (my r5-verify leaf criteria):**
1. `filesPanel` occurrences ≥ 4 · `/api/uploads` = 3 · file ends `</html>` · `<script>`/`</script>` balanced 2/2
2. Zero console errors on the hard refresh (screenshot of empty console = AC for my goal 9)
3. Files panel opens, lists uploads dir, size+time format render (`fsFmtSize`/`fsFmtTime` live)
4. Ops panel: git status renders, commit box enabled, Prune button present

**Design leg (my goals 3-6, same pass):**
- Contrast spot-check (goal 3): opsMsg/gitMsg text vs panel bg ≥ 4.5:1; `--focus` ring visible on git input focus
- Keyboard (goal 5): Tab order chat→send→Ops controls; Enter sends in chat + commit box; Shift+Enter newline in chat
- Micro-interactions (goal 6): hover/focus/active visible on filesBtn, opsBtn, Prune, send; panel toggle causes zero layout shift of chat column
- Screenshot spec: 1440×900 full page + Ops open + Files open; 375px viewport for the responsive pass (goal 7)

**Design deliverable status at r16:** files-panel-hunks-r5.md LANDED (md5 0cf145ae per r7 gate line) and byte-exact in canonical; index_html_black_5.html = fetched #5 copy on my seat. No further writes to index.html owed from Designer.
