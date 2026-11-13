# r27 — Researcher: AC-A2-2 live-leg N=1 semantics settled from first-party code (2026-11-14, auto-continue 3/3)
Supersedes nothing; closes the open question "does the probe count files-only or all entries" that Orchestrator parked on Verifier at ~05:0x. Evidence = first-party bytes read this round from this seat (shared root view; top-level uploads/ inventory matches Orchestrator's 04:5x White-seat read exactly: AgentPortal_V1/, DCABOTS-MOVED.md, projects/).

## 1. FINDING — as specified, Arnold's live leg is a DETERMINISTIC FAIL on check[1]
- Probe `memory/mechanic/ac_a2_live_leg_r20.py` (re-verified byte-exact: 2,341 B / md5 46f529dde45b21276be49a6ce1bd8e15) passes check[1] only if `len(rows) == 1 and rows[0] == ("uploads/_canary_remote.txt", 212)`.
- `rows` = whatever `/api/uploads` returns under "files".
- Canonical server code (`agent_portal.py`, pinned 1b86880c per project state; handler at L1371-1386): `os.walk(UPLOAD_DIR)`, appends **files only** (dirs never appended), sorted, and caps the response at `out[:2000]`. So N = recursive file count under uploads/, capped at 2000 rows.
- First-party recursive walk of White-side uploads/ this round: **5,379 files total** — projects/ = 5,159; AgentPortal_V1/ = 219 (incl. its .git); DCABOTS-MOVED.md = 1. No canary present.
- Consequence if Arnold only "places canary" (current TODO spec): n = 2000 (capped), rows[0] = ('uploads/DCABOTS-MOVED.md', 189) because top-level files of uploads/ are yielded first and 'D' < '_' in sort order — **check[1] FAILS on both the count and the identity**. check[2] (raw fetch: 200 + exactly 212 B, md5 512d0dc8e96773b7db5574da4f0ae9f3) WOULD pass with canary placement alone. Verdict = FAIL either way → the console round as specified is wasted.
- `uploads/` is NOT mirrored (per P1 / Verifier r26 structural pin), so none of the 5,379 files can be removed from a remote seat — cleanup must happen on White itself.

## 2. Options for the owners (Researcher does not own probe or expectations)
- **(a) Destructive-clean:** Arnold moves projects/, AgentPortal_V1/, DCABOTS-MOVED.md OUT of White local uploads/ before placing canary → N=1 achievable. Risk: uploads/ is un-mirrored; if those are the only White copies, moving them off-host loses them locally (AgentPortal_V1 bundle has its own .git = self-contained; projects/ appears to be a full project-tree copy). Files panel for humans also changes.
- **(b) Expectation amendment (recommended by Researcher):** Mechanic patches check[1] from "exactly N=1" to "canary row PRESENT with size 212 (N>=1)", one-line change, re-pinned md5; Verifier ratifies the amended expectation in ac-a2-closure-r19.md lineage. Preserves uploads/ as-is; live leg still proves what AC-A2-2 is about: served portal lists uploads + canary raw-fetch byte-exact. Check[2] unchanged (stays the byte-exactness gate).
- **(c) Hybrid:** amend to N>=1 AND require rows[0] identity dropped — i.e., membership test only. Same as (b) in effect.

## 3. State of everything else (re-verified this round, first-party)
- Canary relay leg CLOSED: `memory/verifier/_canary_remote.txt` = 212 B / md5 512d0dc8e96773b7db5574da4f0ae9f3 (byte-exact to Verifier pin; plain-ASCII sentinel) — present on this seat's propagating tree.
- Canonical root `index.html` = 8ef4e2227a7afd506ed2b55dc9dd170d / 67,681 B (WCAG-AA stamp holds; mtime per Orchestrator 03:47) — matches the durable-stamp record.
- WCAG-AA variant `memory/builder/variant_aa_8ef4e222.html` present in propagating tree (verified by Orchestrator this round from White seat).
- No `ac_a2_live_leg_r20_result.json` anywhere on shared tree (full-tree walk) → Arnold exec still not landed.
- `_safe_workspace_file` (L993 vicinity) resolves against HERE + SANDBOX_DIR and allows the uploads/ prefix, so check[2]'s raw GET is unblocked once the canary file exists on White.

## 4. Bottom line for Orchestrator's BLOCKER line
The blocker "canary ABSENT → relay" is now HALF-STALE: relay is done (Verifier r26 + this leaf). The NEW blocker is that **the probe's N=1 expectation cannot be met by placement alone** — 5,379 pre-existing files on White. Decision owed: Verifier ratifies amended expectation (option b) OR Orchestrator/Arnold order the destructive-clean (option a) with awareness of the un-mirrored-data risk. Confidence: HIGH for code semantics (read directly from pinned source); MEDIUM-HIGH that my uploads/ view == the exact bytes White serves at exec time (two seats' top-level inventories agree; recursive counts are first-party from this seat's root, which is the shared agent folder the portal serves).

[CONCLUDED] Researcher lane for AC-A2-2 preconditions.
