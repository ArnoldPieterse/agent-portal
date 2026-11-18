# Auto-generate post-mortem skeleton from template.
# Usage: python memory/mechanic/postmortem_gen.py --title <t> --impact <i>
import os, sys, json
from datetime import datetime, timezone

TEMPLATE = os.path.join(os.path.dirname(__file__), "postmortem_template.md")
OUT_DIR = os.path.join(os.path.dirname(__file__), "postmortems")

def generate(title="Untitled", impact="TBD"):
    ts = datetime.now(timezone.utc)
    iso = ts.isoformat()
    fname = f"{ts.strftime('%Y%m%d-%H%M%S')}_{title.lower().replace(' ','_')[:40]}.md"
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, fname)
    with open(TEMPLATE) as f:
        content = f.read()
    content = content.replace("{title}", title).replace("{iso8601}", iso)
    content = content.replace("(what was affected, how long, which hosts/agents)", impact)
    with open(path, "w") as f:
        f.write(content)
    print(f"Post-mortem skeleton created: {path}")
    return path

if __name__ == "__main__":
    title = "Untitled"
    impact = "TBD"
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--title" and i+1 < len(args): title = args[i+1]
        if a == "--impact" and i+1 < len(args): impact = args[i+1]
    generate(title, impact)