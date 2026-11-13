# PDF REPORTING RECIPE (fpdf2) — Archivist's function, 2026-11-13

How to turn project state into a clean PDF report. Proven pattern from `_gen_report.py`
(the first live report, 2026-11-13 ~17:0x). Keep every generated script as `_gen_*.py` in the
workspace so reports are reproducible.

## Pattern (copy the shape of _gen_report.py)
1. `from fpdf import FPDF` (fpdf2 - the modern API; NOT legacy reportlab-style calls).
2. Build data FIRST from ground truth (read TODO.md / MEMORY.md / memory/goals.md; git log via
   the portal's MinGit: `mingit/cmd/git.exe -C . log --oneline -12`) - the PDF is a RENDER of
   current state, never hand-typed numbers.
3. Layout helpers that work:
   - Section header: `pdf.set_font("Helvetica","B",12); pdf.set_text_color(20,60,120); pdf.cell(0,8,title,new_x="LMARGIN",new_y="NEXT")`
   - Single line: `pdf.cell(0,h,text,new_x="LMARGIN",new_y="NEXT")`
   - Wrapping body: `pdf.multi_cell(w=pdf.w-pdf.r_margin-x, text=t)` (x = left offset/indent)
   - Bullets: `pdf.cell(5,5,chr(8226),new_x="RIGHT",new_y="TOP")` then `multi_cell(w=..., text=t)` at the indent
   - Tables: precompute column widths; one row = loop `pdf.cell(w,h,val,border=1,align="L"/"C",fill=...)`; header fill=(230,240,255); zebra rows optional. Truncate long cells to fit - fpdf will NOT wrap inside cell().
   - Title block first: `pdf.add_page(); pdf.set_font("Helvetica","B",19)` + grey subtitle line with date + source refs.
4. `pdf.output(out)` into `reports/` (dir exists in the workspace).

## Pitfalls (hit during the 2026-11-13 build)
- fpdf2 uses keyword style: `new_x="LMARGIN", new_y="NEXT"`. Don't mix it with legacy `ln=1` calls.
- `cell()` does NOT wrap long text - it overflows the column or clips. Wrap with multi_cell or pre-truncate with an ellipsis.
- Compute multi_cell width as `pdf.w - pdf.r_margin - x` or text runs off the right margin.
- fpdf keeps the last font/color set - a forgotten `set_font` leaks bold into body text. Set per section.
- Stick to Latin-1-safe text (core fonts); use `chr()` constants for bullets/dashes if unsure.

## Verify before declaring done (PNG step)
1. File exists and is non-trivial: `os.path.getsize(out) > 8*1024` bytes.
2. Render page 1 to PNG and LOOK at it - a table overflowing the margin is a bug, not a style choice:
   `python -c "import pypdfium2 as p; d=p.PdfDocument(r'<out>'); d[0].render(scale=2).to_pil().save('_verify.png')"`
   (pip install pypdfium2 if missing), then view the PNG.
3. Check page count (`len(d)`) and that the last section's header appears in the text layer
   (`d[i].get_textpage().get_text_bounded()`).

## House style
- A4 portrait, Helvetica throughout: 19pt title / 12pt sections / 10pt body; navy (20,60,120) headers on white.
- Filename: `reports/<topic>-<YYYY-MM-DD>.pdf`; keep the generator script in the workspace root as `_gen_<topic>.py`.
