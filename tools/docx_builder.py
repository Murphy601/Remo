"""Build a visually dense, internal-engineering Word document from a JSON spec."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn, nsmap
from docx.shared import Cm, Inches, Pt, RGBColor, Emu, Twips
from docx.table import Table
from docx.text.paragraph import Paragraph


NAVY = RGBColor(0x1B, 0x36, 0x5D)
STEEL = RGBColor(0x2F, 0x4A, 0x6E)
BODY = RGBColor(0x22, 0x22, 0x22)
MUTED = RGBColor(0x55, 0x55, 0x55)
RULE = RGBColor(0xC5, 0xCD, 0xD6)
ROW_ALT = "EEF2F6"
HEADER_BG = "1B365D"
CALLOUT_BG = "F4F1E8"
CODE_BG = "F3F4F6"
DECISION_BG = "E7EEF5"
WARN_BG = "F8EDE8"

BODY_FONT = "Liberation Serif"
SANS = "Liberation Sans"
MONO = "Liberation Mono"


def _set_run_font(run, name, size_pt=None, bold=None, italic=None, color=None):
    run.font.name = name
    r = run._element
    rPr = r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), name)
    rFonts.set(qn("w:hAnsi"), name)
    rFonts.set(qn("w:eastAsia"), name)
    rFonts.set(qn("w:cs"), name)
    if size_pt is not None:
        run.font.size = Pt(size_pt)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color is not None:
        run.font.color.rgb = color


def _shade_cell(cell, hex_color: str):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = tcPr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tcPr.append(shd)
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"), "clear")


def _set_cell_borders(cell, color="C5CDD6", sz="4"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.find(qn("w:tcBorders"))
    if tcBorders is None:
        tcBorders = OxmlElement("w:tcBorders")
        tcPr.append(tcBorders)
    for edge in ("top", "left", "bottom", "right"):
        el = tcBorders.find(qn(f"w:{edge}"))
        if el is None:
            el = OxmlElement(f"w:{edge}")
            tcBorders.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), sz)
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)


def _set_cell_margins(cell, top=40, bottom=40, left=80, right=80):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = tcPr.find(qn("w:tcMar"))
    if tcMar is None:
        tcMar = OxmlElement("w:tcMar")
        tcPr.append(tcMar)
    for name, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        node = tcMar.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            tcMar.append(node)
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")


def _clear_table_borders(table: Table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = tblPr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tblPr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = borders.find(qn(f"w:{edge}"))
        if el is None:
            el = OxmlElement(f"w:{edge}")
            borders.append(el)
        el.set(qn("w:val"), "nil")
        el.set(qn("w:sz"), "0")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "auto")


def _keep_with_next(paragraph: Paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    kwn = pPr.find(qn("w:keepNext"))
    if kwn is None:
        kwn = OxmlElement("w:keepNext")
        pPr.append(kwn)


def _spacing(paragraph: Paragraph, before=0, after=8, line=240, rule="auto"):
    pf = paragraph.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pPr = paragraph._p.get_or_add_pPr()
    sp = pPr.find(qn("w:spacing"))
    if sp is None:
        sp = OxmlElement("w:spacing")
        pPr.append(sp)
    sp.set(qn("w:line"), str(line))
    sp.set(qn("w:lineRule"), rule)
    sp.set(qn("w:before"), str(int(before * 20)))
    sp.set(qn("w:after"), str(int(after * 20)))


def _add_page_number(paragraph: Paragraph):
    """Insert PAGE of NUMPAGES fields."""
    def _fld(begin_text=None, instr=None, separate=False, end=False):
        run = paragraph.add_run()
        r = run._r
        fld = OxmlElement("w:fldChar")
        if begin_text is not None:
            fld.set(qn("w:fldCharType"), "begin")
            r.append(fld)
            if instr:
                ir = paragraph.add_run()
                it = OxmlElement("w:instrText")
                it.set(qn("xml:space"), "preserve")
                it.text = instr
                ir._r.append(it)
        elif separate:
            fld.set(qn("w:fldCharType"), "separate")
            r.append(fld)
        elif end:
            fld.set(qn("w:fldCharType"), "end")
            r.append(fld)
        return run

    run = paragraph.add_run()
    r = run._r
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    r.append(fld1)
    ir = paragraph.add_run()
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = " PAGE "
    ir._r.append(it)
    sep = paragraph.add_run()
    f2 = OxmlElement("w:fldChar")
    f2.set(qn("w:fldCharType"), "end")
    sep._r.append(f2)


def _add_numpages(paragraph: Paragraph):
    run = paragraph.add_run()
    r = run._r
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    r.append(fld1)
    ir = paragraph.add_run()
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = " NUMPAGES "
    ir._r.append(it)
    sep = paragraph.add_run()
    f2 = OxmlElement("w:fldChar")
    f2.set(qn("w:fldCharType"), "end")
    sep._r.append(f2)


def _horizontal_line(paragraph: Paragraph, color="1B365D", sz="12"):
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), sz)
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    pPr.append(pBdr)


def _set_narrow_cell_width(cell, dxa):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcW = tcPr.find(qn("w:tcW"))
    if tcW is None:
        tcW = OxmlElement("w:tcW")
        tcPr.append(tcW)
    tcW.set(qn("w:w"), str(dxa))
    tcW.set(qn("w:type"), "dxa")


def _paragraph_text(cell, text, font=SANS, size=9, bold=False, color=BODY, align=None):
    cell.text = ""
    p = cell.paragraphs[0]
    if align:
        p.alignment = align
    _spacing(p, before=0, after=0, line=230)
    run = p.add_run(text)
    _set_run_font(run, font, size, bold=bold, color=color)
    return p


def build_document(spec: dict, out_path: Path) -> Path:
    doc = Document()

    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.left_margin = Inches(1.15)
    section.right_margin = Inches(1.15)
    section.top_margin = Inches(1.2)
    section.bottom_margin = Inches(1.05)
    section.header_distance = Inches(0.4)
    section.footer_distance = Inches(0.4)

    # Default style
    normal = doc.styles["Normal"]
    normal.font.name = BODY_FONT
    normal.font.size = Pt(12)
    normal.font.color.rgb = BODY
    rPr = normal.element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    rFonts.set(qn("w:ascii"), BODY_FONT)
    rFonts.set(qn("w:hAnsi"), BODY_FONT)

    pf = normal.paragraph_format
    pf.space_after = Pt(12)
    pf.space_before = Pt(0)
    pf.line_spacing = 1.78

    for i in range(1, 4):
        hs = doc.styles[f"Heading {i}"]
        hs.font.color.rgb = NAVY
        hs.font.name = SANS
        hs.font.bold = True
        hrPr = hs.element.get_or_add_rPr()
        rFonts = hrPr.find(qn("w:rFonts"))
        if rFonts is None:
            rFonts = OxmlElement("w:rFonts")
            hrPr.append(rFonts)
        rFonts.set(qn("w:ascii"), SANS)
        rFonts.set(qn("w:hAnsi"), SANS)
        if i == 1:
            hs.font.size = Pt(16)
            hs.paragraph_format.space_before = Pt(22)
            hs.paragraph_format.space_after = Pt(12)
        elif i == 2:
            hs.font.size = Pt(13)
            hs.paragraph_format.space_before = Pt(16)
            hs.paragraph_format.space_after = Pt(8)
        else:
            hs.font.size = Pt(12)
            hs.paragraph_format.space_before = Pt(12)
            hs.paragraph_format.space_after = Pt(6)

    _build_header(section, spec)
    _build_footer(section, spec)
    _build_title_block(doc, spec)

    for block in spec.get("blocks", []):
        _render_block(doc, block)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out_path))
    return out_path


def _build_header(section, spec):
    header = section.header
    header.is_linked_to_previous = False
    # wipe default empty para content by using it
    p = header.paragraphs[0]
    p.clear()
    _spacing(p, before=0, after=2, line=200)
    _horizontal_line(p, color="1B365D", sz="18")

    run = p.add_run(spec.get("org", "Northstar Engineering"))
    _set_run_font(run, SANS, 9, bold=True, color=NAVY)

    run = p.add_run("   |   ")
    _set_run_font(run, SANS, 9, color=MUTED)

    run = p.add_run(spec.get("doc_type", "Internal Document"))
    _set_run_font(run, SANS, 9, color=STEEL)

    run = p.add_run(" " * 8)
    run = p.add_run(spec.get("classification", "INTERNAL"))
    _set_run_font(run, SANS, 8, bold=True, color=NAVY)

    p2 = header.add_paragraph()
    _spacing(p2, before=0, after=0, line=200)
    run = p2.add_run(spec.get("title", ""))
    _set_run_font(run, SANS, 8, italic=True, color=MUTED)


def _build_footer(section, spec):
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0]
    p.clear()
    _spacing(p, before=4, after=0, line=200)
    _horizontal_line(p, color="1B365D", sz="12")

    run = p.add_run(spec.get("doc_id", "DOC-000"))
    _set_run_font(run, SANS, 8, color=MUTED)
    run = p.add_run("  ·  v" + str(spec.get("version", "1.0")))
    _set_run_font(run, SANS, 8, color=MUTED)
    run = p.add_run("  ·  " + spec.get("date", ""))
    _set_run_font(run, SANS, 8, color=MUTED)
    run = p.add_run("  ·  Page ")
    _set_run_font(run, SANS, 8, color=MUTED)
    _add_page_number(p)
    for run in p.runs:
        if run.font.size is None:
            _set_run_font(run, SANS, 8, color=MUTED)
    run = p.add_run(" of ")
    _set_run_font(run, SANS, 8, color=MUTED)
    _add_numpages(p)
    run = p.add_run("  ·  " + spec.get("classification", "INTERNAL"))
    _set_run_font(run, SANS, 8, color=MUTED)


def _build_title_block(doc: Document, spec: dict):
    kicker = doc.add_paragraph()
    _spacing(kicker, before=0, after=2, line=200)
    run = kicker.add_run(spec.get("kicker", spec.get("doc_type", "")).upper())
    _set_run_font(run, SANS, 9, bold=True, color=NAVY)

    title = doc.add_paragraph()
    _spacing(title, before=0, after=4, line=240)
    run = title.add_run(spec.get("title", ""))
    _set_run_font(run, SANS, 22, bold=True, color=NAVY)

    subtitle = spec.get("subtitle")
    if subtitle:
        sp = doc.add_paragraph()
        _spacing(sp, before=0, after=8, line=230)
        run = sp.add_run(subtitle)
        _set_run_font(run, BODY_FONT, 12, italic=True, color=STEEL)

    rule = doc.add_paragraph()
    _spacing(rule, before=0, after=10, line=80)
    _horizontal_line(rule, color="1B365D", sz="16")

    meta_rows = [
        ("Document ID", spec.get("doc_id", "")),
        ("Version", str(spec.get("version", "1.0"))),
        ("Status", spec.get("status", "Draft")),
        ("Date", spec.get("date", "")),
        ("Author", spec.get("author", "Aman Kumar")),
        ("Role", spec.get("role", "Software Engineer II")),
        ("Team / engagement", spec.get("team", "")),
        ("Audience", spec.get("audience", "")),
        ("Classification", spec.get("classification", "INTERNAL")),
    ]
    if spec.get("owners"):
        meta_rows.append(("Owners", spec["owners"]))
    if spec.get("related"):
        meta_rows.append(("Related", spec["related"]))

    table = doc.add_table(rows=len(meta_rows), cols=2)
    table.autofit = True
    table.allow_autofit = True
    _clear_table_borders(table)
    for i, (k, v) in enumerate(meta_rows):
        c0, c1 = table.rows[i].cells
        _set_cell_margins(c0, 50, 50, 70, 70)
        _set_cell_margins(c1, 50, 50, 70, 70)
        _shade_cell(c0, "EEF2F6" if i % 2 == 0 else "F7F9FB")
        _shade_cell(c1, "EEF2F6" if i % 2 == 0 else "F7F9FB")
        _set_cell_borders(c0, "D5DCE4", "4")
        _set_cell_borders(c1, "D5DCE4", "4")
        _paragraph_text(c0, k, font=SANS, size=9, bold=True, color=NAVY)
        _paragraph_text(c1, str(v), font=BODY_FONT, size=10, color=BODY)
        _set_narrow_cell_width(c0, 2200)

    spacer = doc.add_paragraph()
    _spacing(spacer, before=6, after=4, line=120)

    if spec.get("revision_history"):
        h = doc.add_paragraph()
        _spacing(h, before=8, after=6, line=240)
        run = h.add_run("Revision history")
        _set_run_font(run, SANS, 11, bold=True, color=NAVY)
        _keep_with_next(h)
        _add_table(
            doc,
            ["Ver", "Date", "Author", "Notes"],
            spec["revision_history"],
            col_widths=(900, 1600, 2000, 4500),
        )

    if spec.get("summary"):
        h = doc.add_paragraph()
        _spacing(h, before=12, after=4, line=240)
        run = h.add_run("What this is")
        _set_run_font(run, SANS, 11, bold=True, color=NAVY)
        _add_para(doc, spec["summary"])


def _add_para(doc, text, first_line=False):
    p = doc.add_paragraph()
    _spacing(p, before=0, after=12, line=427)
    p.paragraph_format.first_line_indent = Inches(0.2)
    run = p.add_run(text)
    _set_run_font(run, BODY_FONT, 12, color=BODY)
    return p


def _page_break_before(paragraph: Paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    pb = pPr.find(qn("w:pageBreakBefore"))
    if pb is None:
        pb = OxmlElement("w:pageBreakBefore")
        pPr.append(pb)


def _add_heading(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    if level == 1 and str(text).startswith("Appendix"):
        _page_break_before(p)
    return p


def _add_bullets(doc, items, ordered=False):
    for i, item in enumerate(items, 1):
        p = doc.add_paragraph()
        p.style = doc.styles["List Number" if ordered else "List Bullet"]
        _spacing(p, before=1, after=3, line=260)
        # style may inject a run; clear and rewrite
        if p.runs:
            p.clear()
        run = p.add_run(item)
        _set_run_font(run, BODY_FONT, 12, color=BODY)


def _add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True

    for j, h in enumerate(headers):
        cell = table.rows[0].cells[j]
        _shade_cell(cell, HEADER_BG)
        _set_cell_borders(cell, "1B365D", "4")
        _set_cell_margins(cell, 50, 50, 70, 70)
        _paragraph_text(cell, str(h), font=SANS, size=9, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
        if col_widths and j < len(col_widths):
            _set_narrow_cell_width(cell, col_widths[j])

    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = table.rows[i + 1].cells[j]
            bg = "FFFFFF" if i % 2 == 0 else ROW_ALT
            _shade_cell(cell, bg)
            _set_cell_borders(cell, "C5CDD6", "4")
            _set_cell_margins(cell, 50, 50, 70, 70)
            _paragraph_text(cell, str(val), font=BODY_FONT, size=9.5, color=BODY)
            if col_widths and j < len(col_widths):
                _set_narrow_cell_width(cell, col_widths[j])

    cap_space = doc.add_paragraph()
    _spacing(cap_space, before=2, after=8, line=80)
    return table


def _add_callout(doc, label, text, kind="decision"):
    bg = {"decision": DECISION_BG, "note": CALLOUT_BG, "warn": WARN_BG}.get(kind, DECISION_BG)
    table = doc.add_table(rows=1, cols=1)
    cell = table.rows[0].cells[0]
    _shade_cell(cell, bg)
    _set_cell_borders(cell, "1B365D" if kind != "warn" else "A15C46", "10")
    _set_cell_margins(cell, 80, 90, 120, 120)
    cell.text = ""
    p0 = cell.paragraphs[0]
    _spacing(p0, before=0, after=4, line=220)
    run = p0.add_run(label.upper())
    _set_run_font(run, SANS, 8, bold=True, color=NAVY if kind != "warn" else RGBColor(0x8A, 0x3B, 0x28))
    p1 = cell.add_paragraph()
    _spacing(p1, before=0, after=0, line=250)
    run = p1.add_run(text)
    _set_run_font(run, BODY_FONT, 10.5, color=BODY)
    sp = doc.add_paragraph()
    _spacing(sp, before=4, after=8, line=80)


def _add_code(doc, text, caption=None):
    if caption:
        p = doc.add_paragraph()
        _spacing(p, before=4, after=2, line=200)
        run = p.add_run(caption)
        _set_run_font(run, SANS, 8.5, italic=True, color=MUTED)
    table = doc.add_table(rows=1, cols=1)
    cell = table.rows[0].cells[0]
    _shade_cell(cell, CODE_BG)
    _set_cell_borders(cell, "C5CDD6", "6")
    _set_cell_margins(cell, 90, 90, 120, 120)
    cell.text = ""
    p = cell.paragraphs[0]
    _spacing(p, before=0, after=0, line=220)
    # preserve line breaks
    lines = text.split("\n")
    for idx, line in enumerate(lines):
        if idx == 0:
            run = p.add_run(line)
            _set_run_font(run, MONO, 8.5, color=BODY)
        else:
            p2 = cell.add_paragraph()
            _spacing(p2, before=0, after=0, line=220)
            run = p2.add_run(line if line else " ")
            _set_run_font(run, MONO, 8.5, color=BODY)
    sp = doc.add_paragraph()
    _spacing(sp, before=2, after=8, line=80)


def _render_block(doc, block):
    kind = block.get("type")
    if kind == "h1":
        _add_heading(doc, block["text"], 1)
    elif kind == "h2":
        _add_heading(doc, block["text"], 2)
    elif kind == "h3":
        _add_heading(doc, block["text"], 3)
    elif kind == "p":
        _add_para(doc, block["text"])
    elif kind == "bullets":
        _add_bullets(doc, block["items"], ordered=False)
    elif kind == "steps":
        _add_bullets(doc, block["items"], ordered=True)
    elif kind == "table":
        if block.get("caption"):
            p = doc.add_paragraph()
            _spacing(p, before=4, after=3, line=200)
            run = p.add_run(block["caption"])
            _set_run_font(run, SANS, 8.5, italic=True, color=MUTED)
        _add_table(doc, block["headers"], block["rows"], block.get("col_widths"))
    elif kind == "callout":
        _add_callout(doc, block.get("label", "Note"), block["text"], block.get("kind", "decision"))
    elif kind == "code":
        _add_code(doc, block["text"], block.get("caption"))
    elif kind == "quote":
        p = doc.add_paragraph()
        _spacing(p, before=4, after=8, line=260)
        p.paragraph_format.left_indent = Inches(0.3)
        run = p.add_run(block["text"])
        _set_run_font(run, BODY_FONT, 11, italic=True, color=STEEL)
        if block.get("attrib"):
            p2 = doc.add_paragraph()
            _spacing(p2, before=0, after=8, line=220)
            p2.paragraph_format.left_indent = Inches(0.3)
            run = p2.add_run("- " + block["attrib"])
            _set_run_font(run, SANS, 9, color=MUTED)
    else:
        raise ValueError(f"Unknown block type: {kind}")
