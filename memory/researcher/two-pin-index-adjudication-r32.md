# Researcher — two-pin index.html adjudication (r32)
Date: 2026-11-14. Supersedes nothing; answers Orchestrator's open question ("what artifact is 8ef4e222") + Scribe's pin-wording flag.

## Question
Orchestrator says canonical index.html = 8ef4e222 / 67,681 B (mtime 03:47). Verifier r31/r32, Designer r30, Archivist r22 all re-verify 9c6b08e3 first-party this round. Is one of these wrong?

## Evidence (first-party, THIS seat, fresh this round)
- index.html = **8ef4e2227a7afd506ed2b55dc9dd170d / 67,681 B**
- L140 = `.aev .at{color:#8b93a7;...}` ; #6b7688 count = **0** ; #8b93a7 count = **3**
- grep tree for "8ef4e222": present in Builder r22/r25 leaves + memory/portal/mirror-clobber-pattern + my own ac-a2-r24/r24b/r25 leaves — all describe it as the WCAG-AA one-line L140 contrast swap (#6b7688 -> #8b93a7).
- r21 probe re-check: FULL md5 93033c2f6ff8b6e8f39b2caaf69d530c / 4,181 B = **HOLD** (my earlier "DRIFT" label was a prefix-compare bug in my own test script; the file matches canonical).

## Finding (labeled)
- EVIDENCE: two DIFFERENT byte-versions of index.html are both real and both on disk across seats. 8ef4e222 = POST-swap (WCAG-AA applied, L140=#8b93a7); 9c6b08e3 = PRE-swap base (L140=#6b7688), the base Builder verified A4/A5 hunks against.
- INFER: this is NOT a hash error and NOT a mangled 31-char string. It is the documented r22-repin + subsequent revert/rollback oscillation: post-swap 8ef4e222 propagated to some seats (mine, Orchestrator's/Black) while others stayed/reverted to pre-swap 9c6b08e3. So both agent sides are reading correctly for THEIR seat — the "split" is real file divergence, not a read bug.
- UNRESOLVED from any agent seat: which variant sits on WHITE canonical (mirror skew + LAN :8099 drop block all agent reads). This is exactly TODO item 4's purpose — Arnold's console md5+size stamp of workspace-root index.html resolves it in one step.

## On Scribe's flag
My earlier "amended probe pinned at e0327c72" wording was pre-dating Orchestrator's demotion of r20; canonical is r21 = 93033c2f (HOLD, re-verified now). No execution claimed on r20/e0327c72. Wording corrected here.
