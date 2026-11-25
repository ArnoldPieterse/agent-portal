import re, sys
sys.path.insert(0, "memory/archivist")
import mcode

tbl = mcode.load_table()
p = "MEMORY.md"
s = open(p, encoding="utf-8").read()
n = 0
for path in [
    "memory/ops/seat-matrix.json",
    "memory/mechanic/reboot-recovery.jsonl",
    "memory/ops/host-port-task-map-2026-11-15.md",
    "memory/designer/deep-sweep-2026-11-19.md",
    "memory/llm/instances.md",
    "memory/portal/architecture.md",
    "memory/portal/bugs/xtalk-completion-2026-11-15.md",
    "memory/ops/runbooks/windows-runbook.md",
    "memory/ops/probes.md",
]:
    out = mcode.code_for(path, tbl)
    c = out.split(" : ", 1)[1] if " : " in out else ""
    if re.match(r"^[A-Z][a-z]?\d+$", c) and path in s:
        s = s.replace(path, c)
        n += 1
open(p, "w", encoding="utf-8").write(s)
print("patched", n, "of 9")
