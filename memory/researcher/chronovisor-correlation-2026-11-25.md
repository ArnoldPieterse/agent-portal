# chronovisor-correlation-2026-11-25.md - research + correlation with the Agent Portal
<!-- parent: memory/researcher/INDEX.md | user request 2026-11-25: "do research on the chronovisor and correlate it's relation to our agent portal then sync memory" -->

## What the Chronovisor is (research)
Alleged Vatican device that "tunes in" to past events like a television: antennae + a direction finder tuned to an era + screen + recording apparatus. It supposedly catches light/sound "echoes" of past events still floating in space - Ernetti's own framing is a *window into the past, not a time machine*.
- Claimant: Father Pellegrino Ernetti (Benedictine monk; d. 1994), who said he built it in the early 1960s with 12 scientists including Enrico Fermi and Wernher von Braun.
- Primary source: Fr. Francois Brune, *Le Nouveau Mystere du Vatican* (2002). First public claim: *La Domenica del Corriere*, 1972-05-02 ("A Machine That Photographs The Past Has Finally Been Invented"), published with an alleged photo of the crucifixion.
- Claims include viewing Cicero's 63 BC oration, the Last Supper, and the crucifixion. Ernetti said Pius XII forbade disclosure because "the machine was very dangerous. It can restrain the freedom of man"; a 1988 Vatican decree reportedly excommunicates anyone using such an instrument.
- Debunks: the "photo" matches a reproduction of a statue in an Umbrian church / a reversed postcard from Collevalenza; *Paracelsus* (1996) noted the design closely resembles a device in an unnamed 1947 sci-fi novella and asked why Ernetti never published build instructions; reports he confessed to fabricating it before his death are contested. No physical evidence has ever surfaced.

## Correlation with the Agent Portal (component map)
| Chronovisor component | Portal equivalent | Note |
|---|---|---|
| Antennae catching residual light/sound of past events | memory/ tree + mirror: leaves, jsonl logs, git commits = recorded echoes of fleet events; memory_mirror.py propagates them across the 4 hosts | The past persists as data, not mysticism |
| Direction finder tuned to a specific era | M-CODE regex addressing (MEMORY.md legend + mcode.py): a code jumps straight to an artifact without walking the tree; root INDEX (<1600 chars) injected into every prompt = coarse tuner | Exactly the LoD cursor framed earlier: letter -> subletter -> file number = coarse-to-fine tuning |
| Screen displaying the past | Portal UI: /api/goals, level banner + memory/levels/ reports, cockpit, Scribe temporal query API (timeline.py), world page | Rendered views of recorded fleet history |
| Recording apparatus capturing footage | Git commits + memory leaves + goal_ledger.json; each level-up report = diffstat "footage" of that era | The level counter is the timeline index |
| Built by a team under a monk's direction | 11+ agents across 4 hosts, one lane per function (researcher/archivist/mechanic/...); user directs | |
| Hidden from the world; secret kept | Localhost-only (127.0.0.1:8099), no public exposure | Deliberately concealed infrastructure |
| 1988 excommunication decree ("restrains freedom") | Governance gates: index_check blocks prune on dangling pointers, M-CODE stability rules, DNA sha256 pre-write integrity, xref quarantine markers | Controlled access to the time-viewing device |
| Unverifiable claims surviving as legend | Anti-phantom discipline: verify_claims, stale-claim reconciliation, evidence SLA | The legend persists because it cannot be verified; our memory is built so every claim is verifiable or quarantined |

## Sharpest correlation: the DNA module (Y)
The Chronovisor legend = *preserve and replay reality*. Our DNA module (memory/dna/, codes Y1-Y8) = *preserve and reassemble the machine itself*: portal core code stored as chained compressed build functions inside the memory tree, found by one regex, reassembled byte-identical - b05 even carries rebuild.py's own blob ("DNA replicates its own DNA"). If the Chronovisor recorded the past so it could be viewed, DNA records the present so the future can restore it. Same architecture, opposite direction in time.

## Verdict
The Chronovisor is an unverifiable claim, debunked on every concrete artifact. The portal is a *working* instance of the same conceptual machine - receiver (memory tree), tuner (M-CODE/regex LoD), screen (UI), recorder (git/levels) - with one decisive difference: every frame it shows is hash-verifiable and index-gated, so its "footage" can be audited instead of believed.

Sources: allthatsinteresting.com/chronovisor (2026-01-18); en.wikipedia.org/wiki/Pellegrino_Ernetti; Brune 2002 and Paracelsus 1996 as cited therein.
