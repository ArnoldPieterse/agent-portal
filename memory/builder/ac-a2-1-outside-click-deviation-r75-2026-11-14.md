# AC-A2-1 outside-click clause: verified deviation, recommend RATIFY (option a)
Date: 2026-11-14 ~r75 (Builder seat, Black). Triggered by Verifier's AC-A2 sweep naming Builder/Designer.

## Finding (independently re-verified from this seat)
AC-A2-1 text says "outside click closes it". Shipped code does NOT close filesPanel on
document outside-click — it uses the app-standard button toggle:
  $("filesBtn").onclick=... $("filesPanel").classList.toggle("open") ...

## Evidence (Builder, raw file inspection)
1. Local base index.html = md5 8fc29f19ac6f1a79e00ace5087542600 (68,549 B) — same artifact
   lineage other seats pin (Researcher seat pin 8fc29f19). Contains the Files panel.
2. In that file, ALL THREE persistent panels (actPanel, fleetPanel, filesPanel) use
   classList.toggle("open") button-toggle close. NONE has a document outside-click handler.
3. The ONLY doc-outside-click handler in the app is for #attachWrap — a transient popover MENU:
   document.addEventListener("click", e=>{ if(!e.target.closest("#attachWrap")) amenu.hidden=true; });
4. apply_files_panel.py (the v2.2 build script) explicitly inserts the filesBtn toggle as
   "JS (after fleet toggle block)" — deliberate mirroring of the panel convention, not an oversight.

## Assessment
App has two consistent conventions: MENUS close on outside click; PANELS are button toggles.
The AC clause describes menu behavior applied to a panel = spec-wording gap, not functional defect
(panel closes via re-click, identical UX to act/fleet panels).

## Recommendation: option (a) — ratify as acceptable app-pattern deviation.
Reasons:
- Shipped pattern is intentional + internally consistent (3 panels identical).
- Option (b) now would change index.html md5/size → invalidates the f18b24c4 / 71,096 B pin that
  Designer confirmed (r71), Archivist's bundle-v2 stamp correction targets, and Researcher r75
  re-derived from raw bytes. Re-pinning at 3 seats immediately before Arnold's human pass =
  pure churn, zero functional gain.

## If option (b) is ever chosen later
Patch = ~3-line document listener mirroring the existing #attachWrap pattern:
  document.addEventListener("click", e=>{ const p=$("filesPanel"); if(p.classList.contains("open") && !e.target.closest("#filesPanel") && !e.target.closest("#filesBtn")) { $("filesBtn").click(); } });
Builder can produce v2.3 in minutes — but Designer/Archivist/Researcher re-pins become mandatory,
and bundle item-1 target changes again.

## Suggested bundle-v2 / TODO annotation (for Orchestrator → Arnold)
"AC-A2-1: PASS with ratified deviation — Files panel uses app-standard button-toggle close
(same as act/fleet panels); outside-click-close is reserved for menus (#attachWrap). See
memory/builder/ac-a2-1-outside-click-deviation-r75-2026-11-14.md."

Formal UI ratification: Designer (owns interface pattern). Builder position on record.
