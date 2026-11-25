# dna-spec.md - the self-rebuild contract (2026-11-25)
<!-- parent: memory/dna/INDEX.md | entry point: memory/dna/rebuild.py (Y2) -->

## What DNA is
The portal's core code, reassemblable from this memory tree. Each artifact is stored as a
**build function**: a small .py file holding a compressed blob (gzip+base64) of the target
file, its sha256, and a metadata header. A single regex finds every build function; executing
them in chain order rewrites the core byte-identical. Add a new artifact = add one build file -
the next rebuild picks it up automatically (the system evolves by appending).

## The scan regex (single source of truth)
    ^# DNA-BUILD id=(\d+) name=(\S+) target=(\S+) date=(\d{4}-\d{2}-\d{2}) deps=([\w,\-]*)$
One header line per build file, first non-blank comment. Fields:
- id:     2-digit chain position (assembly order; deps may reorder within it)
- name:   short slug
- target: repo-relative path the blob rewrites (e.g. agent_portal.py)
- date:   last build date of THIS blob (stamped when the blob was minted/refreshed)
- deps:   comma list of ids that must be written first, or "-" for none

## Build file shape (memory/dna/builds/bNN-<name>.py)
    # DNA-BUILD id=NN name=<slug> target=<path> date=YYYY-MM-DD deps=-
    # one-line note on what this rebuilds
    BLOB = "<base64(gzip(original bytes))>"
    SHA256 = "<sha256 hex of original bytes>"

## Chain semantics
rebuild.py scans builds/*.py, parses headers with the regex above, topologically sorts by deps
(falling back to id order), then per build: decompress -> sha256(blob) must equal SHA256
(integrity) -> write target -> sha256(target on disk) must equal SHA256 (verification).
The manifest memory/dna/manifest.json records every run. Self-reference: b05 carries rebuild.py's
own blob, so a full --apply reassembles the rebuilder too (DNA replicates its own DNA).

## Operations
    python memory/dna/rebuild.py             # DRY-RUN: verify blobs + report drift vs live files
    python memory/dna/rebuild.py --out DIR   # pure reassembly into DIR (no live writes) - the proof
    python memory/dna/rebuild.py --apply     # back up current targets, then rewrite them
Refresh a stale build (artifact changed on disk):  python memory/dna/rebuild.py --mint bNN
(mint recomputes BLOB/SHA256/date for that build from the live file - keeps DNA in sync.)

## v1 chain (5 builds)
b01 portal-core -> agent_portal.py | b02 api-extras -> portal/api_extras.py |
b03 gpu-fit -> portal/gpu_fit.py | b04 evolve-template -> ui/pages/evolve.html |
b05 dna-rebuild -> memory/dna/rebuild.py (self)
Growth rule: append b06+ for new core artifacts (ui/core.js, agents.json schema, ...); never
rewrite an existing build's id - ids are the stable chain address.
